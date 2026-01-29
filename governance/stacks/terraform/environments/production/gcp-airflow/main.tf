# GCP Stack with Cloud Composer (Airflow) Orchestrator
# This is a SEPARATE stack from the Vertex AI stack
#
# Workspace: Configurable via variables (default: enterprise-dev-staging)
# Stack Name: gcp-airflow-stack
#
# Use this when you want Airflow orchestration capabilities.
# Can coexist with other stacks (Vertex AI, Kubernetes, etc.)

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    zenml = {
      source  = "zenml-io/zenml"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # REQUIRED for production: Use remote backend for state
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "zenml/production/gcp-airflow"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

provider "zenml" {
  server_url = var.zenml_server_url
  api_key    = var.zenml_api_key
}

# =============================================================================
# Local Variables
# =============================================================================

locals {
  zenml_labels = {
    environment  = var.environment
    workspace    = var.workspace_name
    team         = var.team_name
    cost_center  = var.cost_center
    managed_by   = "terraform"
    orchestrator = "airflow"
  }

  gcp_labels = merge(var.labels, {
    environment  = var.environment
    workspace    = var.workspace_name
    managed_by   = "terraform"
    orchestrator = "airflow"
  })
}

# =============================================================================
# Random suffix for unique resource names
# =============================================================================

resource "random_id" "suffix" {
  byte_length = 4
}

# =============================================================================
# Artifact Store (use shared or create dedicated)
# =============================================================================

data "google_storage_bucket" "shared_artifact_store" {
  count = var.shared_artifact_bucket != "" ? 1 : 0
  name  = var.shared_artifact_bucket
}

resource "google_storage_bucket" "artifact_store" {
  count    = var.shared_artifact_bucket == "" ? 1 : 0
  name     = "${var.project_id}-${var.stack_name}-${random_id.suffix.hex}"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = false

  labels = local.gcp_labels
}

locals {
  artifact_bucket_name = var.shared_artifact_bucket != "" ? var.shared_artifact_bucket : google_storage_bucket.artifact_store[0].name
}

# =============================================================================
# Artifact Registry
# =============================================================================

resource "google_artifact_registry_repository" "container_registry" {
  project       = var.project_id
  location      = var.region
  repository_id = "${var.stack_name}-${random_id.suffix.hex}"
  format        = "DOCKER"

  labels = local.gcp_labels
}

# =============================================================================
# Service Account
# =============================================================================

resource "google_service_account" "zenml_sa" {
  project      = var.project_id
  account_id   = "zenml-${var.stack_name}-${random_id.suffix.hex}"
  display_name = "ZenML ${var.stack_name} (Airflow) Service Account"
}

resource "google_service_account_key" "zenml_sa_key" {
  service_account_id = google_service_account.zenml_sa.name
}

# =============================================================================
# IAM Permissions
# =============================================================================

resource "google_storage_bucket_iam_member" "zenml_sa_storage" {
  bucket = local.artifact_bucket_name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.zenml_sa.email}"
}

resource "google_artifact_registry_repository_iam_member" "zenml_sa_ar" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.container_registry.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.zenml_sa.email}"
}

# Composer Worker role
resource "google_project_iam_member" "zenml_sa_composer_worker" {
  project = var.project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.zenml_sa.email}"
}

# =============================================================================
# Cloud Composer Environment
# =============================================================================

resource "google_composer_environment" "zenml_airflow" {
  count    = var.create_composer_environment ? 1 : 0
  provider = google-beta

  name    = "zenml-${var.stack_name}-${random_id.suffix.hex}"
  project = var.project_id
  region  = var.region

  config {
    software_config {
      image_version = var.composer_image_version

      pypi_packages = {
        "pydantic"                                 = "~=2.11.1"
        "apache-airflow-providers-docker"          = ">=4.4.0"
        "apache-airflow-providers-cncf-kubernetes" = ">=10.0.0"
      }

      env_variables = {
        ZENML_LOGGING_VERBOSITY = "INFO"
      }
    }

    workloads_config {
      scheduler {
        cpu        = var.composer_scheduler_cpu
        memory_gb  = var.composer_scheduler_memory_gb
        storage_gb = var.composer_scheduler_storage_gb
        count      = var.composer_scheduler_count
      }
      web_server {
        cpu        = var.composer_webserver_cpu
        memory_gb  = var.composer_webserver_memory_gb
        storage_gb = var.composer_webserver_storage_gb
      }
      worker {
        cpu        = var.composer_worker_cpu
        memory_gb  = var.composer_worker_memory_gb
        storage_gb = var.composer_worker_storage_gb
        min_count  = var.composer_worker_min_count
        max_count  = var.composer_worker_max_count
      }
    }

    environment_size = var.composer_environment_size

    node_config {
      service_account = google_service_account.zenml_sa.email
    }
  }

  labels = local.gcp_labels
}

