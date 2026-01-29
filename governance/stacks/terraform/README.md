# ZenML Stack Terraform Configurations

This directory contains Terraform configurations for deploying enterprise ZenML stacks.

## Quick Start

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
# Edit .env with your ZenML API keys and cloud credentials

# 2. Deploy all stacks (shared → dev → staging → production)
cd governance/stacks/terraform
./deploy.sh deploy-all

# 3. Check status
./deploy.sh status
```

## Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENTERPRISE MLOPS STACKS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐       │
│  │   AWS STAGING STACK          │    │   GCP PRODUCTION STACK        │       │
│  │   (enterprise-dev-staging)   │    │   (enterprise-production)     │       │
│  │                              │    │                               │       │
│  │  Orchestrator: Kubernetes    │    │  Orchestrator: Cloud Composer │       │
│  │               (EKS)          │    │               (Airflow) or    │       │
│  │                              │    │               Vertex AI       │       │
│  │  Artifact Store: S3          │    │                               │       │
│  │  Container Registry: ECR     │    │  Artifact Store: GCS          │       │
│  │                              │    │  Container Registry: GAR      │       │
│  └──────────────────────────────┘    └──────────────────────────────┘       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │              OPTIONAL: SHARED ARTIFACT STORE                      │       │
│  │   gs://zenml-enterprise-shared-artifacts-xxxxx                   │       │
│  │   (Enables cross-workspace model promotion)                       │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
governance/stacks/terraform/
├── deploy.sh                     # Easy deployment script
├── README.md                     # This file
├── .env.example                  # Environment template
├── .gitignore                    # Ignore state and credentials
│
├── environments/
│   ├── development/gcp/          # dev-stack (local orchestrator)
│   ├── staging/
│   │   ├── aws/                  # aws-staging (EKS orchestrator)
│   │   └── gcp/                  # staging-stack (Vertex AI)
│   └── production/
│       ├── aws/                  # (placeholder)
│       └── gcp/                  # gcp-stack (Cloud Composer or Vertex AI)
│
└── shared/gcp/                   # Shared artifact store bucket
```

## Stack Details

### AWS Staging Stack (Kubernetes/EKS)

**Location:** `environments/staging/aws/`

**Components:**
- **Orchestrator:** Kubernetes (EKS) - existing cluster
- **Artifact Store:** S3 bucket
- **Container Registry:** ECR
- **Authentication:** IAM Role with assume role

**Prerequisites:**
- Existing EKS cluster
- Existing S3 bucket (or create new)
- IAM role with appropriate permissions

**Deployment:**
```bash
cd environments/staging/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

**Manual equivalent (what Terraform creates):**
```bash
zenml service-connector register aws_connector \
  --type=aws \
  --auth-method=iam-role \
  --region=eu-central-1 \
  --role_arn=arn:aws:iam::ACCOUNT:role/zenml-connectors \
  --aws_access_key_id=YOUR_KEY \
  --aws_secret_access_key=YOUR_SECRET

zenml orchestrator register kubernetes \
  --flavor=kubernetes \
  --synchronous=False \
  --connector=aws_connector \
  --resource-id=your-eks-cluster

zenml artifact-store register s3 \
  --flavor=s3 \
  --path=s3://your-bucket \
  --connector=aws_connector

zenml container-registry register ecr \
  --flavor=aws \
  --uri=ACCOUNT.dkr.ecr.REGION.amazonaws.com \
  --connector=aws_connector

zenml stack register aws-staging -o kubernetes -a s3 -c ecr
```

---

### GCP Production Stack (Cloud Composer or Vertex AI)

**Location:** `environments/production/gcp/`

**Orchestrator Options:**

#### Option 1: Vertex AI (Default)
- Serverless, no infrastructure to manage
- Best for simple pipeline execution
- Pay-per-use pricing

#### Option 2: Cloud Composer (Airflow)
- Full Airflow capabilities (complex DAGs, sensors, hooks)
- Best for teams already using Airflow
- Managed GKE cluster underneath

**Components:**
- **Orchestrator:** Vertex AI OR Cloud Composer (Airflow)
- **Artifact Store:** GCS bucket
- **Container Registry:** Google Artifact Registry
- **Authentication:** Service Account

**Deployment with Vertex AI:**
```bash
cd environments/production/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: orchestrator_type = "vertex"

