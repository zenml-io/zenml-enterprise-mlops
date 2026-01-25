# ZenML Stack Infrastructure (Terraform)

This directory contains Terraform configurations for deploying ZenML stacks using official ZenML Terraform modules.

## Overview

ZenML provides official Terraform modules that provision cloud infrastructure AND automatically register stacks with your ZenML server in one step:

- **AWS Module**: `zenml-io/zenml-stack/aws`
- **GCP Module**: `zenml-io/zenml-stack/gcp`
- **Azure Module**: `zenml-io/zenml-stack/azure`

These modules handle everything: cloud resources + ZenML registration.

## Prerequisites

### 1. ZenML Server

You need a running ZenML server (NOT local):
- ZenML Pro (cloud-hosted): https://cloud.zenml.io
- Self-hosted server: https://docs.zenml.io/deploying-zenml

### 2. Service Account & API Key

```bash
# Create service account
zenml service-account create terraform-deployer

# Get API key (save this!)
zenml service-account api-key <service-account-id> <key-name>
```

### 3. Set Environment Variables

```bash
export ZENML_SERVER_URL="https://your-zenml-server.com"
export ZENML_API_KEY="<your-api-key>"
```

### 4. Cloud CLI Authentication

```bash
# AWS
aws configure

# GCP
gcloud auth application-default login

# Azure
az login
```

### 5. Terraform

```bash
# macOS
brew install terraform

# Verify version >= 1.9
terraform version
```

## Quick Start

### AWS Staging Stack

```bash
cd environments/staging/aws

# Review and edit variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Deploy
terraform init
terraform apply

# Install integrations
zenml integration install aws s3

# Activate stack
zenml stack set <stack-name-from-output>
```

### GCP Staging Stack

```bash
cd environments/staging/gcp

cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

terraform init
terraform apply

zenml integration install gcp
zenml stack set <stack-name-from-output>
```

### Azure Staging Stack

```bash
cd environments/staging/azure

cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

terraform init
terraform apply

zenml integration install azure
zenml stack set <stack-name-from-output>
```

## What Gets Provisioned

### AWS Stack
- **S3 Bucket**: Artifact storage
- **ECR Repository**: Container images
- **CodeBuild Project**: CI/CD builds
- **IAM Roles**: Minimal permissions
- **Orchestrator**: SageMaker, SkyPilot, or Local
- **ZenML Components**: Automatically registered

### GCP Stack
- **GCS Bucket**: Artifact storage
- **Artifact Registry**: Container images
- **Cloud Build**: CI/CD builds
- **Service Accounts**: IAM
- **Orchestrator**: Vertex AI, Airflow, SkyPilot, or Local
- **ZenML Components**: Automatically registered

### Azure Stack
- **Blob Storage**: Artifact storage
- **Container Registry**: Container images
- **Service Principal**: Authentication
- **Orchestrator**: AzureML, SkyPilot, or Local
- **ZenML Components**: Automatically registered

## Directory Structure

```
terraform/
├── environments/
│   ├── staging/
│   │   ├── aws/           # AWS staging stack
│   │   ├── gcp/           # GCP staging stack
│   │   └── azure/         # Azure staging stack
│   └── production/
│       ├── aws/           # AWS production stack
│       ├── gcp/           # GCP production stack
│       └── azure/         # Azure production stack
└── README.md
```

## Configuration

### Common Variables

All modules support these key variables:

```hcl
# Stack configuration
zenml_stack_name = "my-stack"
orchestrator     = "sagemaker"  # or "vertex", "azureml", "skypilot", "local"

# Resource naming
zenml_stack_deployment_name = "my-deployment"

# Tags/Labels
tags = {
  Environment = "staging"
  Team        = "ml-platform"
}
```

### Orchestrator Options

**AWS**: `sagemaker`, `skypilot`, `local`
**GCP**: `vertex`, `airflow`, `skypilot`, `local`
**Azure**: `azureml`, `skypilot`, `local`

## State Management

### Use Remote Backends

