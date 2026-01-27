# Plan: 2-Workspace Architecture for ZenML Enterprise MLOps

## Enterprise Requirements Mapping

This plan addresses common enterprise MLOps requirements:

| Requirement | How We Address It | Status |
|-------------|-------------------|--------|
| **Hub-and-spoke → Consolidated** | 2-workspace architecture (dev-staging + production) with label-based cost tracking | ✅ Complete |
| **Multi-Environment Model Promotion** | Cross-workspace promotion via `promote_cross_workspace.py` with metadata preservation | ✅ Complete |
| **GitOps Promotion** | GitHub workflows triggered by PR/release with approval gates | ✅ Complete |
| **Lineage Across Project Boundaries** | Full lineage in dev-staging, metadata links in production | ✅ Complete |
| **Approval Gates** | GitHub environment protection rules on `production` environment | ✅ Complete |
| **Champion/Challenger** | Existing `champion_challenger.py` pipeline | ✅ Already exists |
| **Rollbacks** | Existing `rollback_model.py` script | ✅ Already exists |
| **GCP/Vertex AI Integration** | Terraform configs for Vertex AI orchestrator, GCS, Artifact Registry | ✅ Complete |
| **MLflow Integration** | Hook-based auto-logging via `governance/hooks/mlflow_hook.py` | ✅ Already exists |
| **Platform-Enforced Steps** | Hooks inject MLflow, compliance without user code changes | ✅ Already exists |
| **Batch Inference by Alias** | `model=Model(name="...", version=ModelStages.PRODUCTION)` | ✅ Already exists |
| **Real-Time Inference** | Pipeline Deployments via `realtime_inference.py` | ✅ Already exists |
| **Audit Trails** | Model Control Plane + metadata preservation across workspaces | ✅ Complete |
| **Container Management** | Platform-managed Docker settings in `governance/docker/` | ✅ Already exists |

### Key Pain Points Addressed

1. **"Promotion is manual and error-prone"** → Automated cross-workspace promotion via GitOps
2. **"Can't trace prediction back to training"** → Full lineage in dev-staging, metadata links in production
3. **"Platform team can't enforce governance"** → Hook-based injection, no user code changes needed
4. **"Complex KFP wrapper components"** → Pure Python with `@step` and `@pipeline`, hooks for platform concerns

---

## Executive Summary

Migrate from single-workspace to **2-workspace architecture**:
- `enterprise-dev-staging`: Development + staging (full lineage)
- `enterprise-production`: Production only (imported models, inference lineage)

**Key Decisions:**
- Model promotion: Export/import with rich metadata
- Pipeline code promotion: Build snapshots from same Git commit in each workspace
- GCP project: `zenml-core` (single project, labels for cost tracking)
- Lineage: Full in dev-staging, inference lineage + metadata links in production

---

## Target Architecture

```
Organization: Enterprise MLOps
│
├── Workspace: enterprise-dev-staging
│   ├── Project: cancer-detection
│   ├── Stack: dev-stack (local orchestrator, fast iteration)
│   ├── Stack: staging-stack (Vertex AI, production-like testing)
│   ├── Training pipeline runs (FULL LINEAGE)
│   ├── Model versions (none → staging stages)
│   └── Test batch inference runs (staging validation)
│
└── Workspace: enterprise-production
    ├── Project: cancer-detection
    ├── Stack: gcp-stack (Vertex AI, production)
    ├── Imported model versions (production stage)
    ├── Batch inference pipeline snapshots
    ├── Real-time inference deployments
    └── Production batch inference runs (INFERENCE LINEAGE)
```

---

## Why This Architecture

| Benefit | How It Works |
|---------|--------------|
| **ZenML Version Isolation** | Upgrade dev-staging first, test, then production |
| **Lineage Preservation** | Full training lineage in dev-staging, inference lineage in production |
| **Audit Trail** | Metadata in production links back to source with all metrics |
| **Clear Workflow** | Dev → staging (same workspace), staging → production (cross-workspace) |

---

## Phase 1: Documentation Updates

### 1.1 Update CLAUDE.md
**File:** `/home/htahir1/workspace/zenml_io/zenml-enterprise-mlops/CLAUDE.md`

Key changes:
- Change "Single Workspace Architecture" to "2-Workspace Architecture"
- Update paradigm description:
  - **Pro users**: 2 workspaces (dev-staging + production)
  - **OSS users**: 2 separate ZenML servers
