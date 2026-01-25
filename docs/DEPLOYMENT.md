# Deployment Guide

This guide covers deployment procedures for moving ML models from development to production using this enterprise MLOps template.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Environment Setup](#environment-setup)
- [GitOps Workflows](#gitops-workflows)
- [Manual Deployment](#manual-deployment)
- [CI/CD Integration](#cicd-integration)
- [Verification and Testing](#verification-and-testing)
- [Troubleshooting](#troubleshooting)

## Deployment Overview

### Deployment Strategy

This template uses a **multi-environment promotion** strategy:

```
Development → Staging → Production
   (local)      (CI/CD)    (manual approval)
```

### Key Principles

1. **Immutability**: Production deployments use pipeline snapshots (ZenML Pro)
2. **GitOps**: All promotions triggered by Git events (PR merges, releases)
3. **Approval Gates**: Production requires manual approval
4. **Rollback Capability**: Can revert to previous versions instantly
5. **Complete Audit**: Every deployment is logged and traceable

### Deployment Artifacts

Each deployment involves:
- **Model artifacts**: Trained model, scaler, preprocessor
- **Pipeline definition**: Immutable snapshot (Pro) or code commit
- **Metadata**: Metrics, hyperparameters, lineage
- **Configuration**: Environment-specific settings

## Environment Setup

### Prerequisites

Before deploying to any environment, ensure:

1. **ZenML Stack Configured**:
   ```bash
   zenml stack describe <environment>
   ```

2. **Secrets Registered**:
   ```bash
   zenml secret list
   ```

3. **Permissions Granted**:
   - Staging: Automatic (via CI/CD service account)
   - Production: Manual approval required

4. **Infrastructure Ready**:
   - Artifact store accessible
   - Container registry available
   - Orchestrator running
   - MLflow server reachable

### Environment-Specific Configuration

Each environment has its own configuration in `configs/`:

- `configs/staging.yaml`: Staging settings
- `configs/production.yaml`: Production settings
- `configs/model_config.yaml`: Model hyperparameters
- `configs/deployment_config.yaml`: Deployment settings

## GitOps Workflows

### 1. Development Workflow

**Trigger**: Local development and testing

```bash
# 1. Developer creates feature branch
git checkout -b feature/improve-model

# 2. Develop and test locally
python run.py --pipeline training

# 3. Verify results
zenml login  # Check dashboard

# 4. Commit and push
git add src/
git commit -m "Improve model feature engineering"
git push origin feature/improve-model
```

No automated deployment - purely local testing.

### 2. Staging Workflow

**Trigger**: Pull request to `staging` or `main` branch

**Workflow File**: `.github/workflows/train-staging.yml`

#### Automatic Process

1. **PR Created**: Developer creates PR to staging/main
2. **CI Triggered**: GitHub Actions starts automatically
3. **Build Snapshot** (Pro):
   ```yaml
   - name: Build and run snapshot (Pro)
     run: |
       python scripts/build_snapshot.py \
         --environment staging \
         --stack $ZENML_STAGING_STACK \
         --run
   ```
4. **Run Training**: Pipeline executes in staging environment
5. **Validate Results**: Model must meet staging thresholds
6. **Comment on PR**: Results posted as PR comment

#### Manual Process

If you need to manually trigger staging deployment:

```bash
# Set environment variables
export ZENML_STORE_URL=<your-zenml-server>
export ZENML_STORE_API_KEY=<your-api-key>
export ZENML_PROJECT=default
export ZENML_STAGING_STACK=staging

# Connect to ZenML
zenml connect --url $ZENML_STORE_URL --api-key $ZENML_STORE_API_KEY

# Set staging stack
zenml stack set $ZENML_STAGING_STACK

# Run training (Pro with snapshot)
python scripts/build_snapshot.py \
    --environment staging \
    --stack $ZENML_STAGING_STACK \
    --run

# Or run directly (OSS)
python run.py --pipeline training
```

### 3. Production Workflow

**Trigger**: GitHub release created

**Workflow File**: `.github/workflows/promote-production.yml`

#### Automatic Process

1. **Create Release**: Platform team creates GitHub release
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # Create release in GitHub UI
   ```

2. **Build Snapshot** (Pro):
   - Creates immutable pipeline definition
   - Does NOT run automatically (manual trigger)

3. **Promote Model**:
   - Validates model meets production thresholds
   - Changes stage from "staging" to "production"
   - Notifies team

4. **Verification**:
   - Batch inference picks up new production model
   - Monitoring alerts activated

#### Step-by-Step Production Deployment

**Phase 1: Pre-Deployment** (1-2 days before)

1. Verify staging model performance:
   ```bash
   zenml model version describe patient_readmission_predictor \
       --version=<version>
   ```

2. Review metrics against production thresholds:
   - Accuracy >= 0.80
   - Precision >= 0.80
   - Recall >= 0.80
   - F1 >= 0.80

3. Run additional validation:
   ```bash
   # Test batch inference in staging
   python run.py --pipeline batch_inference

   # Check data drift
   python scripts/check_drift.py --version=<version>
   ```

4. Get stakeholder approval:
   - Email ML stakeholders
   - Share metrics and lineage
   - Document any concerns

**Phase 2: Deployment** (during deployment window)

1. Create GitHub release:
   ```bash
   # Create and push tag
   git tag -a v1.0.0 -m "Production release: improved model accuracy"
   git push origin v1.0.0
   ```

2. Create release in GitHub UI:
   - Navigate to Releases
   - Click "Create a new release"
   - Select tag `v1.0.0`
   - Add release notes (auto-generated or custom)
   - Click "Publish release"

3. Monitor GitHub Actions:
   - Watch workflow execution
   - Check for any failures
   - Review promotion logs

4. Verify promotion:
   ```bash
   # Check production model
   zenml model version describe patient_readmission_predictor \
       --version=ModelStages.PRODUCTION

   # Should show newly promoted version
   ```

**Phase 3: Post-Deployment** (immediately after)

1. Verify batch inference:
   ```bash
   # Check batch inference runs
   zenml pipeline runs list --pipeline=batch_inference_pipeline

   # Verify using production model
   zenml pipeline runs describe <latest-run>
   ```

2. Monitor metrics:
   - Check MLflow for logged predictions
   - Review dashboard for anomalies
   - Set up alerts for performance degradation

3. Document deployment:
   - Update changelog
   - Note deployment time
   - Record deployed version
   - Share with team

## Manual Deployment

### Manual Model Promotion

If you need to promote manually (not via GitHub Actions):

```bash
# 1. Connect to ZenML production
zenml connect --url <production-url> --api-key <production-key>
zenml stack set production

# 2. Promote model to staging first
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --version <version> \
    --to-stage staging

# 3. Validate and promote to production
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --from-stage staging \
    --to-stage production

# 4. Verify
zenml model version describe patient_readmission_predictor \
    --version=ModelStages.PRODUCTION
```

### Manual Pipeline Execution

To manually run pipelines in production:

```bash
# Set production stack
zenml stack set production

# Build snapshot (Pro)
python scripts/build_snapshot.py \
    --environment production \
    --stack production \
    --pipeline training

# Later, trigger the snapshot via UI or API
zenml pipeline run --snapshot-name=PROD_model_abc1234
```

Or direct execution (OSS):

```bash
python run.py --pipeline training
```

## CI/CD Integration

### GitHub Actions Setup

#### Required Secrets

Configure these secrets in GitHub Settings → Secrets and variables → Actions:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `ZENML_STORE_URL` | ZenML server URL | `https://your-zenml-server.com` |
| `ZENML_STORE_API_KEY` | ZenML API key | `ZENML_DEFAULT_...` |
| `ZENML_PROJECT` | ZenML project name | `default` or `ml-platform` |
| `ZENML_STAGING_STACK` | Staging stack name | `staging` |
| `ZENML_PRODUCTION_STACK` | Production stack name | `production` |

#### Environment Protection Rules

Configure environment protection in GitHub Settings → Environments:

**Staging Environment**:
- No required reviewers
- No deployment branches

**Production Environment**:
- Required reviewers: 2
- Deployment branches: Only `main` branch
- Environment secrets: Production credentials

### Workflow Customization

#### Training Workflow

Edit `.github/workflows/train-staging.yml`:

```yaml
# Customize when training runs
on:
  pull_request:
    branches:
      - staging
      - main
    paths:  # Only trigger on relevant changes
      - 'src/**'
      - 'governance/**'
      - 'configs/**'
```

#### Promotion Workflow

Edit `.github/workflows/promote-production.yml`:

```yaml
# Customize promotion strategy
jobs:
  promote-model:
    environment:
      name: production  # Requires approval
    steps:
      - name: Promote to production
        run: |
          python scripts/promote_model.py \
            --model patient_readmission_predictor \
            --from-stage staging \
            --to-stage production
```

### Other CI/CD Platforms

#### GitLab CI

`.gitlab-ci.yml`:

```yaml
stages:
  - train
  - promote

train_staging:
  stage: train
  script:
    - zenml connect --url $ZENML_STORE_URL --api-key $ZENML_STORE_API_KEY
    - zenml stack set staging
    - python scripts/build_snapshot.py --environment staging --stack staging --run
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

#### Jenkins

`Jenkinsfile`:

```groovy
pipeline {
    agent any

    stages {
        stage('Train in Staging') {
            when {
                branch 'staging'
            }
            steps {
                sh 'zenml connect --url $ZENML_STORE_URL --api-key $ZENML_STORE_API_KEY'
                sh 'zenml stack set staging'
                sh 'python scripts/build_snapshot.py --environment staging --stack staging --run'
            }
        }

        stage('Promote to Production') {
            when {
                tag 'v*'
            }
            steps {
                input message: 'Approve promotion to production?'
                sh 'python scripts/promote_model.py --from-stage staging --to-stage production'
            }
        }
    }
}
```

## Verification and Testing

### Pre-Deployment Checks

Before promoting to production:

```bash
# 1. Verify model exists
zenml model version describe patient_readmission_predictor --version=<version>

# 2. Check metrics
zenml model version describe patient_readmission_predictor --version=<version> | grep accuracy

# 3. Test batch inference in staging
zenml stack set staging
python run.py --pipeline batch_inference

# 4. Check for data drift
python scripts/check_drift.py --version=<version>

# 5. Verify pipeline snapshot (Pro)
zenml pipeline-snapshot describe PROD_model_<sha>
```

### Post-Deployment Verification

After deploying to production:

```bash
# 1. Verify production model
zenml model version describe patient_readmission_predictor \
    --version=ModelStages.PRODUCTION

# 2. Check batch inference uses new model
zenml pipeline runs list --pipeline=batch_inference_pipeline | head -5

# 3. Monitor first predictions
# Check MLflow UI or monitoring dashboard

# 4. Verify alerts are configured
# Check alerting system (Slack, PagerDuty, etc.)
```

### Smoke Tests

Run smoke tests after deployment:

```bash
# Test prediction endpoint (if deployed)
curl -X POST https://api.company.com/predict \
    -H "Content-Type: application/json" \
    -d '{"features": [...]}'

# Test batch inference
python scripts/test_batch_inference.py --version=production

# Verify lineage
python scripts/verify_lineage.py --version=production
```

## Troubleshooting

### Common Deployment Issues

#### 1. Promotion Script Fails

**Symptom**:
```
Error: Model version X does not meet production requirements
```

**Solution**:
- Check model metrics meet thresholds
- Review validation logs
- Adjust thresholds if appropriate (requires approval)
- Retrain model if performance insufficient

#### 2. GitHub Actions Failure

**Symptom**: Workflow fails with authentication error

**Solution**:
```bash
# Verify secrets are set
gh secret list

# Update expired credentials
gh secret set ZENML_STORE_API_KEY

# Re-run workflow
gh run rerun <run-id>
```

#### 3. Snapshot Creation Fails

**Symptom**:
```
Error: Pipeline snapshots require ZenML Pro
```

**Solution**:
- Verify ZenML Pro is enabled
- Check server configuration
- Fall back to direct execution (OSS):
  ```bash
  python run.py --pipeline training
  ```

#### 4. Production Model Not Loading

**Symptom**: Batch inference still using old model

**Solution**:
```bash
# Verify promotion completed
zenml model version describe patient_readmission_predictor \
    --version=ModelStages.PRODUCTION

# Check batch inference code
# Should load by stage: Model(name="...", version=ModelStages.PRODUCTION)

# Restart batch inference
python run.py --pipeline batch_inference
```

### Rollback Procedures

#### Quick Rollback

```bash
# Promote previous version to production
python scripts/promote_model.py \
    --model patient_readmission_predictor \
    --version <previous-version> \
    --to-stage production \
    --force
```

#### Rollback via Snapshot

```bash
# List available snapshots
zenml pipeline-snapshot list

# Trigger previous snapshot
zenml pipeline run --snapshot-name=PROD_model_<previous-sha>
```

### Getting Help

1. **Check logs**:
   ```bash
   # GitHub Actions logs
   gh run view <run-id> --log

   # ZenML logs
   zenml pipeline runs logs <run-name>
   ```

2. **Debug mode**:
   ```bash
   export ZENML_DEBUG=true
   python scripts/promote_model.py ...
   ```

3. **Contact platform team**:
   - Slack: #mlops-support
   - Email: mlops-team@company.com
   - PagerDuty: (for production incidents)

## Best Practices

### Do's ✅

- Always test in staging before production
- Create detailed release notes
- Monitor deployments for at least 24 hours
- Document any issues or anomalies
- Follow the deployment checklist
- Get required approvals
- Schedule deployments during low-traffic periods

### Don'ts ❌

- Never deploy directly to production
- Don't skip staging validation
- Don't promote without metrics review
- Don't deploy without rollback plan
- Don't ignore monitoring alerts
- Don't bypass approval process

## Deployment Checklist

Use this checklist for production deployments:

- [ ] Model trained and validated in staging
- [ ] Metrics meet or exceed production thresholds
- [ ] Batch inference tested in staging
- [ ] Data drift check passed
- [ ] Stakeholder approval obtained
- [ ] Release notes prepared
- [ ] Rollback plan documented
- [ ] Team notified of deployment
- [ ] Monitoring dashboard ready
- [ ] Off-hours contact established
- [ ] GitHub release created
- [ ] GitHub Actions completed successfully
- [ ] Production model verified
- [ ] Batch inference tested
- [ ] Monitoring alerts confirmed
- [ ] Deployment documented

---

**Questions?** Contact the platform team at mlops-team@company.com or Slack #mlops-support.
