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
| Slack notifications | **Stack component + Hook** | Alerter in stack, hooks call it |
| Compliance logging | **Hook** | `on_failure=compliance_failure_hook` |
| Data validation | **Step** | `validate_data_quality(data)` |

## Usage Patterns

### Hooks (Automatic Notifications)

Hooks are applied **dynamically based on environment** - not hardcoded in pipeline decorators.

**Local development**: No hooks (fast iteration, no Slack spam)
**Staging/Production**: Full governance hooks (alerts, validation, monitoring)

Hooks are applied in `run.py`:

```python
# run.py applies hooks based on environment
if environment == "local":
    # No hooks - clean and fast
    training_pipeline(**kwargs)
else:
    # Staging/production - apply governance hooks
    from governance.hooks import (
        model_governance_hook,
        pipeline_success_hook,
        pipeline_failure_hook,
    )

    # Combine multiple success hooks (ZenML expects single callable)
    def combined_success_hook():
        pipeline_success_hook()
        model_governance_hook()

    training_pipeline.with_options(
        on_success=combined_success_hook,
        on_failure=pipeline_failure_hook,
    )(**kwargs)
```

This keeps pipeline code clean while enabling environment-specific governance.

#### Available Hooks

| Hook | When it runs | What it does |
|------|--------------|--------------|
| `alerter_success_hook` | Step succeeds | Sends Slack notification |
| `alerter_failure_hook` | Step fails | Sends Slack alert with error details |
| `pipeline_success_hook` | Pipeline completes | Sends completion notification |
| `pipeline_failure_hook` | Pipeline fails | Sends critical failure alert |
| `model_governance_hook` | Model training succeeds | Enforces required tags and naming conventions |
| `monitoring_success_hook` | Step succeeds | Sends metrics to external systems (Datadog, Prometheus) |


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

#### Hook Enforcement

Hooks enforce governance policies automatically:

- `model_governance_hook` - Validates required tags and naming conventions
- `pipeline_success_hook` - Sends Slack notification on completion
- `pipeline_failure_hook` - Sends alert on failure

Models must have required tags:
```python
@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        tags=["use_case:breast_cancer", "owner_team:ml-platform"]  # Required!
    ),
)
```

The `model_governance_hook` enforces these requirements in staging/production.

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
- `STANDARD_DOCKER_SETTINGS` - Python 3.11, sklearn
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