- Update why: ZenML version upgrade isolation
- Add cross-workspace promotion explanation
- Update example workflows

### 1.2 Update docs/ARCHITECTURE.md
**File:** `/home/htahir1/workspace/zenml_io/zenml-enterprise-mlops/docs/ARCHITECTURE.md`

Key changes:
- Rewrite Multi-Tenancy section for 2-workspace model
- Add cross-workspace promotion documentation
- Add diagram: dev-staging → production flow
- Document shared GCS bucket for model exchange
- Update lineage explanation

### 1.3 Update docs/PRO_FEATURES.md
**File:** `/home/htahir1/workspace/zenml_io/zenml-enterprise-mlops/docs/PRO_FEATURES.md`

Key changes:
- Document workspace-per-environment-group pattern
- Add version upgrade isolation benefit
- Update RBAC guidance

---

## Phase 2: Terraform Infrastructure

### 2.1 Create Development Stack Config
**New directory:** `governance/stacks/terraform/environments/development/gcp/`

**Files to create:**
- `main.tf`
- `variables.tf`
- `terraform.tfvars.example`

**Development stack specifics:**
```hcl
# main.tf
module "zenml_stack" {
  source  = "zenml-io/zenml-stack/gcp"
  version = "~> 0.1"

  zenml_stack_name            = var.stack_name  # "dev-stack"
  zenml_stack_deployment_name = "zenml-development"
  orchestrator                = "local"  # Fast iteration

  project_id = var.project_id  # zenml-core
  region     = var.region

  labels = {
    environment = "development"
    workspace   = "enterprise-dev-staging"
  }
}
```

### 2.2 Create Staging Stack Config
**New directory:** `governance/stacks/terraform/environments/staging/gcp/` (already exists, update)

**Changes:**
```hcl
# variables.tf - change defaults
variable "stack_name" {
  default = "staging-stack"  # Was "gcp-staging"
}

# main.tf - update labels
labels = {
  environment = "staging"
  workspace   = "enterprise-dev-staging"
}
```

### 2.3 Update Production Stack Config
**Directory:** `governance/stacks/terraform/environments/production/gcp/`

**Changes:**
```hcl
# variables.tf - change defaults
variable "stack_name" {
  default = "gcp-stack"  # Was "gcp-production"
}

# main.tf - update labels
labels = {
  environment = "production"
  workspace   = "enterprise-production"
}
```

### 2.4 Create Shared Model Exchange Bucket
**Add to:** `governance/stacks/terraform/shared/gcp/model_exchange.tf`

```hcl
resource "google_storage_bucket" "model_exchange" {
  name     = "zenml-core-model-exchange"
  project  = "zenml-core"
  location = "us-central1"

  uniform_bucket_level_access = true

  labels = {
    purpose = "cross-workspace-model-promotion"
  }
}

# Grant access to both workspace service accounts
resource "google_storage_bucket_iam_member" "dev_staging_access" {
  bucket = google_storage_bucket.model_exchange.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.dev_staging_service_account}"
}

resource "google_storage_bucket_iam_member" "production_access" {
  bucket = google_storage_bucket.model_exchange.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.production_service_account}"
}
```

### 2.5 Terraform Deployment Order
```bash
# 1. Development stack (in enterprise-dev-staging workspace)
cd governance/stacks/terraform/environments/development/gcp
terraform init && terraform apply

# 2. Staging stack (in enterprise-dev-staging workspace)
cd governance/stacks/terraform/environments/staging/gcp
terraform init && terraform apply

# 3. Production stack (in enterprise-production workspace)
cd governance/stacks/terraform/environments/production/gcp
terraform init && terraform apply

# 4. Shared model exchange bucket
cd governance/stacks/terraform/shared/gcp
terraform init && terraform apply
```

---

## Phase 3: Cross-Workspace Promotion Scripts

### 3.1 Create promote_cross_workspace.py
**New file:** `/home/htahir1/workspace/zenml_io/zenml-enterprise-mlops/scripts/promote_cross_workspace.py`

