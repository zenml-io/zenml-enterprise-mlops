# AWS Staging Stack: Kubernetes (EKS) Orchestrator
# Using ZenML Terraform Provider for stack component registration
#
# Workspace: enterprise-dev-staging
# Stack Name: aws-staging
#
# Prerequisites:
# - Existing EKS cluster (eu-staging-cloud-infra-cluster)
# - Existing S3 bucket (zenml-dev) or create new
# - AWS credentials with appropriate permissions
#
# Features:
# - Kubernetes (EKS) orchestrator
# - S3 for artifact storage
# - ECR for container images
# - IAM Role-based authentication

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    zenml = {
      source  = "zenml-io/zenml"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  # RECOMMENDED: Use remote backend for state
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "zenml/staging/aws/terraform.tfstate"
  #   region         = "eu-central-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region
}

provider "zenml" {
  server_url = var.zenml_server_url
  api_key    = var.zenml_api_key
}

# =============================================================================
# Local Variables
# =============================================================================

locals {
  # Common labels for ZenML resources
  zenml_labels = {
    environment = "staging"
    workspace   = "enterprise-dev-staging"
    team        = var.team_name
    cost_center = var.cost_center
    managed_by  = "terraform"
  }

  # Common tags for AWS resources
  aws_tags = merge(var.tags, {
    Environment = "staging"
    Workspace   = "enterprise-dev-staging"
    ManagedBy   = "terraform"
    Team        = var.team_name
    CostCenter  = var.cost_center
  })
}

# =============================================================================
# Random suffix for unique resource names
# =============================================================================

resource "random_id" "suffix" {
  byte_length = 4
}

# =============================================================================
# Data Sources - Reference existing infrastructure
# =============================================================================

# Reference existing EKS cluster
data "aws_eks_cluster" "existing" {
  name = var.eks_cluster_name
}

data "aws_eks_cluster_auth" "existing" {
  name = var.eks_cluster_name
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# =============================================================================
# IAM Role for ZenML Service Connector
# =============================================================================

# IAM Role that ZenML will assume
resource "aws_iam_role" "zenml_connector" {
  count = var.create_iam_role ? 1 : 0

  name = "zenml-connector-${var.stack_name}-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          # Allow the ZenML server or local machine to assume this role
          AWS = var.zenml_assume_role_principals
        }
      }
    ]
  })

  tags = local.aws_tags
}

# IAM Policy for ZenML operations
resource "aws_iam_role_policy" "zenml_connector" {
  count = var.create_iam_role ? 1 : 0

  name = "zenml-connector-policy"
  role = aws_iam_role.zenml_connector[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 permissions for artifact store
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      # ECR permissions for container registry
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:CreateRepository",
          "ecr:DescribeRepositories"
        ]
        Resource = "*"
      },
      # EKS permissions for Kubernetes orchestrator
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters"
        ]
        Resource = data.aws_eks_cluster.existing.arn
      }
    ]
  })
}

# =============================================================================
# S3 Bucket for Artifact Store (optional - use existing or create new)
# =============================================================================

resource "aws_s3_bucket" "artifact_store" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = "${var.s3_bucket_name}-${random_id.suffix.hex}"

  tags = local.aws_tags
}

