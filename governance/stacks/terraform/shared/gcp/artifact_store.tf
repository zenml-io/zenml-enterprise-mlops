# Shared Artifact Store Bucket
# =============================================================================
# This bucket is shared between dev-staging and production workspaces.
#
# Benefits:
# - ZenML's fileio works seamlessly across workspaces (same artifact store)
# - Cross-workspace promotion is just copying within the same bucket
# - Both service accounts have access to the shared storage
# - Single bucket to manage, backup, and configure lifecycle policies
#
# Directory Structure:
# gs://shared-bucket/
# ├── artifacts/           ← Pipeline artifacts (automatic)
# ├── model-exchange/      ← Cross-workspace model exports
# └── (zenml managed)      ← ZenML internal metadata
#
# Deployment Order:
# 1. Deploy this shared bucket FIRST
# 2. Deploy staging stack (references this bucket)
# 3. Deploy production stack (references this bucket)
#
# Usage:
#   cd governance/stacks/terraform/shared/gcp
#   terraform init
#   terraform apply

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
# Variables
# =============================================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "zenml-core"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name for the shared artifact store bucket"
  type        = string
  default     = "zenml-enterprise-shared-artifacts"
}

variable "retention_days" {
  description = "Days to retain model exports before cleanup"
  type        = number
  default     = 90
}

variable "staging_service_account" {
  description = "Service account email for staging stack (from staging terraform output)"
  type        = string
  default     = ""
}

variable "production_service_account" {
  description = "Service account email for production stack (from production terraform output)"
  type        = string
  default     = ""
}

# =============================================================================
# Shared Artifact Store Bucket
# =============================================================================

resource "google_storage_bucket" "shared_artifact_store" {
  name     = var.bucket_name  # Use exact name from .env (MODEL_EXCHANGE_BUCKET)
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = false # Protect artifacts

  # Lifecycle rule for model-exchange exports only
  lifecycle_rule {
    condition {
      age            = var.retention_days
      matches_prefix = ["model-exchange/"]
    }
    action {
      type = "Delete"
    }
  }

  # Versioning for artifact protection
  versioning {
    enabled = true
  }

  labels = {
    purpose     = "shared-artifact-store"
    managed_by  = "terraform"
    environment = "shared"
  }
}

# =============================================================================
# IAM: Grant service accounts access to the shared bucket
# =============================================================================

# Staging service account (from enterprise-dev-staging workspace)
resource "google_storage_bucket_iam_member" "staging_access" {
  count  = var.staging_service_account != "" ? 1 : 0
  bucket = google_storage_bucket.shared_artifact_store.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.staging_service_account}"
}

# Production service account (from enterprise-production workspace)
resource "google_storage_bucket_iam_member" "production_access" {
  count  = var.production_service_account != "" ? 1 : 0
  bucket = google_storage_bucket.shared_artifact_store.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.production_service_account}"
}

# =============================================================================
# Outputs
# =============================================================================

output "bucket_name" {
  description = "Name of the shared artifact store bucket"
  value       = google_storage_bucket.shared_artifact_store.name
}

output "bucket_url" {
  description = "GCS URL for the shared artifact store"
  value       = "gs://${google_storage_bucket.shared_artifact_store.name}"
}

output "bucket_id" {
  description = "Bucket ID for use in stack terraform"
  value       = google_storage_bucket.shared_artifact_store.id
}

output "usage_instructions" {
  description = "How to use the shared artifact store"
  value       = <<-EOT
    Shared Artifact Store: ${google_storage_bucket.shared_artifact_store.name}

    This bucket is shared between dev-staging and production workspaces.

    Next steps:
    1. Note the bucket name: ${google_storage_bucket.shared_artifact_store.name}

    2. Deploy staging stack with shared bucket:
       cd ../environments/staging/gcp
       terraform apply -var="shared_artifact_bucket=${google_storage_bucket.shared_artifact_store.name}"

    3. Deploy production stack with shared bucket:
       cd ../environments/production/gcp
       terraform apply -var="shared_artifact_bucket=${google_storage_bucket.shared_artifact_store.name}"

    4. After stacks are deployed, grant access to service accounts:
       terraform apply \
         -var="staging_service_account=<staging-sa-email>" \
         -var="production_service_account=<production-sa-email>"

    Benefits:
    - ZenML's fileio works seamlessly (same artifact store bounds)
    - Cross-workspace promotion uses standard ZenML APIs
    - No need for separate model exchange bucket
  EOT
}