**Functionality:**
```python
@click.command()
@click.option("--model", required=True)
@click.option("--source-workspace", type=click.Choice(["enterprise-dev-staging"]))
@click.option("--dest-workspace", type=click.Choice(["enterprise-production"]))
@click.option("--source-stage", default="staging")
@click.option("--dest-stage", default="production")
@click.option("--export-only", is_flag=True)
@click.option("--import-from", type=str)
def promote_cross_workspace(...):
    """
    Export model from source workspace → shared GCS bucket
    Import into destination workspace with rich metadata
    """
```

**Export phase:**
1. Connect to source workspace
2. Load model version and artifacts
3. Save to `gs://zenml-core-model-exchange/exports/{model}/{timestamp}/`
4. Create manifest.json with:
   - Source workspace, version, pipeline run ID
   - All metrics (accuracy, precision, recall, etc.)
   - Git commit, training date
   - Hyperparameters
   - Promotion chain history

**Import phase:**
1. Connect to destination workspace
2. Load artifacts from shared bucket
3. Run import pipeline to create model version
4. Log all source metadata as run_metadata
5. Set to destination stage

### 3.2 Create import_model.py Pipeline
**New file:** `/home/htahir1/workspace/zenml_io/zenml-enterprise-mlops/src/pipelines/import_model.py`

```python
@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        description="Imported from cross-workspace promotion",
        tags=["imported"],
    ),
)
def import_model_pipeline(
    model_artifact: ClassifierMixin,
    scaler_artifact: Optional[TransformerMixin],
    import_metadata: dict,
    dest_stage: str = "production",
):
    """
    Creates model version in destination workspace with:
    - Registered artifacts
    - Source lineage metadata
    - Appropriate stage
    """
    registered_model = register_model(model_artifact, import_metadata)
    registered_scaler = register_scaler(scaler_artifact)
    log_cross_workspace_metadata(import_metadata)
    set_stage(dest_stage)
```

### 3.3 Update Existing Scripts

**File:** `scripts/promote_model.py`
- Keep for within-workspace stage transitions (none → staging within dev-staging)
- Add header comment explaining when to use this vs cross-workspace script

**File:** `scripts/build_snapshot.py`
- Add `--workspace` parameter to specify which workspace to connect to
- Update to use `zenml login {workspace}` instead of `zenml connect`

---

## Phase 4: GitHub Workflows

### 4.1 Update train-staging.yml
**File:** `.github/workflows/train-staging.yml`

```yaml
name: Train Model (Dev-Staging)

on:
  pull_request:
    branches: [main]
    paths: ['src/**', 'governance/**', 'configs/**']

jobs:
  train:
    runs-on: ubuntu-latest
    env:
      ZENML_DEV_STAGING_API_KEY: ${{ secrets.ZENML_DEV_STAGING_API_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup
        run: |
          pip install uv
          uv pip install --system -r requirements.txt

      # Connect to dev-staging workspace
      - name: Connect to dev-staging
        run: |
          zenml login enterprise-dev-staging --api-key $ZENML_DEV_STAGING_API_KEY
          zenml project set cancer-detection
          zenml stack set staging-stack

      - name: Train model
        run: |
          python scripts/build_snapshot.py \
            --environment staging \
            --stack staging-stack \
            --run
```

### 4.2 Create test-batch-inference.yml
**New file:** `.github/workflows/test-batch-inference.yml`

```yaml
name: Test Batch Inference (Staging)

on:
  workflow_run:
    workflows: ["Train Model (Dev-Staging)"]
    types: [completed]
  pull_request:
    paths: ['src/pipelines/batch_inference.py']

jobs:
  test:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'pull_request' }}

    steps:
      - uses: actions/checkout@v4

      - name: Connect to dev-staging
        run: |
          zenml login enterprise-dev-staging --api-key ${{ secrets.ZENML_DEV_STAGING_API_KEY }}
          zenml project set cancer-detection
          zenml stack set staging-stack

      - name: Test batch inference
        run: python run.py --pipeline batch_inference --environment staging
```

### 4.3 Create promote-to-production.yml
**New file:** `.github/workflows/promote-to-production.yml`

