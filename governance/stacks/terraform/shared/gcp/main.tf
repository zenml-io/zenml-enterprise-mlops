# Shared GCP Resources for Cross-Workspace Model Promotion
#
# This creates a shared GCS bucket used for model export/import between
# the enterprise-dev-staging and enterprise-production workspaces.
#
# Models are exported from dev-staging, stored here, then imported to production.

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # RECOMMENDED: Use remote backend for shared state
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "zenml/shared/gcp"
  # }
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

  # Enable versioning for audit trail
  versioning {
    enabled = true
  }

  # Lifecycle rules for cleanup
  lifecycle_rule {
    condition {
      age = var.export_retention_days
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
# IAM: Grant access to workspace service accounts
# =============================================================================

# Dev-staging workspace service account (export models)
resource "google_storage_bucket_iam_member" "dev_staging_access" {
  count = var.dev_staging_service_account != "" ? 1 : 0

  bucket = google_storage_bucket.model_exchange.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.dev_staging_service_account}"
}

# Production workspace service account (import models)
resource "google_storage_bucket_iam_member" "production_access" {
  count = var.production_service_account != "" ? 1 : 0

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
  description = "GCS URL of the model exchange bucket"
  value       = "gs://${google_storage_bucket.model_exchange.name}"
}

output "export_path_template" {
  description = "Template for model export paths"
  value       = "gs://${google_storage_bucket.model_exchange.name}/exports/{model_name}/{timestamp}/"
}

output "post_deployment_instructions" {
  description = "Instructions for using the model exchange bucket"
  value       = <<-EOT
    ✅ Model Exchange Bucket created successfully!

    Bucket: gs://${google_storage_bucket.model_exchange.name}

    Usage:
    1. Export model from dev-staging workspace:
       python scripts/promote_cross_workspace.py \
         --model breast_cancer_classifier \
         --source-workspace enterprise-dev-staging \
         --export-only

    2. Import model to production workspace:
       python scripts/promote_cross_workspace.py \
         --model breast_cancer_classifier \
         --dest-workspace enterprise-production \
         --import-from gs://${google_storage_bucket.model_exchange.name}/exports/...

    Export Structure:
    gs://${google_storage_bucket.model_exchange.name}/
    └── exports/
        └── breast_cancer_classifier/
            └── 2026-01-26T12:00:00/
                ├── model.joblib
                ├── scaler.joblib
                └── manifest.json (metadata, metrics, lineage)

    Note: Exports are automatically deleted after ${var.export_retention_days} days.
  EOT
}