resource "aws_s3_bucket_versioning" "artifact_store" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.artifact_store[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifact_store" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.artifact_store[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

locals {
  # Use created bucket or existing bucket name
  s3_bucket = var.create_s3_bucket ? aws_s3_bucket.artifact_store[0].bucket : var.s3_bucket_name

  # Use created role ARN or existing role ARN
  iam_role_arn = var.create_iam_role ? aws_iam_role.zenml_connector[0].arn : var.existing_iam_role_arn
}

# =============================================================================
# ZenML Service Connector
# =============================================================================

resource "zenml_service_connector" "aws" {
  name        = "${var.stack_name}-aws-connector"
  type        = "aws"
  auth_method = var.aws_auth_method

  configuration = var.aws_auth_method == "iam-role" ? {
    region                = var.region
    role_arn              = local.iam_role_arn
    aws_access_key_id     = var.aws_access_key_id
    aws_secret_access_key = var.aws_secret_access_key
  } : {
    region                = var.region
    aws_access_key_id     = var.aws_access_key_id
    aws_secret_access_key = var.aws_secret_access_key
  }

  # Skip validation during creation to avoid plan-time errors
  verify = false

  labels = local.zenml_labels
}

# =============================================================================
# ZenML Stack Components
# =============================================================================

# Artifact Store (S3)
resource "zenml_stack_component" "artifact_store" {
  name   = "${var.stack_name}-s3"
  type   = "artifact_store"
  flavor = "s3"

  configuration = {
    path = "s3://${local.s3_bucket}"
  }

  connector_id = zenml_service_connector.aws.id
  labels       = local.zenml_labels
}

# Container Registry (ECR)
resource "zenml_stack_component" "container_registry" {
  name   = "${var.stack_name}-ecr"
  type   = "container_registry"
  flavor = "aws"

  configuration = {
    uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
  }

  connector_id = zenml_service_connector.aws.id
  labels       = local.zenml_labels
}

# Kubernetes Orchestrator (EKS)
resource "zenml_stack_component" "orchestrator" {
  name   = "${var.stack_name}-kubernetes"
  type   = "orchestrator"
  flavor = "kubernetes"

  configuration = {
    synchronous = "false"
  }

  connector_id = zenml_service_connector.aws.id

  labels = local.zenml_labels

  depends_on = [zenml_service_connector.aws]
}

# Connect orchestrator to specific EKS cluster (workaround for provider bug)
resource "null_resource" "connect_orchestrator" {
  depends_on = [zenml_stack_component.orchestrator, zenml_service_connector.aws]

  provisioner "local-exec" {
    command = <<-EOT
      zenml orchestrator connect ${var.stack_name}-kubernetes \
        --connector ${var.stack_name}-aws-connector \
        --resource-id ${var.eks_cluster_name}
    EOT

    environment = {
      ZENML_SERVER_URL = var.zenml_server_url
      ZENML_API_KEY    = var.zenml_api_key
    }
  }

  triggers = {
    orchestrator_id = zenml_stack_component.orchestrator.id
    connector_id    = zenml_service_connector.aws.id
    cluster_name    = var.eks_cluster_name
  }
}

# =============================================================================
# ZenML Stack
# =============================================================================

resource "zenml_stack" "aws_staging" {
  name = var.stack_name

  components = {
    artifact_store     = zenml_stack_component.artifact_store.id
    container_registry = zenml_stack_component.container_registry.id
    orchestrator       = zenml_stack_component.orchestrator.id
  }

  labels = local.zenml_labels
}

# =============================================================================
# Outputs
# =============================================================================

output "zenml_stack_id" {
  description = "The ID of the registered ZenML stack"
  value       = zenml_stack.aws_staging.id
}

output "zenml_stack_name" {
  description = "The name of the registered ZenML stack"
  value       = zenml_stack.aws_staging.name
}

output "s3_bucket" {
  description = "S3 bucket for artifacts"
  value       = local.s3_bucket
}

output "ecr_uri" {
  description = "ECR registry URI"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

output "eks_cluster" {
  description = "EKS cluster name"
  value       = var.eks_cluster_name
}

output "iam_role_arn" {
  description = "IAM role ARN for ZenML connector"
  value       = local.iam_role_arn
}

output "post_deployment_instructions" {
  description = "Steps to activate the staging stack"
  value       = <<-EOT
    AWS Staging Stack deployed successfully!

    Stack Details:
    - Name: ${var.stack_name}
    - Orchestrator: Kubernetes (EKS: ${var.eks_cluster_name})
    - Artifact Store: S3 (${local.s3_bucket})
    - Container Registry: ECR
    - Region: ${var.region}
    - Workspace: enterprise-dev-staging

    Labels applied to all ZenML resources:
    - environment: staging
    - team: ${var.team_name}
    - cost_center: ${var.cost_center}

    Next steps:
    1. Install required integrations:
       zenml integration install kubernetes s3 aws

    2. Source workspace (if using workspace switching):
       source scripts/use-workspace.sh dev-staging

    3. Set the project:
       zenml project set cancer-detection

    4. Activate the stack:
       zenml stack set ${var.stack_name}

    5. Run a pipeline:
       python run.py --pipeline training --environment staging
  EOT
}
