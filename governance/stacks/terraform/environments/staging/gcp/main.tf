# GCP Staging Stack with Vertex AI
# This provisions GCP infrastructure AND registers the stack with ZenML
#
# Features demonstrated:
# - Vertex AI Pipelines as orchestrator
# - GCS for artifact storage (can use existing bucket)
# - Artifact Registry for container images
# - Workload Identity Federation for authentication
# - BigQuery integration for data access

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # RECOMMENDED: Use remote backend for state
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "zenml/staging/gcp"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# OPTION 1: Use Official ZenML Module (Recommended for new setups)
# =============================================================================

module "zenml_stack" {
  source  = "zenml-io/zenml-stack/gcp"
  version = "~> 0.1"

  # Stack configuration
  zenml_stack_name            = var.stack_name
  zenml_stack_deployment_name = var.deployment_name
  orchestrator                = var.orchestrator  # "vertex" for Vertex AI

  # GCP-specific settings
  project_id = var.project_id
  region     = var.region

  # Labels for resource management and cost tracking
  labels = merge(var.labels, {
    environment = "staging"
    managed_by  = "terraform"
    team        = var.team_name
    cost_center = var.cost_center
  })
}

# =============================================================================
# OPTION 2: Use Existing GCS Bucket (For organizations with existing infra)
# =============================================================================

# If you have existing GCS buckets, you can register them with ZenML directly
# instead of creating new ones. Uncomment and configure:

# resource "zenml_stack_component" "existing_artifact_store" {
#   name   = "existing-gcs-store"
#   type   = "artifact_store"
#   flavor = "gcp"
#
#   configuration = {
#     path = "gs://${var.existing_gcs_bucket}/zenml-artifacts"
#   }
# }

# =============================================================================
# BigQuery Integration (For data access)
# =============================================================================

# Grant ZenML service account access to BigQuery datasets
resource "google_bigquery_dataset_iam_member" "zenml_reader" {
  count = var.bigquery_dataset != "" ? 1 : 0

  dataset_id = var.bigquery_dataset
  project    = var.project_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${module.zenml_stack.service_account_email}"
}

# =============================================================================
# Workload Identity Federation (For GitHub Actions CI/CD)
# =============================================================================

# This allows GitHub Actions to authenticate to GCP without service account keys
resource "google_iam_workload_identity_pool" "github_pool" {
  count = var.enable_workload_identity ? 1 : 0

  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions CI/CD"
  project                   = var.project_id
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  count = var.enable_workload_identity ? 1 : 0

  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  project                            = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  # Restrict to your GitHub organization/repository
  attribute_condition = "assertion.repository_owner == '${var.github_org}'"
}

# Allow GitHub Actions to impersonate the ZenML service account
resource "google_service_account_iam_member" "github_impersonation" {
  count = var.enable_workload_identity ? 1 : 0

  service_account_id = module.zenml_stack.service_account_id
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool[0].name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

# =============================================================================
# Outputs
# =============================================================================

output "zenml_stack_id" {
  description = "The ID of the registered ZenML stack"
  value       = module.zenml_stack.zenml_stack_id
}

output "zenml_stack_name" {
  description = "The name of the registered ZenML stack"
  value       = module.zenml_stack.zenml_stack_name
}

output "gcs_artifact_store_path" {
  description = "GCS path for artifact storage"
  value       = module.zenml_stack.gcs_artifact_store_path
}

output "artifact_registry_uri" {
  description = "Artifact Registry URI for container images"
  value       = module.zenml_stack.artifact_registry_uri
}

output "service_account_email" {
  description = "Service account used by ZenML pipelines"
  value       = module.zenml_stack.service_account_email
}

output "workload_identity_provider" {
  description = "Workload Identity provider for GitHub Actions"
  value       = var.enable_workload_identity ? google_iam_workload_identity_pool_provider.github_provider[0].name : null
}

output "github_actions_setup" {
  description = "Configuration for GitHub Actions"
  value = var.enable_workload_identity ? <<-EOT
    # Add to your GitHub Actions workflow:

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v2
      with:
        workload_identity_provider: ${google_iam_workload_identity_pool_provider.github_provider[0].name}
        service_account: ${module.zenml_stack.service_account_email}
  EOT : "Workload Identity not enabled"
}

output "post_deployment_instructions" {
  description = "Steps to activate the stack"
  value       = <<-EOT
    ✅ GCP Stack deployed successfully!

    Stack Details:
    - Name: ${var.stack_name}
    - Orchestrator: ${var.orchestrator}
    - Region: ${var.region}
    - Artifact Store: ${module.zenml_stack.gcs_artifact_store_path}

    Next steps:
    1. Install GCP integration:
       zenml integration install gcp

    2. Activate the stack:
       zenml stack set ${var.stack_name}

    3. Verify the stack:
       zenml stack describe ${var.stack_name}

    4. Run a pipeline:
       python run.py --pipeline training --environment staging

    For GitHub Actions CI/CD:
    - Configure secrets: ZENML_STORE_URL, ZENML_STORE_API_KEY
    - Use Workload Identity for GCP auth (see github_actions_setup output)
  EOT
}
