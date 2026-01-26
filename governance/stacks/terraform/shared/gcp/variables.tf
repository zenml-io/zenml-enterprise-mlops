# Variables for Shared GCP Resources

# =============================================================================
# Required Variables
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

# =============================================================================
# Bucket Configuration
# =============================================================================

variable "region" {
  description = "GCP region for the bucket"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name of the model exchange bucket"
  type        = string
  default     = "zenml-core-model-exchange"
}

variable "export_retention_days" {
  description = "Days to retain model exports before automatic deletion"
  type        = number
  default     = 90
}

# =============================================================================
# Service Account Configuration
# =============================================================================

variable "dev_staging_service_account" {
  description = "Service account email for dev-staging workspace (leave empty to skip)"
  type        = string
  default     = ""
}

variable "production_service_account" {
  description = "Service account email for production workspace (leave empty to skip)"
  type        = string
  default     = ""
}
