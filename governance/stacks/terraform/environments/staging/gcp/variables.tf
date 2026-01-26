# Variables for GCP Staging Stack
# Configure these in terraform.tfvars or via environment variables

# =============================================================================
# Required Variables
# =============================================================================

variable "project_id" {
  description = "GCP Project ID for staging environment"
  type        = string
}

# =============================================================================
# Stack Configuration
# =============================================================================

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "stack_name" {
  description = "Name of the ZenML stack"
  type        = string
  default     = "staging-stack"  # Part of enterprise-dev-staging workspace
}

variable "deployment_name" {
  description = "Name for the stack deployment (used in resource naming)"
  type        = string
  default     = "zenml-staging"
}

variable "orchestrator" {
  description = "Type of orchestrator to deploy (vertex = Vertex AI Pipelines)"
  type        = string
  default     = "vertex"

  validation {
    condition     = contains(["vertex", "airflow", "skypilot", "local"], var.orchestrator)
    error_message = "Orchestrator must be one of: vertex, airflow, skypilot, local"
  }
}

# =============================================================================
# Cost Tracking / Resource Management
# =============================================================================

variable "team_name" {
  description = "Team name for cost attribution"
  type        = string
  default     = "platform"
}

variable "cost_center" {
  description = "Cost center for billing attribution"
  type        = string
  default     = "ml-platform"
}

variable "labels" {
  description = "Additional labels to apply to GCP resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Existing Infrastructure (Optional)
# =============================================================================

variable "existing_gcs_bucket" {
  description = "Use existing GCS bucket instead of creating new one"
  type        = string
  default     = ""
}

variable "bigquery_dataset" {
  description = "BigQuery dataset to grant ZenML service account access to"
  type        = string
  default     = ""
}

# =============================================================================
# Workload Identity Federation (For GitHub Actions)
# =============================================================================

variable "enable_workload_identity" {
  description = "Enable Workload Identity Federation for GitHub Actions"
  type        = bool
  default     = false
}

variable "github_org" {
  description = "GitHub organization name (required if enable_workload_identity = true)"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name (required if enable_workload_identity = true)"
  type        = string
  default     = ""
}
