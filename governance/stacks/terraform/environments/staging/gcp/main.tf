# GCP Staging Stack using Official ZenML Module
# This provisions GCP infrastructure AND registers the stack with ZenML

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # RECOMMENDED: Use remote backend for state
  # Uncomment and configure after initial setup
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "zenml/staging/gcp"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Official ZenML GCP Stack Module
# https://registry.terraform.io/modules/zenml-io/zenml-stack/gcp/latest
module "zenml_stack" {
  source  = "zenml-io/zenml-stack/gcp"
  version = "~> 0.1"  # Check for latest version

  # Stack configuration
  zenml_stack_name            = var.stack_name
  zenml_stack_deployment_name = var.deployment_name
  orchestrator                = var.orchestrator

  # GCP-specific settings
  project_id = var.project_id
  region     = var.region

  # Labels for resource management
  labels = merge(
    var.labels,
    {
      environment = "staging"
      managed_by  = "terraform"
      project     = "zenml-enterprise-mlops"
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

output "gcs_artifact_store_path" {
  description = "GCS path for artifact storage"
  value       = module.zenml_stack.gcs_artifact_store_path
}

output "artifact_registry_uri" {
  description = "Artifact Registry URI for container images"
  value       = module.zenml_stack.artifact_registry_uri
}

output "post_deployment_instructions" {
  description = "Steps to activate the stack"
  value       = <<-EOT
    ✅ Stack deployed successfully!

    Next steps:
    1. Install required integrations:
       ${var.orchestrator == "vertex" ? "zenml integration install gcp" : var.orchestrator == "airflow" ? "zenml integration install gcp airflow" : "zenml integration install gcp skypilot_gcp"}

    2. Activate the stack:
       zenml stack set ${var.stack_name}

    3. Verify the stack:
       zenml stack describe ${var.stack_name}

    4. Run a pipeline:
       python run.py --pipeline training
  EOT
}
