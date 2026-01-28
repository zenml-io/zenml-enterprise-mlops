# GCP Staging Stack (Vertex AI Orchestrator)
# Using ZenML Terraform Provider directly for full label control
#
# Workspace: enterprise-dev-staging
# Stack Name: staging-stack
#
# Features:
# - Vertex AI orchestrator (production-like environment)
# - GCS for artifact storage
# - Artifact Registry for container images
# - Full label control on all ZenML resources

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
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
}

provider "google" {
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
  # Common labels for ZenML resources
  zenml_labels = {
    environment = "staging"
    workspace   = "enterprise-dev-staging"
    team        = var.team_name
    cost_center = var.cost_center
    managed_by  = "terraform"
  }

  # Common labels for GCP resources
  gcp_labels = merge(var.labels, {
    environment = "staging"
    workspace   = "enterprise-dev-staging"
    managed_by  = "terraform"
    team        = var.team_name
    cost_center = var.cost_center
  })
}

# =============================================================================
# Random suffix for unique resource names
# =============================================================================

resource "random_id" "suffix" {
  byte_length = 4  # 8 hex chars to keep service account ID under 30 chars
}

# =============================================================================
# GCP Infrastructure
# =============================================================================

# =============================================================================
# Artifact Store: Use shared bucket if provided, otherwise create dedicated one
# =============================================================================

# Option 1: Use shared artifact store (recommended for cross-workspace promotion)
data "google_storage_bucket" "shared_artifact_store" {
  count = var.shared_artifact_bucket != "" ? 1 : 0
  name  = var.shared_artifact_bucket
}

# Option 2: Create dedicated bucket (legacy, for isolated stacks)
resource "google_storage_bucket" "artifact_store" {
  count    = var.shared_artifact_bucket == "" ? 1 : 0
  name     = "${var.project_id}-${var.stack_name}-${random_id.suffix.hex}"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = true

  labels = local.gcp_labels
}

locals {
  # Use shared bucket if provided, otherwise use dedicated bucket
  artifact_bucket_name = var.shared_artifact_bucket != "" ? var.shared_artifact_bucket : google_storage_bucket.artifact_store[0].name
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "container_registry" {
  project       = var.project_id
  location      = var.region
  repository_id = "${var.stack_name}-${random_id.suffix.hex}"
  format        = "DOCKER"

  labels = local.gcp_labels
}

# Service Account for ZenML
resource "google_service_account" "zenml_sa" {
  project      = var.project_id
  account_id   = "zenml-${var.stack_name}-${random_id.suffix.hex}"
  display_name = "ZenML ${var.stack_name} Service Account"
}

# Service Account Key
resource "google_service_account_key" "zenml_sa_key" {
  service_account_id = google_service_account.zenml_sa.name
}

# IAM: Storage Admin on the artifact bucket (shared or dedicated)
resource "google_storage_bucket_iam_member" "zenml_sa_storage" {
  bucket = local.artifact_bucket_name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.zenml_sa.email}"
}

# IAM: Artifact Registry Writer
resource "google_artifact_registry_repository_iam_member" "zenml_sa_ar" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.container_registry.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.zenml_sa.email}"
}

# IAM: Vertex AI User (for submitting pipeline jobs)
resource "google_project_iam_member" "zenml_sa_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.zenml_sa.email}"
}

# IAM: Vertex AI Service Agent (for running pipelines)
resource "google_project_iam_member" "zenml_sa_vertex_agent" {
  project = var.project_id
  role    = "roles/aiplatform.serviceAgent"
  member  = "serviceAccount:${google_service_account.zenml_sa.email}"
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

# Artifact Store (uses shared or dedicated bucket)
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

# Container Registry
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

# Vertex AI Orchestrator
resource "zenml_stack_component" "orchestrator" {
  name   = "${var.stack_name}-vertex"
  type   = "orchestrator"
  flavor = "vertex"

  configuration = {
    location                 = var.region
    project                  = var.project_id
    workload_service_account = google_service_account.zenml_sa.email
    synchronous              = "true"
  }

  connector_id = zenml_service_connector.gcp.id
  labels       = local.zenml_labels
}

# =============================================================================
# ZenML Stack
# =============================================================================

resource "zenml_stack" "staging_stack" {
  name = var.stack_name

  components = {
    artifact_store     = zenml_stack_component.artifact_store.id
    container_registry = zenml_stack_component.container_registry.id
    orchestrator       = zenml_stack_component.orchestrator.id
  }

  labels = local.zenml_labels
}

# =============================================================================
# Outputs
# =============================================================================

output "zenml_stack_id" {
  description = "The ID of the registered ZenML stack"
  value       = zenml_stack.staging_stack.id
}

output "zenml_stack_name" {
  description = "The name of the registered ZenML stack"
  value       = zenml_stack.staging_stack.name
}

output "gcs_bucket" {
  description = "GCS bucket for artifacts"
  value       = local.artifact_bucket_name
}

output "using_shared_bucket" {
  description = "Whether using shared artifact store"
  value       = var.shared_artifact_bucket != ""
}

output "service_account" {
  description = "Service account for Vertex AI workloads"
  value       = google_service_account.zenml_sa.email
}

output "post_deployment_instructions" {
  description = "Steps to activate the staging stack"
  value       = <<-EOT
    Staging Stack deployed successfully!

    Stack Details:
    - Name: ${var.stack_name}
    - Orchestrator: Vertex AI (${var.region})
    - Workspace: enterprise-dev-staging

    Labels applied to all ZenML resources:
    - environment: staging
    - team: ${var.team_name}
    - cost_center: ${var.cost_center}

    Next steps:
    1. Source workspace: source scripts/use-workspace.sh dev-staging
    2. Set the project: zenml project set cancer-detection
    3. Activate the stack: zenml stack set ${var.stack_name}
    4. Run training: python run.py --pipeline training --environment staging
  EOT
}
