# Variables for GCP Development Stack
# Configure these in terraform.tfvars or via environment variables

# =============================================================================
# Required Variables
# =============================================================================

variable "project_id" {
  description = "GCP Project ID (e.g., zenml-core)"
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
  default     = "dev-stack"
}

variable "deployment_name" {
  description = "Name for the stack deployment (used in resource naming)"
  type        = string
  default     = "zenml-development"
}

# =============================================================================
# Cost Tracking / Resource Management
# =============================================================================

variable "team_name" {
  description = "Team name for cost attribution"
  type        = string
  default     = "data-science"
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
