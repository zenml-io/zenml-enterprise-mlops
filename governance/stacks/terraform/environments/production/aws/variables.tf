# Variables for AWS Production Stack

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "stack_name" {
  description = "Name of the ZenML stack"
  type        = string
  default     = "aws-production"
}

variable "deployment_name" {
  description = "Name for the stack deployment (used in resource naming)"
  type        = string
  default     = "zenml-production"
}

variable "orchestrator" {
  description = "Type of orchestrator to deploy (recommend sagemaker for production)"
  type        = string
  default     = "sagemaker"

  validation {
    condition     = contains(["sagemaker", "skypilot"], var.orchestrator)
    error_message = "Production orchestrator must be one of: sagemaker, skypilot (local not recommended for production)"
  }
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
