# Variables for GCP Production Stack
# Configure these in terraform.tfvars or via environment variables

# =============================================================================
# ZenML Connection (Required)
# =============================================================================

variable "zenml_server_url" {
  description = "ZenML server URL (e.g., https://your-workspace.zenml.io)"
  type        = string
  sensitive   = false
}

variable "zenml_api_key" {
  description = "ZenML API key for authentication"
  type        = string
  sensitive   = true
}

# =============================================================================
# GCP Configuration (Required)
# =============================================================================

variable "project_id" {
  description = "GCP Project ID for production environment"
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
  default     = "gcp-stack"
}

# =============================================================================
# Cost Tracking / Resource Management
# =============================================================================

variable "team_name" {
  description = "Team name for cost attribution"
  type        = string
  default     = "platform-team"  # Production owned by platform team
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
# Shared Artifact Store (Recommended)
# =============================================================================

variable "shared_artifact_bucket" {
  description = <<-EOT
    Name of the shared artifact store bucket (from shared/gcp terraform).
    When set, uses the shared bucket instead of creating a new one.
    This enables seamless cross-workspace promotion with ZenML's fileio.

    Benefits:
    - ZenML's fileio works across workspaces (same artifact store bounds)
    - Cross-workspace promotion uses standard APIs (no GCS client bypass)
    - Single bucket to manage and backup

    Leave empty to create a dedicated bucket for this stack.
  EOT
  type        = string
  default     = ""
}