**Never** store Terraform state locally in production!

#### AWS (S3 + DynamoDB)

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "zenml/staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

#### GCP (GCS)

```hcl
terraform {
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "zenml/staging"
  }
}
```

#### Azure (Blob Storage)

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "terraformstate"
    container_name       = "tfstate"
    key                  = "zenml/staging.tfstate"
  }
}
```

## Best Practices

### 1. Separate Environments

Use separate state files and workspaces for staging vs production:

```
environments/
├── staging/
│   └── aws/main.tf     # Staging state
└── production/
    └── aws/main.tf     # Production state (separate)
```

### 2. Use Variables Files

```hcl
# terraform.tfvars (gitignored!)
zenml_stack_name = "staging-stack"
region          = "us-east-1"
```

### 3. Never Commit Secrets

Add to `.gitignore`:
```
*.tfvars
*.tfstate
*.tfstate.*
.terraform/
```

### 4. Use Service Accounts

Don't use personal credentials - create dedicated service accounts:

```bash
# AWS
aws iam create-user --user-name zenml-terraform

# GCP
gcloud iam service-accounts create zenml-terraform

# Azure
az ad sp create-for-rbac --name zenml-terraform
```

### 5. Label Everything

```hcl
tags = {
  ManagedBy   = "terraform"
  Environment = "staging"
  Team        = "ml-platform"
  CostCenter  = "engineering"
}
```

## Updating Stacks

```bash
# Pull latest module version
terraform init -upgrade

# Review changes
terraform plan

# Apply updates
terraform apply
```

## Cleanup

⚠️ **WARNING**: This deletes ALL infrastructure!

```bash
terraform destroy
```

## Troubleshooting

### Authentication Errors

```bash
# Verify environment variables
echo $ZENML_SERVER_URL
echo $ZENML_API_KEY

# Test ZenML connection
zenml status

# Verify cloud credentials
aws sts get-caller-identity  # AWS
gcloud auth list             # GCP
az account show              # Azure
```

### State Lock Issues

```bash
# Force unlock (use with caution!)
terraform force-unlock <lock-id>
```

### Module Not Found

```bash
# Re-initialize
rm -rf .terraform
terraform init
```

### Permission Errors

Ensure your cloud credentials have permissions to create:
- Storage buckets
- Container registries
- IAM roles/service accounts
- Orchestrator resources (SageMaker, Vertex AI, etc.)

## Cost Estimates

### Staging (Monthly)

| Cloud | Storage | Registry | Orchestrator | Total |
|-------|---------|----------|--------------|-------|
| AWS | $20 | $10 | $50-200 | $80-230 |
| GCP | $20 | $10 | $50-200 | $80-230 |
| Azure | $20 | $10 | $50-200 | $80-230 |

### Production (Monthly)

| Cloud | Storage | Registry | Orchestrator | HA | Total |
|-------|---------|----------|--------------|-----|-------|
| AWS | $100 | $50 | $200-500 | $100 | $450-750 |
| GCP | $100 | $50 | $200-500 | $100 | $450-750 |
| Azure | $100 | $50 | $200-500 | $100 | $450-750 |

*Estimates vary based on usage*

## Resources

- [ZenML Terraform Modules](https://docs.zenml.io/stacks/deployment/deploy-a-cloud-stack-with-terraform)
- [ZenML Terraform Provider](https://registry.terraform.io/providers/zenml-io/zenml/latest)
- [AWS Module GitHub](https://github.com/zenml-io/terraform-aws-zenml-stack)
- [GCP Module GitHub](https://github.com/zenml-io/terraform-gcp-zenml-stack)
- [Azure Module GitHub](https://github.com/zenml-io/terraform-azure-zenml-stack)
- [Infrastructure as Code Guide](https://docs.zenml.io/user-guides/best-practices/iac)

## Support

- Documentation: https://docs.zenml.io
- GitHub Issues: https://github.com/zenml-io/zenml/issues
- Slack Community: https://zenml.io/slack
