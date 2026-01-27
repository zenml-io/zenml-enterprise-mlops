# Variables for Shared Model Exchange Bucket
# Configure these after deploying the environment stacks

# =============================================================================
# GCP Configuration
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "zenml-core"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name of the model exchange bucket"
  type        = string
  default     = "zenml-core-model-exchange"
}

variable "retention_days" {
  description = "Days to retain exported models before cleanup"
  type        = number
  default     = 90
}

# =============================================================================
# Service Account Access
# Get these from the stack terraform outputs:
#   terraform -chdir=../environments/staging/gcp output service_account
#   terraform -chdir=../environments/production/gcp output service_account
# =============================================================================

variable "staging_service_account" {
  description = "Service account email from staging stack (for cross-workspace access)"
  type        = string
  default     = ""
}

variable "production_service_account" {
  description = "Service account email from production stack (for cross-workspace access)"
  type        = string
  default     = ""
}
