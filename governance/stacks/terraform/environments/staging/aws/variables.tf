# Variables for AWS Staging Stack

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "stack_name" {
  description = "Name of the ZenML stack"
  type        = string
  default     = "aws-staging"
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
    condition     = contains(["sagemaker", "skypilot", "local"], var.orchestrator)
    error_message = "Orchestrator must be one of: sagemaker, skypilot, local"
  }
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