terraform init
terraform plan
terraform apply
```

**Deployment with Cloud Composer (Airflow):**
```bash
cd environments/production/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars:
#   orchestrator_type = "airflow"
#   create_composer_environment = true

terraform init
terraform plan
terraform apply

# Note: Cloud Composer creation takes ~20-30 minutes
```

**Using Existing Cloud Composer:**
```hcl
orchestrator_type           = "airflow"
create_composer_environment = false
existing_composer_name      = "my-existing-composer"
```

---

## Shared Artifact Store (Recommended)

Both workspaces can share a single artifact store bucket for seamless cross-workspace promotion:

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
    aws-staging                    gcp-stack
    (dev-staging)                 (production)
```

**Benefits:**
- ZenML's `fileio` works seamlessly across workspaces
- Cross-workspace promotion uses standard ZenML APIs
- Single bucket to manage and configure lifecycle policies

**Deployment:**
```bash
cd shared/gcp
terraform init && terraform apply
# Note the bucket name from output

# Then reference in other stacks:
# shared_artifact_bucket = "zenml-enterprise-shared-artifacts-xxxxx"
```

---

## Prerequisites

### GCP
```bash
# Authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT

# Enable required APIs
gcloud services enable \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  composer.googleapis.com \
  iam.googleapis.com
```

### AWS
```bash
# Configure credentials
aws configure

# Ensure EKS cluster exists
aws eks list-clusters
```

### Terraform
```bash
# Install Terraform >= 1.0
terraform --version
```

---

## Environment Configuration

Create `.env` from `.env.example`:

```bash
# GCP
GCP_PROJECT_ID=zenml-core
GCP_REGION=us-central1

# AWS
AWS_REGION=eu-central-1
AWS_EKS_CLUSTER=eu-staging-cloud-infra-cluster
AWS_S3_BUCKET=zenml-dev

# ZenML Project (same in both workspaces)
ZENML_PROJECT=cancer-detection

# Stack names
ZENML_STAGING_STACK=aws-staging
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

---

## Deployment Commands

### Deploy All
```bash
./deploy.sh deploy-all
```

### Deploy Individual Stack
```bash
# AWS Staging (requires dev-staging workspace)
source scripts/use-workspace.sh dev-staging
./deploy.sh deploy staging-aws

# GCP Production (requires production workspace)
source scripts/use-workspace.sh production
./deploy.sh deploy production-gcp
```

### Check Status
```bash
./deploy.sh status
```

### Destroy
```bash
# Destroy specific stack
./deploy.sh destroy staging-aws

# Destroy all (reverse order)
./deploy.sh destroy-all
```

---

## Verifying Deployment

```bash
# Switch to appropriate workspace
source scripts/use-workspace.sh dev-staging  # or production

# List stacks
zenml stack list

# Describe specific stack
zenml stack describe aws-staging

# Set active stack
zenml stack set aws-staging

# Run a test pipeline
python run.py --pipeline training --environment staging
```

---

## Troubleshooting

### "ZENML_SERVER_URL not set"
```bash
source scripts/use-workspace.sh dev-staging
```

### "Cloud Composer creation failed"
- Check GCP quotas for GKE nodes
- Ensure Composer API is enabled
- Wait up to 30 minutes for creation

### "EKS cluster not found"
```bash
# Verify cluster exists
aws eks describe-cluster --name your-cluster-name --region eu-central-1
```

### "IAM Role cannot be assumed"
- Check trust policy on the IAM role
- Verify credentials have `sts:AssumeRole` permission

### "Module version errors"
```bash
rm -rf .terraform .terraform.lock.hcl
terraform init
```

---

## Security Best Practices

1. **Never commit credentials** - Use environment variables or secret managers
2. **Use remote state** - Enable GCS/S3 backend for state files
3. **Rotate service account keys** - Set up key rotation policies
4. **Principle of least privilege** - IAM roles should have minimal required permissions
5. **Enable audit logging** - GCP Cloud Audit Logs, AWS CloudTrail
