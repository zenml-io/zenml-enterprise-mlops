# Shared Model Exchange Bucket
# Enables cross-workspace model promotion between dev-staging and production
#
# Usage:
#   1. First deploy the environment stacks (dev, staging, production)
#   2. Then deploy this shared bucket with the service account emails:
#
#   terraform init
#   terraform apply \
#     -var="staging_service_account=zenml-staging-stack-xxx@zenml-core.iam.gserviceaccount.com" \
#     -var="production_service_account=zenml-gcp-stack-xxx@zenml-core.iam.gserviceaccount.com"
#
# Note: No ZenML connection needed - just GCP resources.

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# Model Exchange Bucket
# =============================================================================

resource "google_storage_bucket" "model_exchange" {
  name     = var.bucket_name
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true

  # Clean up old exports after retention period
  lifecycle_rule {
    condition {
      age = var.retention_days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    purpose     = "cross-workspace-model-promotion"
    managed_by  = "terraform"
    environment = "shared"
  }
}

# =============================================================================
# IAM: Grant service accounts access to the model exchange bucket
# =============================================================================

# Staging service account (from enterprise-dev-staging workspace)
resource "google_storage_bucket_iam_member" "staging_access" {
  count  = var.staging_service_account != "" ? 1 : 0
  bucket = google_storage_bucket.model_exchange.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.staging_service_account}"
}

# Production service account (from enterprise-production workspace)
resource "google_storage_bucket_iam_member" "production_access" {
  count  = var.production_service_account != "" ? 1 : 0
  bucket = google_storage_bucket.model_exchange.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.production_service_account}"
}

# =============================================================================
# Outputs
# =============================================================================

output "bucket_name" {
  description = "Name of the model exchange bucket"
  value       = google_storage_bucket.model_exchange.name
}

output "bucket_url" {
  description = "GCS URL for model exchange"
  value       = "gs://${google_storage_bucket.model_exchange.name}"
}

output "usage_instructions" {
  description = "How to use the model exchange bucket"
  value       = <<-EOT
    Model Exchange Bucket: ${google_storage_bucket.model_exchange.name}

    This bucket enables cross-workspace model promotion:

    1. Export model from staging (enterprise-dev-staging):
       python scripts/promote_cross_workspace.py \
         --model breast_cancer_classifier \
         --source-workspace enterprise-dev-staging \
         --export-only

    2. Import model to production (enterprise-production):
       python scripts/promote_cross_workspace.py \
         --model breast_cancer_classifier \
         --dest-workspace enterprise-production \
         --import-from gs://${google_storage_bucket.model_exchange.name}/exports/...

    Service accounts with access:
    - Staging: ${var.staging_service_account != "" ? var.staging_service_account : "Not configured"}
    - Production: ${var.production_service_account != "" ? var.production_service_account : "Not configured"}
  EOT
}
