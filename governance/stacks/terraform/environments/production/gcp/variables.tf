# Variables for GCP Production Stack

variable "project_id" {
  description = "GCP Project ID for production environment"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "stack_name" {
  description = "Name of the ZenML stack"
  type        = string
  default     = "gcp-stack" # Part of enterprise-production workspace
}

variable "deployment_name" {
  description = "Name for the stack deployment (used in resource naming)"
  type        = string
  default     = "zenml-production"
}

variable "orchestrator" {
  description = "Type of orchestrator to deploy (recommend vertex or airflow for production)"
  type        = string
  default     = "vertex"

  validation {
    condition     = contains(["vertex", "airflow", "skypilot"], var.orchestrator)
    error_message = "Production orchestrator must be one of: vertex, airflow, skypilot (local not recommended for production)"
  }
}

variable "labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
}
