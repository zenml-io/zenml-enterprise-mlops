# Notebooks

Interactive demonstrations of ZenML Enterprise MLOps patterns.

## Available Notebooks

### 1. lineage_demo.ipynb

**Purpose**: Demonstrate complete model lineage and audit trails for compliance.

**What it shows**:
- Trace production predictions back to training data and code
- View model promotion history
- Access all model metadata programmatically
- Build automated compliance reports

**Use case**: HIPAA/GDPR compliance, regulatory submissions, incident investigation

**Run**:
```bash
jupyter notebook notebooks/lineage_demo.ipynb
```

### 2. promotion_rollback_demo.ipynb

**Purpose**: Demonstrate model promotion and rollback workflows.

**What it shows**:
- Promote models across stages (none → staging → production)
- Validate promotion criteria (performance thresholds)
- Rollback to previous versions safely
- Track promotion history and approvers

**Use case**: Safe production deployments, rollback procedures, change management

**Run**:
```bash
jupyter notebook notebooks/promotion_rollback_demo.ipynb
```

## Prerequisites

Install Jupyter:
```bash
pip install jupyter
# or
uv pip install jupyter
```

Ensure ZenML is connected:
```bash
zenml login  # Connect to your ZenML server
zenml stack list  # Verify stack is configured
```

## Best Practices

- **Clear outputs before committing**: `jupyter nbconvert --clear-output notebooks/*.ipynb`
- **Run in order**: lineage_demo → promotion_rollback_demo
- **Use staging data**: Don't run against production models during demos
- **Document changes**: Add markdown cells explaining each step

## Integration with CI/CD

These notebooks can be automated for:
- **Scheduled compliance reports** - Run lineage_demo weekly, export to PDF
- **Pre-deployment checks** - Validate promotion criteria before releases
- **Audit trail generation** - Automated compliance documentation
- **Model validation** - Programmatic checks before production promotion

Example GitHub Action:
```yaml
- name: Generate Compliance Report
  run: |
    jupyter nbconvert --execute --to pdf notebooks/lineage_demo.ipynb
    # Upload PDF to compliance system
```
