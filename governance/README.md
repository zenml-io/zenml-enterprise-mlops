# Platform Governance Components

This folder contains **shared components** maintained by the platform team that enforce governance policies across all ML pipelines.

## Overview

The platform team provides:
- **Hooks** - Automatic alerts and compliance logging
- **Steps** - Shared validation and quality gates
- **Materializers** - Enhanced artifact handling with metadata tracking
- **Docker** - Base images with curated dependencies
- **Stacks** - Infrastructure as Code (Terraform)

Data science teams import and use these components without needing to understand the implementation.

## Folder Structure

```
governance/
├── hooks/              # Automatic enforcement
│   ├── alerting_hook.py        # Slack/alerter notifications
│   ├── compliance_hook.py      # Audit trail on failures
│   └── monitoring_hook.py      # Metrics logging
│
├── steps/              # Shared validation
│   ├── validate_data_quality.py
│   └── validate_model_performance.py
│
├── materializers/      # Enhanced artifact handling
│   └── dataframe_materializer.py
│
├── docker/             # Container configuration
│   ├── docker_settings.py      # Pre-configured DockerSettings
│   ├── Dockerfile.base         # Platform base image
│   └── README.md               # Docker usage guide
│
└── stacks/             # Infrastructure
    └── terraform/              # IaC configurations
```

## Stack Components vs Hooks

Understanding when to use stack components vs hooks:

| Concern | Solution | Configuration |
|---------|----------|---------------|
| Experiment tracking (MLflow) | **Stack component** | `zenml stack update --experiment_tracker mlflow` |
| Slack notifications | **Stack component + Hook** | Alerter in stack, hooks call it |
| Compliance logging | **Hook** | `on_failure=compliance_failure_hook` |
| Data validation | **Step** | `validate_data_quality(data)` |

**Key insight**: MLflow tracking is automatic via the experiment tracker stack component - no hook needed!

## Usage Patterns

### Hooks (Automatic Notifications)

Hooks send Slack notifications and log compliance events:

```python
from zenml import pipeline
from governance.hooks import pipeline_success_hook, pipeline_failure_hook

@pipeline(
    on_success=pipeline_success_hook,    # Slack notification on completion
    on_failure=pipeline_failure_hook,    # Slack alert + compliance log
)
def training_pipeline():
    # Clean ML code - no alerting mixed in
    data = load_data()
    model = train_model(data)
    return model
```

#### Available Hooks

| Hook | When it runs | What it does |
|------|--------------|--------------|
| `alerter_success_hook` | Step succeeds | Sends Slack message |
| `alerter_failure_hook` | Step fails | Sends Slack alert with error |
| `pipeline_success_hook` | Pipeline completes | Sends completion notification |
| `pipeline_failure_hook` | Pipeline fails | Sends alert + logs for compliance |
| `compliance_failure_hook` | Pipeline fails | Logs to audit system |

### Stack Component: Experiment Tracking (MLflow)

MLflow experiment tracking is configured via stack components - no code needed:

```bash
# Register MLflow tracker
zenml experiment-tracker register mlflow_tracker \
    --flavor=mlflow \
    --tracking_uri=<your-mlflow-uri>

# Add to stack
zenml stack update my_stack --experiment_tracker mlflow_tracker
```

Now MLflow logs automatically for any pipeline using that stack!

### Stack Component: Slack Alerter

```bash
# Register Slack alerter
zenml alerter register slack_alerter \
    --flavor=slack \
    --slack_token=<bot-token> \
    --default_slack_channel_id=<channel-id>

# Add to stack
zenml stack update my_stack --alerter slack_alerter
```

The alerting hooks will automatically use the configured alerter.

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

### Docker Settings (Container Configuration)

Platform-managed Docker settings ensure consistent environments:

```python
from zenml import pipeline, step
from governance.docker import STANDARD_DOCKER_SETTINGS, GPU_DOCKER_SETTINGS

# Apply to entire pipeline
@pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
def training_pipeline():
    data = load_data()
    model = train_model(data)
    return model

# Or per-step for specialized needs
@step(settings={"docker": GPU_DOCKER_SETTINGS})
def train_with_gpu(data):
    import torch
    # GPU training code
    ...
```

Available configurations:
- `STANDARD_DOCKER_SETTINGS` - Python 3.11, MLflow, sklearn
- `GPU_DOCKER_SETTINGS` - PyTorch with CUDA 11.8
- `LIGHTWEIGHT_DOCKER_SETTINGS` - Minimal for preprocessing

See [Docker README](docker/README.md) for full documentation.

## For Platform Engineers

### Setting Up the Stack

Recommended production stack:

```bash
# Create stack with all governance components
zenml stack register production_stack \
    --orchestrator kubernetes \
    --artifact_store gcs \
    --experiment_tracker mlflow \
    --alerter slack \
    --container_registry gcr
```

### Adding New Hooks

1. Create hook in `governance/hooks/`
2. Use the alerter from the stack (don't hardcode Slack)
3. Test thoroughly
4. Export from `__init__.py`
5. Document in this README

### Adding New Validation Steps

1. Create step in `governance/steps/`
2. Add clear error messages
3. Make thresholds configurable
4. Document usage examples

## For Data Scientists

### Importing Shared Components

```python
# Alerting hooks
from governance.hooks import pipeline_success_hook, pipeline_failure_hook

# Validation steps
from governance.steps import validate_data_quality, validate_model_performance

# Docker settings
from governance.docker import STANDARD_DOCKER_SETTINGS
```

### When to Use What

| Component | When to Use | Example |
|-----------|-------------|---------|
| Alerting Hooks | Pipeline notifications | Slack alerts on success/failure |
| Validation Steps | Data/model quality gates | Check missing values, accuracy |
| Docker Settings | Containerized execution | Consistent environments |

### What's Automatic (No Code Needed)

- **MLflow tracking** - Just use a stack with experiment_tracker
- **Artifact storage** - Configured via artifact_store in stack
- **Container builds** - Docker settings handle this

## Versioning

Shared components follow semantic versioning:
- **Major**: Breaking changes (requires code updates)
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

Current versions:
- Hooks: `v2.0.0` (alerting-based)
- Validation Steps: `v1.0.0`
- Docker Settings: `v1.0.0`

## Support

Questions about shared components?
- **Slack**: #mlops-platform
- **Email**: platform-team@company.com
- **Docs**: See [Platform Guide](../docs/PLATFORM_GUIDE.md)
