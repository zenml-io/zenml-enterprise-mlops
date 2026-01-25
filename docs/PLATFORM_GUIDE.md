# Platform Guide

This guide is for platform engineers and MLOps teams responsible for maintaining the MLOps infrastructure, managing deployments, and ensuring production reliability.

## Table of Contents

- [Overview](#overview)
- [Infrastructure Management](#infrastructure-management)
- [Governance Implementation](#governance-implementation)
- [Production Deployments](#production-deployments)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Incident Response](#incident-response)
- [Maintenance](#maintenance)

## Overview

As the platform team, you are responsible for:
- Managing ZenML stacks across all environments
- Implementing and maintaining governance hooks
- Approving and executing production deployments
- Monitoring model performance and infrastructure health
- Responding to incidents and performing rollbacks
- Managing secrets, credentials, and access control

## Infrastructure Management

### Stack Management

#### Setting Up Stacks

Each environment (local, staging, production) has its own stack configuration.

**Local Stack** (for developers):
```bash
# Use the setup script
./scripts/setup_stacks.sh

# Or manually:
zenml orchestrator register local-orchestrator --flavor=local
zenml artifact-store register local-artifact-store --flavor=local
zenml stack register local-dev -o local-orchestrator -a local-artifact-store
```

**Staging Stack** (for CI/CD):
```bash
# Register GCP components (example)
zenml orchestrator register vertex-staging \
    --flavor=vertex \
    --project=your-project-staging \
    --location=us-central1

zenml artifact-store register gcs-staging \
    --flavor=gcp \
    --path=gs://your-bucket-staging/artifacts

zenml container-registry register gcr-staging \
    --flavor=gcp \
    --uri=gcr.io/your-project-staging/zenml

zenml experiment-tracker register mlflow-staging \
    --flavor=mlflow \
    --tracking_uri=https://mlflow-staging.company.com

# Create staging stack
zenml stack register staging \
    -o vertex-staging \
    -a gcs-staging \
    -c gcr-staging \
    -e mlflow-staging
```

**Production Stack** (restricted access):
```bash
# Similar to staging but with production credentials
# Requires elevated permissions

zenml orchestrator register vertex-production \
    --flavor=vertex \
    --project=your-project-production \
    --location=us-central1

# ... (similar to staging with production resources)

zenml stack register production \
    -o vertex-production \
    -a gcs-production \
    -c gcr-production \
    -e mlflow-production
```

#### Stack Verification

```bash
# List all stacks
zenml stack list

# Describe stack configuration
zenml stack describe staging

# Validate stack is properly configured
zenml stack up staging

# Set active stack
zenml stack set staging
```

### Secrets Management

#### Creating Secrets

```bash
# GCP service account
zenml secret create gcp-staging-credentials \
    --token=@/path/to/service-account-staging.json

zenml secret create gcp-production-credentials \
    --token=@/path/to/service-account-production.json

# MLflow credentials
zenml secret create mlflow-staging-credentials \
    --username=zenml \
    --password=<password>

# Slack webhook for alerts
zenml secret create slack-production-webhook \
    --webhook_url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Secret Rotation

Rotate secrets regularly for security:

```bash
# Update existing secret
zenml secret update gcp-production-credentials \
    --token=@/path/to/new-service-account.json

# Verify pipelines still work after rotation
python run.py --pipeline training
```

### Docker Image Management

#### Building Base Images

```bash
# Build platform base image
./scripts/build_docker_image.sh

# Build for specific environment
IMAGE_NAME=zenml-enterprise-staging \
IMAGE_TAG=v1.0.0 \
./scripts/build_docker_image.sh

# Push to registry
PUSH_TO_REGISTRY=true \
IMAGE_NAME=gcr.io/your-project/zenml-enterprise \
./scripts/build_docker_image.sh
```

#### Image Security Scanning

```bash
# Scan with Trivy
trivy image zenml-enterprise-base:latest

# Scan with GCP Container Analysis
gcloud container images describe gcr.io/your-project/zenml:latest \
    --show-package-vulnerability

# Fail builds on critical vulnerabilities
trivy image --severity CRITICAL --exit-code 1 zenml-enterprise-base:latest
```

## Governance Implementation

### Platform Hooks

Hooks enforce governance automatically without developer code changes.

#### MLflow Logging Hook

Located in `governance/hooks/mlflow_hook.py`:

```python
def mlflow_success_hook() -> None:
    """Automatically log step metadata to MLflow"""
    context = get_step_context()
    # Log metadata, metrics, artifacts
```

**Usage**: Applied via `@pipeline(on_success=mlflow_success_hook)`

**Maintenance**:
- Update hook to log additional metadata
- Add error handling for MLflow connection issues
- Customize based on pipeline type

#### Compliance Hook

Located in `governance/hooks/compliance_hook.py`:

```python
def compliance_failure_hook() -> None:
    """Log failures for audit trail"""
    context = get_step_context()
    # Send alerts, log to compliance system
```

**Usage**: Applied via `@pipeline(on_failure=compliance_failure_hook)`

**Maintenance**:
- Configure alert destinations (Slack, PagerDuty, etc.)
- Adjust alert severity based on environment
- Add incident tracking integration

#### Creating New Hooks

```python
# governance/hooks/custom_hook.py
from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)

def custom_monitoring_hook() -> None:
    """Send metrics to monitoring system"""
    try:
        context = get_step_context()

        # Extract metrics
        metrics = {
            "pipeline": context.pipeline_run.name,
            "step": context.step_run.name,
            "duration": context.step_run.duration,
            "status": context.step_run.status,
        }

        # Send to monitoring system
        send_to_prometheus(metrics)

        logger.info(f"Monitoring metrics sent for {context.step_run.name}")

    except Exception as e:
        logger.warning(f"Monitoring hook failed: {e}")
        # Never fail the pipeline due to monitoring issues
```

### Shared Validation Steps

Platform team provides validation steps that developers must use.

#### Data Validation

Located in `governance/steps/data_validation.py`:

```python
@step
def validate_data_quality(
    dataset: pd.DataFrame,
    min_rows: int = 100,
    max_missing_fraction: float = 0.1,
) -> pd.DataFrame:
    """Enforce data quality standards"""
    # Platform-defined validation logic
```

**Configuration**: Adjust thresholds in step parameters or via config files

#### Model Validation

Located in `governance/steps/model_validation.py`:

```python
@step
def validate_model_performance(
    metrics: dict,
    min_accuracy: float = 0.8,
    min_precision: float = 0.8,
    min_recall: float = 0.8,
    min_f1: float = 0.8,
) -> None:
    """Enforce model performance thresholds"""
    # Fail pipeline if model doesn't meet requirements
```

**Configuration**: Set environment-specific thresholds in `configs/`

## Production Deployments

### Model Promotion Workflow

#### 1. Validation in Staging

Before promoting to production, verify in staging:

```bash
# Check latest staging model
zenml model describe patient_readmission_predictor

# Verify metrics meet production thresholds
zenml model version describe patient_readmission_predictor --version=<version>

# Test batch inference in staging
python run.py --pipeline batch_inference
```

#### 2. Manual Promotion (Script)

```bash
# Promote specific version to production
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --version 5 \
    --to-stage production

# Promote latest staging to production
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --from-stage staging \
    --to-stage production

# Force promotion (demote current production)
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --from-stage staging \
    --to-stage production \
    --force
```

#### 3. GitHub Release-Based Promotion

**Recommended for production**:

1. Validate model in staging
2. Create GitHub release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. Create release in GitHub UI with description
4. GitHub Actions automatically:
   - Validates model meets production thresholds
   - Promotes to production
   - Creates deployment snapshot
   - Notifies team

#### 4. Verification

After promotion, verify:

```bash
# Check production model
zenml model version describe patient_readmission_predictor \
    --version=ModelStages.PRODUCTION

# Verify batch inference uses new model
python run.py --pipeline batch_inference

# Monitor predictions in dashboard
zenml login
```

### Rollback Procedures

#### Quick Rollback

```bash
# Revert to previous production version
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --version <previous-version> \
    --to-stage production \
    --force
```

#### Using Pipeline Snapshots (ZenML Pro)

```bash
# List available snapshots
zenml pipeline-snapshot list

# Trigger previous snapshot
zenml pipeline run \
    --snapshot-name=PROD_model_abc1234
```

### Deployment Checklist

Before promoting to production:

- [ ] Model meets performance thresholds (accuracy, precision, recall)
- [ ] Batch inference tested in staging
- [ ] Data drift checks passed
- [ ] Security scan completed
- [ ] Approval from stakeholders
- [ ] Rollback plan documented
- [ ] Team notified of deployment window
- [ ] Monitoring alerts configured

## Monitoring and Alerts

### Pipeline Monitoring

#### View Pipeline Runs

```bash
# List recent runs
zenml pipeline runs list --pipeline=training_pipeline

# Show run details
zenml pipeline runs describe <run-name>

# View logs
zenml pipeline runs logs <run-name>
```

#### Set Up Alerts

Configure alerts in `configs/deployment_config.yaml`:

```yaml
monitoring:
  alerts:
    - name: model_accuracy_degradation
      threshold: 0.75
      severity: critical
      channels: [slack, email, pagerduty]

    - name: high_prediction_latency
      threshold: 1000  # milliseconds
      severity: warning
      channels: [slack]
```

### Model Performance Monitoring

#### Track Metrics

```python
# In monitoring hook
def send_metrics_to_monitoring():
    """Send metrics to Prometheus/Datadog/etc."""
    from zenml.client import Client

    client = Client()
    model = client.get_model("patient_readmission_predictor")
    production_version = model.get_version(ModelStages.PRODUCTION)

    metrics = production_version.run_metadata

    # Send to monitoring system
    prometheus.send_gauge("model_accuracy", metrics["accuracy"])
    prometheus.send_gauge("model_f1_score", metrics["f1"])
```

#### Data Drift Detection

Configured in batch inference pipeline:

```python
from evidently.metric_preset import DataDriftPreset

@step
def detect_drift(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
) -> dict:
    """Detect data drift using Evidently"""
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference_data, current_data=current_data)

    drift_score = report.as_dict()["drift_score"]

    if drift_score > 0.3:
        send_alert("Data drift detected!", severity="warning")

    return {"drift_score": drift_score}
```

### Infrastructure Monitoring

Monitor ZenML server and stack components:

```bash
# Check ZenML server status
zenml status

# Check stack component health
zenml stack up production

# View system logs
kubectl logs -n zenml -l app=zenml-server  # For K8s deployment
```

## Incident Response

### Response Procedures

#### 1. Model Performance Degradation

**Symptoms**: Accuracy drops below threshold, increased errors

**Response**:
1. Check monitoring dashboard for anomalies
2. Verify data quality hasn't changed
3. Run data drift detection
4. If drift detected, consider retraining
5. If critical, rollback to previous version:
   ```bash
   python scripts/promote_model.py \
       --model patient_readmission_predictor \
       --version <previous-version> \
       --to-stage production --force
   ```

#### 2. Pipeline Failures

**Symptoms**: Pipeline runs fail, CI/CD broken

**Response**:
1. Check pipeline logs:
   ```bash
   zenml pipeline runs logs <run-name>
   ```
2. Identify failing step
3. Check infrastructure (stack components, credentials)
4. Verify data sources are accessible
5. If infrastructure issue, switch to backup stack
6. If code issue, revert PR

#### 3. Infrastructure Outages

**Symptoms**: Cannot connect to artifact store, MLflow, etc.

**Response**:
1. Check cloud provider status pages
2. Verify credentials haven't expired
3. Check VPC/networking configuration
4. Switch to backup region/resources if available
5. Communicate outage to data science team

### Incident Communication

Use this template for incidents:

```
**INCIDENT ALERT**

Severity: [Critical/High/Medium/Low]
Component: [Model/Pipeline/Infrastructure]
Status: [Investigating/Identified/Monitoring/Resolved]

Description: [Brief description of the issue]

Impact: [What is affected and how]

Actions Taken:
1. [Action 1]
2. [Action 2]

Next Steps:
- [Next step 1]
- [Next step 2]

Updated: [Timestamp]
Point of Contact: @platform-team
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Review failed pipeline runs
- [ ] Check monitoring dashboards
- [ ] Verify batch inference completed

#### Weekly
- [ ] Review model performance metrics
- [ ] Check data drift reports
- [ ] Analyze resource usage and costs
- [ ] Review access logs for anomalies

#### Monthly
- [ ] Rotate secrets and credentials
- [ ] Update base Docker images
- [ ] Review and update governance policies
- [ ] Clean up old artifacts and models
- [ ] Update documentation

#### Quarterly
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Capacity planning review
- [ ] Team training on new features

### Cleanup Operations

```bash
# Clean up old pipeline runs (keep last 100)
zenml pipeline runs delete --keep-last=100

# Archive old models
python scripts/archive_old_models.py --older-than=90days

# Clean up artifact store
# (Be careful - verify artifacts aren't referenced!)
gsutil -m rm -r gs://your-bucket/artifacts/old/**
```

### Upgrading ZenML

```bash
# Check current version
zenml version

# Upgrade to latest version
pip install --upgrade zenml[server]

# Run database migrations
zenml migrate

# Verify stacks still work
zenml stack list
zenml stack up production
```

## Access Control

### Role Definitions

| Role | Permissions | Environments |
|------|-------------|--------------|
| **Data Scientist** | Read/write to staging, read from production | Dev, Staging |
| **ML Engineer** | Read/write to staging, read from production | Dev, Staging |
| **Platform Engineer** | Admin access to all environments | All |
| **MLOps Engineer** | Read/write with approval to production | All |

### Managing Access

```bash
# Add user to ZenML (Pro)
zenml user create scientist@company.com --role=developer

# Grant stack permissions
zenml stack share staging --user=scientist@company.com

# Revoke access
zenml stack unshare staging --user=scientist@company.com
```

## Disaster Recovery

### Backup Procedures

```bash
# Backup ZenML database
zenml backup create --output=/backups/zenml-backup.sql

# Backup artifact store
gsutil -m cp -r gs://your-bucket/artifacts /backups/artifacts/

# Backup secrets
zenml secret export --output=/backups/secrets.yaml
```

### Recovery Procedures

```bash
# Restore ZenML database
zenml restore --input=/backups/zenml-backup.sql

# Restore artifact store
gsutil -m cp -r /backups/artifacts/ gs://your-bucket/artifacts/

# Restore secrets
zenml secret import --input=/backups/secrets.yaml
```

## Resources

- [ZenML Pro Documentation](https://docs.zenml.io/platform-guide)
- [Stack Component Guide](https://docs.zenml.io/stacks-and-components)
- [Production Best Practices](https://docs.zenml.io/user-guide/production-guide)
- Internal Runbooks: `/docs/runbooks/` (create these for your team)

---

**On-Call Contacts**:
- Platform Team: mlops-team@company.com
- Slack: #mlops-oncall
- PagerDuty: MLOps Escalation Policy
