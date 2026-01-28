# ZenML Stack Terraform Configurations

This directory contains Terraform configurations for deploying ZenML stacks to GCP.

## Quick Start

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
# Edit .env with your ZenML API keys and GCP project

# 2. Deploy all stacks (shared → dev → staging → production)
cd governance/stacks/terraform
./deploy.sh deploy-all

# 3. Check status
./deploy.sh status
```

## Architecture

```
governance/stacks/terraform/
├── deploy.sh                 # Easy deployment script
├── environments/
│   ├── development/gcp/      # dev-stack (local orchestrator) → enterprise-dev-staging
│   ├── staging/gcp/          # staging-stack (Vertex AI) → enterprise-dev-staging
│   └── production/gcp/       # gcp-stack (Vertex AI) → enterprise-production
└── shared/gcp/               # Shared artifact store bucket
```

### Shared Artifact Store (Recommended)

Both workspaces share a single artifact store bucket:

```
┌─────────────────────────────────────────────────────────────┐
│           Shared Artifact Store Bucket                       │
│  gs://zenml-enterprise-shared-artifacts-xxxxx               │
│                                                             │
│  ├── artifacts/           ← All pipeline artifacts          │
│  ├── model-exchange/      ← Cross-workspace promotion       │
│  └── (zenml-managed)      ← Internal metadata               │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
    staging-stack                  gcp-stack
    (dev-staging)                 (production)
```

**Benefits:**
- ZenML's `fileio` works seamlessly (same artifact store bounds)
- Cross-workspace promotion uses standard ZenML APIs
- Single bucket to manage, backup, and configure lifecycle policies

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

3. **Environment file** configured:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Environment Configuration

The `.env` file (copy from `.env.example`) contains:

```bash
# GCP
GCP_PROJECT_ID=zenml-core
GCP_REGION=us-central1

# ZenML Project (same in both workspaces)
ZENML_PROJECT=cancer-detection

# Stack names
ZENML_DEV_STACK=dev-stack
ZENML_STAGING_STACK=staging-stack
ZENML_PRODUCTION_STACK=gcp-stack

# Dev-Staging workspace credentials
DEV_STAGING_ZENML_SERVER_URL=https://...
DEV_STAGING_ZENML_API_KEY=...

# Production workspace credentials
PRODUCTION_ZENML_SERVER_URL=https://...
PRODUCTION_ZENML_API_KEY=...

# Shared bucket (set after deploying shared/gcp)
# SHARED_ARTIFACT_BUCKET=zenml-enterprise-shared-artifacts-xxxxx
```

## Deployment

### Option 1: Deploy All (Recommended)

```bash
cd governance/stacks/terraform
./deploy.sh deploy-all
```

This deploys in order: shared → development → staging → production

### Option 2: Deploy Individual Stacks

```bash
# Switch workspace first
source scripts/use-workspace.sh dev-staging

# Deploy specific stack
./deploy.sh deploy staging
```

### Option 3: Manual Deployment

```bash
# 1. Deploy shared bucket (no ZenML credentials needed)
cd governance/stacks/terraform/shared/gcp
terraform init && terraform apply
# Note the bucket name from output

# 2. Deploy dev-staging stacks
source scripts/use-workspace.sh dev-staging

cd ../environments/development/gcp
terraform init && terraform apply

cd ../staging/gcp
terraform init && terraform apply -var="shared_artifact_bucket=<bucket-name>"

# 3. Deploy production stack
source scripts/use-workspace.sh production

cd ../production/gcp
terraform init && terraform apply -var="shared_artifact_bucket=<bucket-name>"
```

## Workspace Switching

The `use-workspace.sh` script loads credentials from `.env`:

```bash
# Switch to dev-staging workspace
source scripts/use-workspace.sh dev-staging

# Switch to production workspace
source scripts/use-workspace.sh production
```

This exports:
- `ZENML_SERVER_URL` and `ZENML_API_KEY` for ZenML CLI
- `TF_VAR_*` variables for Terraform
- `ZENML_PROJECT` and stack names

## Stack Details

| Stack | Workspace | Orchestrator | Purpose |
|-------|-----------|--------------|---------|
| dev-stack | enterprise-dev-staging | local | Fast local iteration |
| staging-stack | enterprise-dev-staging | Vertex AI | Production-like testing |
| gcp-stack | enterprise-production | Vertex AI | Production inference |

## Verifying Deployment

```bash
# Check deployment status
./deploy.sh status

# Verify in ZenML
source scripts/use-workspace.sh dev-staging
zenml project set $ZENML_PROJECT
zenml stack list
zenml stack describe $ZENML_STAGING_STACK
```

## Cleanup

```bash
# Destroy all stacks (reverse order)
./deploy.sh destroy-all

# Or destroy specific stack
./deploy.sh destroy staging
```

## Troubleshooting

### "ZENML_SERVER_URL not set"

```bash
source scripts/use-workspace.sh dev-staging
```

### "GCP not authenticated"

```bash
gcloud auth application-default login
```

### "Bucket contains objects"

The destroy script handles this automatically. If manual:
```bash
gsutil -m rm -r "gs://bucket-name/*"
terraform destroy
```

### "Module version errors"

```bash
rm -rf .terraform .terraform.lock.hcl
terraform init
```
