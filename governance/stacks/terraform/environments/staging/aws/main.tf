# AWS Staging Stack using Official ZenML Module
# This provisions AWS infrastructure AND registers the stack with ZenML

terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # RECOMMENDED: Use remote backend for state
  # Uncomment and configure after initial setup
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "zenml/staging/aws/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region
}

# Official ZenML AWS Stack Module
# https://registry.terraform.io/modules/zenml-io/zenml-stack/aws/latest
module "zenml_stack" {
  source  = "zenml-io/zenml-stack/aws"
  version = "~> 0.1"  # Check for latest version

  # Stack configuration
  zenml_stack_name            = var.stack_name
  zenml_stack_deployment_name = var.deployment_name
  orchestrator                = var.orchestrator

  # Tags for resource management
  tags = merge(
    var.tags,
    {
      Environment = "staging"
      ManagedBy   = "terraform"
      Project     = "zenml-enterprise-mlops"
    }
  )
}

# Outputs from the module
output "zenml_stack_id" {
  description = "The ID of the registered ZenML stack"
  value       = module.zenml_stack.zenml_stack_id
}

output "zenml_stack_name" {
  description = "The name of the registered ZenML stack"
  value       = module.zenml_stack.zenml_stack_name
}

output "s3_artifact_store_path" {
  description = "S3 path for artifact storage"
  value       = module.zenml_stack.s3_artifact_store_path
}

output "ecr_repository_url" {
  description = "ECR repository URL for container images"
  value       = module.zenml_stack.ecr_repository_url
}

output "post_deployment_instructions" {
  description = "Steps to activate the stack"
  value       = <<-EOT
    ✅ Stack deployed successfully!

    Next steps:
    1. Install required integrations:
       ${var.orchestrator == "sagemaker" ? "zenml integration install aws s3" : "zenml integration install aws s3 skypilot_aws"}

    2. Activate the stack:
       zenml stack set ${var.stack_name}

    3. Verify the stack:
       zenml stack describe ${var.stack_name}

    4. Run a pipeline:
       python run.py --pipeline training
  EOT
}