```yaml
name: Promote to Production

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      model_version:
        default: 'staging'

jobs:
  export:
    runs-on: ubuntu-latest
    outputs:
      export_path: ${{ steps.export.outputs.path }}

    steps:
      - uses: actions/checkout@v4

      - name: Connect to dev-staging
        run: |
          zenml login enterprise-dev-staging --api-key ${{ secrets.ZENML_DEV_STAGING_API_KEY }}
          zenml project set cancer-detection

      - name: Export model
        id: export
        run: |
          python scripts/promote_cross_workspace.py \
            --model breast_cancer_classifier \
            --source-workspace enterprise-dev-staging \
            --source-stage staging \
            --export-only
          echo "path=$(cat export_path.txt)" >> $GITHUB_OUTPUT

  import:
    needs: export
    runs-on: ubuntu-latest
    environment: production  # Requires approval gate

    steps:
      - uses: actions/checkout@v4

      - name: Connect to production
        run: |
          zenml login enterprise-production --api-key ${{ secrets.ZENML_PRODUCTION_API_KEY }}
          zenml project set cancer-detection
          zenml stack set gcp-stack

      - name: Import model
        run: |
          python scripts/promote_cross_workspace.py \
            --model breast_cancer_classifier \
            --dest-workspace enterprise-production \
            --import-from ${{ needs.export.outputs.export_path }} \
            --dest-stage production
```

### 4.4 Create deploy-batch-inference-prod.yml
**New file:** `.github/workflows/deploy-batch-inference-prod.yml`

```yaml
name: Deploy Batch Inference to Production

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  test-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Connect to dev-staging
        run: |
          zenml login enterprise-dev-staging --api-key ${{ secrets.ZENML_DEV_STAGING_API_KEY }}
          zenml project set cancer-detection
          zenml stack set staging-stack

      - name: Build and run staging snapshot
        run: |
          python scripts/build_snapshot.py \
            --pipeline batch_inference \
            --environment staging \
            --stack staging-stack \
            --run

  deploy-production:
    needs: test-staging
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Connect to production
        run: |
          zenml login enterprise-production --api-key ${{ secrets.ZENML_PRODUCTION_API_KEY }}
          zenml project set cancer-detection
          zenml stack set gcp-stack

      - name: Build production snapshot
        run: |
          python scripts/build_snapshot.py \
            --pipeline batch_inference \
            --environment production \
            --stack gcp-stack
          # Note: No --run, just create snapshot
```

### 4.5 Update batch-inference.yml (Scheduled)
**File:** `.github/workflows/batch-inference.yml`

```yaml
name: Scheduled Batch Inference

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Connect to production
        run: |
          zenml login enterprise-production --api-key ${{ secrets.ZENML_PRODUCTION_API_KEY }}
          zenml project set cancer-detection
          zenml stack set gcp-stack

      - name: Run batch inference
        run: python run.py --pipeline batch_inference --environment production
```

---

## Phase 5: Terraform Deployment

### 5.1 Prerequisites
```bash
# GCP authentication
gcloud auth application-default login
gcloud config set project zenml-core

# Verify workspaces exist
zenml login enterprise-dev-staging
zenml login enterprise-production
```

### 5.2 Deploy Development Stack
```bash
cd governance/stacks/terraform/environments/development/gcp

# Create tfvars
cat > terraform.tfvars << 'EOF'
project_id = "zenml-core"
region = "us-central1"
stack_name = "dev-stack"
orchestrator = "local"
labels = {
  team = "data-science"
  cost_center = "ml-platform"
}
EOF

# Set ZenML credentials for dev-staging workspace
export ZENML_SERVER_URL="https://enterprise-dev-staging.cloud.zenml.io"
export ZENML_API_KEY="..."

terraform init
terraform plan
terraform apply
```

### 5.3 Deploy Staging Stack
```bash
cd governance/stacks/terraform/environments/staging/gcp

cat > terraform.tfvars << 'EOF'
project_id = "zenml-core"
region = "us-central1"
stack_name = "staging-stack"
orchestrator = "vertex"
labels = {
  team = "data-science"
  cost_center = "ml-platform"
}
EOF

# Same workspace as development
export ZENML_SERVER_URL="https://enterprise-dev-staging.cloud.zenml.io"

terraform init
terraform plan
terraform apply
```

### 5.4 Deploy Production Stack
```bash
cd governance/stacks/terraform/environments/production/gcp

cat > terraform.tfvars << 'EOF'
project_id = "zenml-core"
region = "us-central1"
stack_name = "gcp-stack"
orchestrator = "vertex"
labels = {
  team = "data-science"
  cost_center = "ml-platform"
  criticality = "high"
}
EOF

# Production workspace
export ZENML_SERVER_URL="https://enterprise-production.cloud.zenml.io"
export ZENML_API_KEY="..."

terraform init
terraform plan
terraform apply
```

