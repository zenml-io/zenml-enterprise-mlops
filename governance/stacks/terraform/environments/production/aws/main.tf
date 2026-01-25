# AWS Production Stack using Official ZenML Module
# This provisions AWS infrastructure AND registers the stack with ZenML

terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # REQUIRED for production: Use remote backend for state
  # Uncomment and configure before deploying to production
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "zenml/production/aws/terraform.tfstate"
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
  version = "~> 0.1"  # Pin to specific version for production stability

  # Stack configuration
  zenml_stack_name            = var.stack_name
  zenml_stack_deployment_name = var.deployment_name
  orchestrator                = var.orchestrator

  # Tags for resource management and compliance
  tags = merge(
    var.tags,
    {
      Environment = "production"
      ManagedBy   = "terraform"
      Project     = "zenml-enterprise-mlops"
      Criticality = "high"
      Compliance  = "required"
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
  sensitive   = true  # May contain account details
}

output "ecr_repository_url" {
  description = "ECR repository URL for container images"
  value       = module.zenml_stack.ecr_repository_url
  sensitive   = true
}

output "post_deployment_instructions" {
  description = "Steps to activate the production stack"
  value       = <<-EOT
    ✅ Production stack deployed successfully!

    ⚠️  PRODUCTION DEPLOYMENT CHECKLIST:

    1. Verify remote state backend is configured
    2. Ensure proper IAM roles and policies are set
    3. Review and approve infrastructure changes
    4. Document deployment in change management system

    Next steps:
    1. Install required integrations:
       ${var.orchestrator == "sagemaker" ? "zenml integration install aws s3" : "zenml integration install aws s3 skypilot_aws"}

    2. Activate the stack:
       zenml stack set ${var.stack_name}

    3. Verify the stack:
       zenml stack describe ${var.stack_name}

    4. Run initial validation:
       python run.py --pipeline training --min-accuracy 0.85

    5. Set up monitoring and alerting for production runs
    6. Configure S3 bucket lifecycle policies and backups
  EOT
}
