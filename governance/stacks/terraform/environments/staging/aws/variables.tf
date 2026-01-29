# Variables for AWS Staging Stack (Kubernetes/EKS Orchestrator)

# =============================================================================
# AWS Configuration
# =============================================================================

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

# =============================================================================
# Stack Configuration
# =============================================================================

variable "stack_name" {
  description = "Name of the ZenML stack"
  type        = string
  default     = "aws-staging"
}

# =============================================================================
# ZenML Server Configuration
# =============================================================================

variable "zenml_server_url" {
  description = "URL of the ZenML server"
  type        = string
}

variable "zenml_api_key" {
  description = "API key for ZenML server authentication"
  type        = string
  sensitive   = true
}

# =============================================================================
# AWS Authentication
# =============================================================================

variable "aws_auth_method" {
  description = "Authentication method for AWS service connector"
  type        = string
  default     = "iam-role"

  validation {
    condition     = contains(["iam-role", "secret-key", "implicit"], var.aws_auth_method)
    error_message = "auth_method must be one of: iam-role, secret-key, implicit"
  }
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID (for iam-role or secret-key auth)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key (for iam-role or secret-key auth)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_iam_role" {
  description = "Whether to create a new IAM role or use existing"
  type        = bool
  default     = false
}

variable "existing_iam_role_arn" {
  description = "ARN of existing IAM role to use (if create_iam_role is false)"
  type        = string
  default     = ""
}

variable "zenml_assume_role_principals" {
  description = "List of AWS principal ARNs that can assume the ZenML IAM role"
  type        = list(string)
  default     = []
}

# =============================================================================
# EKS Configuration
# =============================================================================

variable "eks_cluster_name" {
  description = "Name of the existing EKS cluster"
  type        = string
  default     = "eu-staging-cloud-infra-cluster"
}

# =============================================================================
# S3 Configuration
# =============================================================================

variable "create_s3_bucket" {
  description = "Whether to create a new S3 bucket or use existing"
  type        = bool
  default     = false
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for artifact storage (existing or to create)"
  type        = string
  default     = "zenml-dev"
}

# =============================================================================
# Labeling / Tagging
# =============================================================================

variable "team_name" {
  description = "Team name for resource labeling"
  type        = string
  default     = "ml-platform"
}

variable "cost_center" {
  description = "Cost center for resource labeling"
  type        = string
  default     = "ml-ops"
}

variable "tags" {
  description = "Additional tags to apply to AWS resources"
  type        = map(string)
  default     = {}
}