# Reference existing Composer environment
data "google_composer_environment" "existing" {
  count   = var.create_composer_environment ? 0 : 1
  name    = var.existing_composer_name
  project = var.project_id
  region  = var.region
}

locals {
  composer_dags_gcs_prefix = var.create_composer_environment ? google_composer_environment.zenml_airflow[0].config[0].dag_gcs_prefix : data.google_composer_environment.existing[0].config[0].dag_gcs_prefix

  composer_airflow_uri = var.create_composer_environment ? google_composer_environment.zenml_airflow[0].config[0].airflow_uri : data.google_composer_environment.existing[0].config[0].airflow_uri
}

# =============================================================================
# ZenML Service Connector
# =============================================================================

resource "zenml_service_connector" "gcp" {
  name        = "${var.stack_name}-gcp-connector"
  type        = "gcp"
  auth_method = "service-account"

  configuration = {
    project_id           = var.project_id
    region               = var.region
    service_account_json = base64decode(google_service_account_key.zenml_sa_key.private_key)
  }

  labels = local.zenml_labels
}

# =============================================================================
# ZenML Stack Components
# =============================================================================

resource "zenml_stack_component" "artifact_store" {
  name   = "${var.stack_name}-gcs"
  type   = "artifact_store"
  flavor = "gcp"

  configuration = {
    path = "gs://${local.artifact_bucket_name}"
  }

  connector_id = zenml_service_connector.gcp.id
  labels       = local.zenml_labels
}

resource "zenml_stack_component" "container_registry" {
  name   = "${var.stack_name}-gar"
  type   = "container_registry"
  flavor = "gcp"

  configuration = {
    uri = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.container_registry.repository_id}"
  }

  connector_id = zenml_service_connector.gcp.id
  labels       = local.zenml_labels
}

resource "zenml_stack_component" "orchestrator_airflow" {
  name   = "${var.stack_name}-airflow"
  type   = "orchestrator"
  flavor = "airflow"

  configuration = {
    local          = "false"
    dag_output_dir = local.composer_dags_gcs_prefix
    operator       = var.airflow_operator
  }

  labels = local.zenml_labels
}

# =============================================================================
# ZenML Stack
# =============================================================================

resource "zenml_stack" "airflow_stack" {
  name = var.stack_name

  components = {
    artifact_store     = zenml_stack_component.artifact_store.id
    container_registry = zenml_stack_component.container_registry.id
    orchestrator       = zenml_stack_component.orchestrator_airflow.id
  }

  labels = local.zenml_labels
}

# =============================================================================
# Outputs
# =============================================================================

output "zenml_stack_id" {
  value = zenml_stack.airflow_stack.id
}

output "zenml_stack_name" {
  value = zenml_stack.airflow_stack.name
}

output "gcs_bucket" {
  value = local.artifact_bucket_name
}

output "service_account" {
  value = google_service_account.zenml_sa.email
}

output "composer_airflow_uri" {
  value = local.composer_airflow_uri
}

output "composer_dags_gcs_prefix" {
  value = local.composer_dags_gcs_prefix
}

output "post_deployment_instructions" {
  value = <<-EOT
    Cloud Composer (Airflow) Production Stack deployed!

    Stack Details:
    - Name: ${var.stack_name}
    - Orchestrator: Cloud Composer (Airflow)
    - Region: ${var.region}

    Airflow UI: ${local.composer_airflow_uri}
    DAGs Path: ${local.composer_dags_gcs_prefix}

    Next steps:
    1. Install integrations:
       zenml integration install gcp airflow

    2. Source workspace:
       source scripts/use-workspace.sh production

    3. Activate the stack:
       zenml stack set ${var.stack_name}

    Note: Cloud Composer creation takes ~20-30 minutes.
  EOT
}
