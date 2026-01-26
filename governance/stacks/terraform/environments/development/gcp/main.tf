# GCP Development Stack (Local Orchestrator + Cloud Artifact Store)
# This provisions GCP infrastructure for fast local development iteration
# while using cloud storage for artifact persistence.
#
# Workspace: enterprise-dev-staging
# Stack Name: dev-stack
#
# Features:
# - Local orchestrator (fast iteration, no Vertex AI costs)
# - GCS for artifact storage (shared with staging for model access)
# - Artifact Registry for container images
# - Service account for GCP access

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # OPTIONAL: Use remote backend for state
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "zenml/development/gcp"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# ZenML Stack Module (Local Orchestrator)
# =============================================================================

module "zenml_stack" {
  source  = "zenml-io/zenml-stack/gcp"
  version = "~> 0.1"

  # Stack configuration
  zenml_stack_name            = var.stack_name
  zenml_stack_deployment_name = var.deployment_name
  orchestrator                = "local" # Local for fast iteration

  # GCP-specific settings
  project_id = var.project_id
  region     = var.region

  # Labels for resource management and cost tracking
  labels = merge(var.labels, {
    environment = "development"
    workspace   = "enterprise-dev-staging"
    managed_by  = "terraform"
    team        = var.team_name
    cost_center = var.cost_center
  })
}

# =============================================================================
# Outputs
# =============================================================================

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

output "service_account_email" {
  description = "Service account used by ZenML pipelines"
  value       = module.zenml_stack.service_account_email
}

output "post_deployment_instructions" {
  description = "Steps to activate the development stack"
  value       = <<-EOT
    ✅ Development Stack deployed successfully!

    Stack Details:
    - Name: ${var.stack_name}
    - Orchestrator: local (fast iteration)
    - Workspace: enterprise-dev-staging
    - Artifact Store: ${module.zenml_stack.gcs_artifact_store_path}

    Next steps:
    1. Connect to the dev-staging workspace:
       zenml login enterprise-dev-staging

    2. Set the project:
       zenml project set cancer-detection

    3. Activate the stack:
       zenml stack set ${var.stack_name}

    4. Verify the stack:
       zenml stack describe ${var.stack_name}

    5. Run a local training pipeline:
       python run.py --pipeline training --environment local

    Note: This stack uses a local orchestrator for fast iteration.
    For production-like testing, use the staging-stack with Vertex AI.
  EOT
}