### 5.5 Create Model Exchange Bucket
```bash
cd governance/stacks/terraform/shared/gcp

terraform init
terraform plan
terraform apply

# Output: gs://zenml-core-model-exchange
```

---

## Phase 6: Verification

### 6.1 Verify Stacks
```bash
# Dev-staging workspace
zenml login enterprise-dev-staging
zenml project set cancer-detection
zenml stack list
# Should show: dev-stack, staging-stack

# Production workspace
zenml login enterprise-production
zenml project set cancer-detection
zenml stack list
# Should show: gcp-stack
```

### 6.2 Test Training
```bash
zenml login enterprise-dev-staging
zenml project set cancer-detection
zenml stack set staging-stack

python run.py --pipeline training --environment staging
```

### 6.3 Test Cross-Workspace Promotion
```bash
# Export from dev-staging
python scripts/promote_cross_workspace.py \
  --model breast_cancer_classifier \
  --source-workspace enterprise-dev-staging \
  --source-stage staging \
  --export-only

# Import to production
python scripts/promote_cross_workspace.py \
  --model breast_cancer_classifier \
  --dest-workspace enterprise-production \
  --import-from gs://zenml-core-model-exchange/exports/... \
  --dest-stage production

# Verify in production
zenml login enterprise-production
zenml model version list breast_cancer_classifier
```

### 6.4 Test Batch Inference
```bash
zenml login enterprise-production
zenml project set cancer-detection
zenml stack set gcp-stack

python run.py --pipeline batch_inference --environment production
```

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `governance/stacks/terraform/environments/development/gcp/main.tf` | Dev stack Terraform |
| `governance/stacks/terraform/environments/development/gcp/variables.tf` | Dev stack variables |
| `governance/stacks/terraform/environments/development/gcp/terraform.tfvars.example` | Dev stack example config |
| `governance/stacks/terraform/shared/gcp/model_exchange.tf` | Shared bucket for promotion |
| `scripts/promote_cross_workspace.py` | Cross-workspace model promotion |
| `src/pipelines/import_model.py` | Import pipeline for destination workspace |
| `.github/workflows/test-batch-inference.yml` | Test inference in staging |
| `.github/workflows/promote-to-production.yml` | Cross-workspace promotion |
| `.github/workflows/deploy-batch-inference-prod.yml` | Deploy inference pipeline |

### Modified Files
| File | Changes |
|------|---------|
| `CLAUDE.md` | 2-workspace architecture, new workflows |
| `docs/ARCHITECTURE.md` | Multi-tenancy section rewrite |
| `docs/PRO_FEATURES.md` | Workspace guidance update |
| `governance/stacks/terraform/environments/staging/gcp/variables.tf` | stack_name default |
| `governance/stacks/terraform/environments/production/gcp/variables.tf` | stack_name default |
| `scripts/build_snapshot.py` | Add --workspace parameter |
| `scripts/promote_model.py` | Add note about cross-workspace script |
| `.github/workflows/train-staging.yml` | Update for workspace login |
| `.github/workflows/batch-inference.yml` | Update for production workspace |

---

## GitHub Secrets Required

| Secret | Workspace | Description |
|--------|-----------|-------------|
| `ZENML_DEV_STAGING_STORE_URL` | enterprise-dev-staging | ZenML server URL for dev-staging workspace |
| `ZENML_DEV_STAGING_API_KEY` | enterprise-dev-staging | API key for dev-staging workspace |
| `ZENML_PRODUCTION_STORE_URL` | enterprise-production | ZenML server URL for production workspace |
| `ZENML_PRODUCTION_API_KEY` | enterprise-production | API key for production workspace |
| `GCP_SA_KEY` | N/A | GCP service account for artifact access (optional) |

---

## Task Execution Order

1. [x] **Phase 1**: Update documentation (CLAUDE.md, ARCHITECTURE.md, PRO_FEATURES.md)
2. [x] **Phase 2**: Create/update Terraform configs
3. [x] **Phase 3**: Create cross-workspace scripts
4. [x] **Phase 4**: Update GitHub workflows
5. [ ] **Phase 5**: Deploy Terraform stacks (requires GCP credentials)
6. [ ] **Phase 6**: Verification testing (requires deployed stacks)
