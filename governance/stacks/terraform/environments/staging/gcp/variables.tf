# Variables for GCP Staging Stack

variable "project_id" {
  description = "GCP Project ID for staging environment"
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
  default     = "gcp-staging"
}

variable "deployment_name" {
  description = "Name for the stack deployment (used in resource naming)"
  type        = string
  default     = "zenml-staging"
}

variable "orchestrator" {
  description = "Type of orchestrator to deploy"
  type        = string
  default     = "local"

  validation {
    condition     = contains(["vertex", "airflow", "skypilot", "local"], var.orchestrator)
    error_message = "Orchestrator must be one of: vertex, airflow, skypilot, local"
  }
}

variable "labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
}
