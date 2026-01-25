# Platform Governance Components

This folder contains **shared components** maintained by the platform team that enforce governance policies across all ML pipelines.

## Overview

The platform team provides:
- **Hooks** - Automatic enforcement of governance policies
- **Steps** - Shared validation and quality gates
- **Materializers** - Enhanced artifact handling with metadata tracking
- **Docker** - Base images with curated dependencies
- **Stacks** - Infrastructure as Code (Terraform)

Data science teams import and use these components without needing to understand the implementation.

## Folder Structure

```
governance/
├── hooks/              # Automatic enforcement
│   ├── mlflow_hook.py          # MLflow auto-logging
│   └── compliance_hook.py      # Audit trail on failures
│
├── steps/              # Shared validation
│   ├── validate_data_quality.py
│   └── validate_model_performance.py
│
├── materializers/      # Enhanced artifact handling
│   └── dataframe_materializer.py
│
└── stacks/             # Infrastructure
    └── terraform/              # IaC configurations
```

## Usage Patterns

### Hooks (Automatic Governance)

Hooks run automatically without data scientists needing to call them:

```python
from zenml import pipeline
from governance.hooks import mlflow_success_hook, compliance_failure_hook

@pipeline(
    on_success=mlflow_success_hook,      # Runs automatically on success
    on_failure=compliance_failure_hook,  # Runs automatically on failure
)
def training_pipeline():
    # Clean ML code - no governance mixed in
    data = load_data()
    model = train_model(data)
    return model
```

### Shared Validation Steps

Platform team provides validation steps that enforce quality gates:

```python
from zenml import pipeline
from governance.steps import validate_data_quality, validate_model_performance

@pipeline
def training_pipeline():
    data = load_data()

    # Platform governance: automatic data quality checks
    data = validate_data_quality(data, min_rows=100)

    model = train_model(data)
    metrics = evaluate_model(model)

    # Platform governance: automatic model quality checks
    validate_model_performance(
        metrics,
        min_accuracy=0.7,
        min_precision=0.7,
        min_recall=0.7,
    )

    return model
```

### Shared Materializers

Enhanced materializers track additional metadata:

```python
from governance.materializers import EnhancedDataFrameMaterializer
from zenml import step

@step(output_materializers=EnhancedDataFrameMaterializer)
def load_data() -> pd.DataFrame:
    """Data automatically tracked with enhanced metadata"""
    return pd.read_csv("data.csv")
```

## For Platform Engineers

### Adding New Hooks

1. Create hook in `governance/hooks/`
2. Test thoroughly
3. Document in this README
4. Announce to teams via Slack/email

### Adding New Validation Steps

1. Create step in `governance/steps/`
2. Add clear error messages
3. Make thresholds configurable
4. Document usage examples

### Updating Base Images

1. Modify `governance/docker/Dockerfile.base`
2. Test with representative pipelines
3. Version the image (e.g., `v1.2.3`)
4. Announce breaking changes

## For Data Scientists

### Importing Shared Components

```python
# Hooks
from governance.hooks import mlflow_success_hook, compliance_failure_hook

# Validation steps
from governance.steps import validate_data_quality, validate_model_performance

# Materializers
from governance.materializers import EnhancedDataFrameMaterializer
```

### When to Use What

| Component | When to Use | Example |
|-----------|-------------|---------|
| Hooks | Always (automatic) | MLflow logging, compliance |
| Validation Steps | Data quality gates | Check missing values, schema |
| Materializers | Enhanced metadata | Track DataFrame statistics |

## Versioning

Shared components follow semantic versioning:
- **Major**: Breaking changes (requires code updates)
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

Current versions:
- Hooks: `v1.0.0`
- Validation Steps: `v1.0.0`
- Materializers: `v1.0.0`

## Contributing

Platform team members:
1. Create feature branch
2. Add tests
3. Update this README
4. Create PR to `develop`
5. Get review from platform lead
6. Merge and announce

## Support

Questions about shared components?
- **Slack**: #mlops-platform
- **Email**: platform-team@company.com
- **Docs**: See [Platform Guide](../docs/PLATFORM_GUIDE.md)
