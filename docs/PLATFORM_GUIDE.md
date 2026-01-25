# Platform Guide

For platform engineers and MLOps teams responsible for infrastructure, deployments, and governance.

## Table of Contents

- [Overview](#overview)
- [Infrastructure Management](#infrastructure-management)
- [Governance Implementation](#governance-implementation)
- [Deployment Workflows](#deployment-workflows)
- [CI/CD Integration](#cicd-integration)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Incident Response](#incident-response)
- [Maintenance](#maintenance)

## Overview

Platform team responsibilities:
- Managing ZenML stacks across environments
- Implementing governance hooks
- Approving production deployments
- Monitoring model performance
- Incident response and rollbacks
- Secrets and access control

### Deployment Strategy

```
Development → Staging → Production
   (local)     (CI/CD)   (manual approval)
```

**Key principles:**
1. **Immutability** - Production uses pipeline snapshots (Pro)
2. **GitOps** - Promotions triggered by Git events
3. **Approval Gates** - Production requires manual approval
4. **Rollback** - Can revert instantly
5. **Audit** - Everything logged and traceable

## Infrastructure Management

### Stack Setup

**Local Stack** (for developers):
```bash
zenml orchestrator register local-orchestrator --flavor=local
zenml artifact-store register local-artifact-store --flavor=local
zenml stack register local-dev -o local-orchestrator -a local-artifact-store
```

**GCP Stack** (staging/production):
```bash
# Use Terraform (recommended)
cd governance/stacks/terraform/environments/staging/gcp
terraform init && terraform apply

# Or manually:
zenml orchestrator register vertex-staging \
    --flavor=vertex \
    --project=your-project-staging \
    --location=us-central1

zenml artifact-store register gcs-staging \
    --flavor=gcp \
    --path=gs://your-bucket-staging/artifacts

zenml stack register staging \
    -o vertex-staging \
    -a gcs-staging
```

### Secrets Management

```bash
# GCP credentials
zenml secret create gcp-credentials \
    --token=@/path/to/service-account.json

# MLflow credentials
zenml secret create mlflow-credentials \
    --username=zenml \
    --password=<password>

# Rotate secrets
zenml secret update gcp-credentials \
    --token=@/path/to/new-service-account.json
```

### Docker Image Management

Platform-managed Docker settings in `governance/docker/docker_settings.py`:

```python
from governance.docker import STANDARD_DOCKER_SETTINGS, GPU_DOCKER_SETTINGS

@pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
def training_pipeline():
    ...
```

Build custom images:
```bash
# Build and push
docker build -t gcr.io/your-project/zenml-base:v1.0.0 -f governance/docker/Dockerfile .
docker push gcr.io/your-project/zenml-base:v1.0.0
```

## Governance Implementation

### Platform Hooks

Hooks enforce governance without developer code changes.

**MLflow Hook** (`governance/hooks/mlflow_hook.py`):
```python
def mlflow_success_hook() -> None:
    """Auto-log to MLflow after each step"""
    context = get_step_context()
    mlflow.log_param("step", context.step_run.name)
    mlflow.log_param("pipeline", context.pipeline_run.name)
```

**Compliance Hook** (`governance/hooks/compliance_hook.py`):
```python
def compliance_failure_hook() -> None:
    """Alert on failures for audit trail"""
    context = get_step_context()
    send_alert(f"Pipeline failed: {context.pipeline_run.name}")
```

**Usage** - applied via pipeline decorator:
```python
@pipeline(
    on_success=mlflow_success_hook,
    on_failure=compliance_failure_hook
)
def training_pipeline():
    ...
```

### Shared Validation Steps

**Data Validation** (`governance/steps/data_validation.py`):
```python
@step
def validate_data_quality(
    dataset: pd.DataFrame,
    min_rows: int = 100,
    max_missing_fraction: float = 0.1,
) -> pd.DataFrame:
    """Platform-enforced data quality"""
```

**Model Validation** (`governance/steps/model_validation.py`):
```python
@step
def validate_model_performance(
    metrics: dict,
    min_accuracy: float = 0.8,
) -> None:
    """Fail if model doesn't meet thresholds"""
```

## Deployment Workflows

### 1. Development (Local)

```bash
git checkout -b feature/improve-model
python run.py --pipeline training
# Test, iterate, commit
git push origin feature/improve-model
```

### 2. Staging (Automatic on PR)

**Trigger**: PR to `staging` or `main` branch

**Workflow** (`.github/workflows/train-staging.yml`):
1. PR created → CI triggered
2. Build snapshot (Pro) or run directly (OSS)
3. Validate model meets staging thresholds
4. Post results to PR

**Manual staging run:**
```bash
zenml stack set staging
python run.py --pipeline training --environment staging
```

### 3. Production (Release-Triggered)

**Trigger**: GitHub release created

**Workflow** (`.github/workflows/promote-production.yml`):
1. Create release tag: `git tag v1.0.0 && git push origin v1.0.0`
2. Create GitHub release
3. Workflow validates and promotes model

**Manual production promotion:**
```bash
# Promote staging to production
python scripts/promote_model.py \
    --model breast_cancer_classifier \
    --from-stage staging \
    --to-stage production

# Force (demote current production)
python scripts/promote_model.py \
    --from-stage staging \
    --to-stage production \
    --force
```

### 4. Rollback

```bash
# Rollback to previous version
python scripts/rollback_model.py --model breast_cancer_classifier

# Rollback to specific version
python scripts/rollback_model.py --to-version 3

# Dry run first
python scripts/rollback_model.py --dry-run
```

### Deployment Checklist

- [ ] Model meets thresholds (accuracy >= 0.80)
- [ ] Batch inference tested in staging
- [ ] Stakeholder approval obtained
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Monitoring alerts configured

## CI/CD Integration

### GitHub Actions

**Required secrets** (Settings → Secrets):

| Secret | Description |
|--------|-------------|
| `ZENML_STORE_URL` | ZenML server URL |
| `ZENML_STORE_API_KEY` | API key |
| `ZENML_PROJECT` | Project name |
| `ZENML_STAGING_STACK` | Staging stack |
| `ZENML_PRODUCTION_STACK` | Production stack |

**Environment protection** (Settings → Environments):
- Staging: No required reviewers
- Production: 2 required reviewers, only `main` branch

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - train
  - promote

train_staging:
  stage: train
  script:
    - zenml connect --url $ZENML_STORE_URL --api-key $ZENML_STORE_API_KEY
    - zenml stack set staging
    - python run.py --pipeline training --environment staging
  only:
    - merge_requests

promote_production:
  stage: promote
  script:
    - python scripts/promote_model.py --from-stage staging --to-stage production
  when: manual
  only:
    - tags
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    stages {
        stage('Train') {
            when { branch 'staging' }
            steps {
                sh 'zenml stack set staging'
                sh 'python run.py --pipeline training'
            }
        }
        stage('Promote') {
            when { tag 'v*' }
            steps {
                input message: 'Approve production promotion?'
                sh 'python scripts/promote_model.py --from-stage staging --to-stage production'
            }
        }
    }
}
```

## Monitoring and Alerts

### Pipeline Monitoring

```bash
# List runs
zenml pipeline runs list --pipeline=training_pipeline

# View logs
zenml pipeline runs logs <run-name>

# Describe run
zenml pipeline runs describe <run-name>
```

### Model Performance

Track metrics in monitoring hook:
```python
def send_metrics():
    client = Client()
    model = client.get_model("breast_cancer_classifier")
    prod = model.get_version(ModelStages.PRODUCTION)

    prometheus.gauge("model_accuracy", prod.run_metadata["accuracy"])
```

### Data Drift Detection

```python
@step
def detect_drift(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    from evidently import Report
    from evidently.metric_preset import DataDriftPreset

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)

    if report.as_dict()["drift_score"] > 0.3:
        send_alert("Data drift detected!")

    return {"drift_score": report.as_dict()["drift_score"]}
```

## Incident Response

### Model Performance Degradation

1. Check monitoring dashboard
2. Run data drift detection
3. If critical, rollback:
   ```bash
   python scripts/rollback_model.py --model breast_cancer_classifier
   ```
4. Investigate root cause
5. Retrain if needed

### Pipeline Failures

1. Check logs: `zenml pipeline runs logs <run-name>`
2. Identify failing step
3. Check infrastructure (credentials, connectivity)
4. Revert PR if code issue

### Incident Template

```
**INCIDENT**
Severity: [Critical/High/Medium]
Component: [Model/Pipeline/Infrastructure]
Status: [Investigating/Identified/Resolved]

Description: [What happened]
Impact: [What's affected]
Actions: [What we're doing]
```

## Maintenance

### Regular Tasks

**Daily:**
- Review failed runs
- Check monitoring dashboards

**Weekly:**
- Review model metrics
- Check data drift reports
- Analyze costs

**Monthly:**
- Rotate secrets
- Update Docker images
- Clean up old artifacts

### Cleanup

```bash
# Clean old runs
zenml pipeline runs delete --keep-last=100

# Archive old models
python scripts/promote_model.py \
    --model breast_cancer_classifier \
    --version <old-version> \
    --to-stage archived
```

### Upgrading ZenML

```bash
pip install --upgrade zenml[server]
zenml migrate
zenml stack list  # Verify stacks work
```

## Access Control

| Role | Permissions | Environments |
|------|-------------|--------------|
| Data Scientist | Read/write staging | Dev, Staging |
| ML Engineer | Read/write staging | Dev, Staging |
| Platform Engineer | Admin | All |

```bash
# Add user (Pro)
zenml user create scientist@company.com --role=developer

# Grant stack access
zenml stack share staging --user=scientist@company.com
```

---

**On-Call**: mlops-team@company.com | Slack: #mlops-oncall
