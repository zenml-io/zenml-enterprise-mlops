# ZenML Stack Terraform Configurations

This directory contains Terraform configurations for deploying ZenML stacks to GCP.

## Architecture

```
governance/stacks/terraform/
├── environments/
│   ├── development/gcp/   # dev-stack (local orchestrator) → enterprise-dev-staging workspace
│   ├── staging/gcp/       # staging-stack (Vertex AI) → enterprise-dev-staging workspace
│   └── production/gcp/    # gcp-stack (Vertex AI) → enterprise-production workspace
└── shared/gcp/            # Shared model exchange bucket for cross-workspace promotion
```

## Prerequisites

1. **GCP CLI** authenticated:
   ```bash
   gcloud auth application-default login
   gcloud config set project zenml-core
   ```

2. **Terraform** installed (>= 1.0):
   ```bash
   terraform --version
   ```

3. **ZenML Server** with API key:
   - Create a service account in your ZenML workspace
   - Generate an API key for the service account

## Authentication

### Recommended: Use the workspace switcher script

```bash
# From repo root, fill in .env with your credentials, then:
source scripts/use-workspace.sh dev-staging   # For dev/staging stacks
source scripts/use-workspace.sh production    # For production stack
```

This sets all env vars for both Terraform and Python.

### Alternative: terraform.tfvars

Edit the `terraform.tfvars` file in each environment directory:

```hcl
zenml_server_url = "https://your-workspace.zenml.io"
zenml_api_key    = "your-api-key"
```

## Deployment Order

Deploy stacks in this order:

### 1. Development Stack (enterprise-dev-staging workspace)

```bash
# Switch to dev-staging workspace
source scripts/use-workspace.sh dev-staging

cd governance/stacks/terraform/environments/development/gcp
terraform init
terraform plan
terraform apply
```

### 2. Staging Stack (enterprise-dev-staging workspace)

```bash
# Same workspace as development
source scripts/use-workspace.sh dev-staging

cd governance/stacks/terraform/environments/staging/gcp
terraform init
terraform plan
terraform apply
```

### 3. Production Stack (enterprise-production workspace)

```bash
# Switch to production workspace
source scripts/use-workspace.sh production

cd governance/stacks/terraform/environments/production/gcp
terraform init
terraform plan
terraform apply
```

### 4. Shared Model Exchange Bucket (Optional)

```bash
cd shared/gcp

# No ZenML connection needed - just GCP
terraform init
terraform plan
terraform apply
```

## Verifying Deployment

After deploying a stack, verify it's registered:

```bash
# Connect to the workspace
zenml login <workspace-name> --api-key

# Set project
zenml project set cancer-detection

# List stacks
zenml stack list

# Describe the stack
zenml stack describe <stack-name>
```

## Stack Details

| Stack | Workspace | Orchestrator | Purpose |
|-------|-----------|--------------|---------|
| dev-stack | enterprise-dev-staging | local | Fast local iteration |
| staging-stack | enterprise-dev-staging | Vertex AI | Production-like testing |
| gcp-stack | enterprise-production | Vertex AI | Production inference |

## Cleanup

To destroy a stack:

```bash
cd environments/<environment>/gcp
terraform destroy
```

## Troubleshooting

### "Missing ZenML API Credentials"

Set the environment variables:
```bash
export ZENML_SERVER_URL="https://your-workspace.zenml.io"
export ZENML_API_KEY="your-api-key"
```

Or fill in terraform.tfvars.

### "Permission denied" on GCP

Ensure you're authenticated:
```bash
gcloud auth application-default login
```

### Module version errors

If you see module errors, delete .terraform and reinitialize:
```bash
rm -rf .terraform .terraform.lock.hcl
terraform init
```
