# ZenML Enterprise MLOps Template

Production-ready MLOps template for regulated industries. Demonstrates enterprise patterns with sklearn's breast cancer dataset.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ZenML](https://img.shields.io/badge/ZenML-0.92.0+-orange.svg)](https://zenml.io)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

## What This Solves

**Enterprise customers' #1 pain point**: Multi-environment model promotion with governance.

This template demonstrates:

| Feature | What It Does |
|---------|--------------|
| **GitOps Promotion** | PR → staging, Release → production |
| **Platform Governance** | Hooks enforce standards without touching ML code |
| **Model Control Plane** | Single source of truth for models, lineage, audit |
| **Champion/Challenger** | Safe model rollouts with A/B comparison |
| **Rollback** | One command to revert production models |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/zenml-io/zenml-enterprise-mlops
cd zenml-enterprise-mlops
pip install -r requirements.txt
zenml init

# Run training pipeline
python run.py --pipeline training

# View results
zenml login
```

## Pipelines

| Pipeline | Command | Purpose |
|----------|---------|---------|
| Training | `python run.py --pipeline training` | Train and validate model |
| Batch Inference | `python run.py --pipeline batch_inference` | Score new data with production model |
| Champion/Challenger | `python run.py --pipeline champion_challenger` | Compare staging vs production |

### With Environment Configs

```bash
python run.py --pipeline training --environment local      # Cache enabled, fast iteration
python run.py --pipeline training --environment staging    # Full validation, 70% threshold
python run.py --pipeline training --environment production # Strict, 80% threshold
```

## Repository Structure

```
├── src/                    # Data scientist code
│   ├── pipelines/          # training, batch_inference, champion_challenger
│   └── steps/              # load_data, train_model, evaluate, predict
│
├── governance/             # Platform team code
│   ├── hooks/              # MLflow logging, compliance tracking
│   ├── steps/              # Data validation, model validation
│   ├── docker/             # Platform-managed container settings
│   └── stacks/terraform/   # GCP/AWS infrastructure as code
│
├── configs/                # Environment configs (local, staging, production)
├── scripts/                # promote_model.py, rollback_model.py, build_snapshot.py
└── .github/workflows/      # GitOps automation
```

## Key Patterns

### 1. Clean Developer Experience

Data scientists write pure Python:

```python
@step
def train_model(X: pd.DataFrame, y: pd.Series) -> Annotated[ClassifierMixin, "model"]:
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    return model
```

No wrappers. No boilerplate. Just ML code.

### 2. Platform Governance via Hooks

Platform team enforces standards automatically:

```python
@pipeline(
    on_success=mlflow_success_hook,    # Auto-log to MLflow
    on_failure=compliance_failure_hook  # Alert on failures
)
def training_pipeline():
    # Data scientist code - governance is invisible
    pass
```

### 3. GitOps Model Promotion

```
PR to staging    → Trains model in staging environment
GitHub Release   → Promotes model to production
```

See `.github/workflows/` for implementation.

### 4. Model Rollback

```bash
# Rollback production to previous version
python scripts/rollback_model.py --model breast_cancer_classifier

# Dry run first
python scripts/rollback_model.py --dry-run
```

## Infrastructure

### GCP with Vertex AI

```bash
cd governance/stacks/terraform/environments/staging/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project details
terraform init && terraform apply
```

Features:
- Vertex AI Pipelines orchestrator
- GCS artifact storage
- Workload Identity for GitHub Actions
- BigQuery integration

### Environment Configs

| Environment | Config | Cache | Accuracy Threshold |
|-------------|--------|-------|-------------------|
| Local | `configs/local.yaml` | ✅ Enabled | 70% |
| Staging | `configs/staging.yaml` | ❌ Disabled | 70% |
| Production | `configs/production.yaml` | ❌ Disabled | 80% |

## Documentation

| Document | Audience |
|----------|----------|
| [Architecture Guide](docs/ARCHITECTURE.md) | Everyone - design decisions and patterns |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Data scientists using the platform |
| [Platform Guide](docs/PLATFORM_GUIDE.md) | ML engineers maintaining governance |
| [Pro Features](docs/PRO_FEATURES.md) | Enterprise - RBAC, multi-tenancy, audit |

## ZenML Pro vs OSS

| Feature | OSS | Pro |
|---------|-----|-----|
| Multi-environment stacks | ✅ | ✅ |
| Model Control Plane | ✅ | ✅ |
| GitOps workflows | ✅ | ✅ |
| Hook-based governance | ✅ | ✅ |
| **Projects (multi-tenancy)** | ❌ | ✅ |
| **RBAC** | ❌ | ✅ |
| **Pipeline Snapshots** | ❌ | ✅ |
| **Audit logging** | Basic | Extended |

Both work with this template. Pro adds team isolation and enterprise governance.

## Scripts

```bash
# Promote model between stages
python scripts/promote_model.py --model breast_cancer_classifier --to-stage staging
python scripts/promote_model.py --from-stage staging --to-stage production

# Rollback production model
python scripts/rollback_model.py --model breast_cancer_classifier

# Build pipeline snapshot (Pro)
python scripts/build_snapshot.py --environment staging --stack gcp-staging --run
```

## Requirements

- Python 3.9+
- ZenML 0.92.0+
- Docker (for remote execution)

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

Built with [ZenML](https://zenml.io) | [Docs](https://docs.zenml.io) | [Slack](https://zenml.io/slack)
