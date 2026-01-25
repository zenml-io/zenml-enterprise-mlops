# ZenML Pipeline Configurations

This directory contains **real ZenML configuration files** that can be passed directly to pipelines.

## Usage

### Via CLI

```bash
# Run training pipeline with staging config
zenml pipeline run src.pipelines.training.training_pipeline \
    --config configs/training_staging.yaml

# Run training pipeline with production config
zenml pipeline run src.pipelines.training.training_pipeline \
    --config configs/training_production.yaml
```

### Via Python

```python
from src.pipelines.training import training_pipeline

# Run with config file
training_pipeline.with_options(
    config_path="configs/training_staging.yaml"
)()
```

## Configuration Files

| File | Purpose |
|------|---------|
| `training_staging.yaml` | Staging: faster iteration, lower thresholds (50 trees, 70% accuracy) |
| `training_production.yaml` | Production: full model, strict thresholds (100 trees, 80% accuracy) |

## Configuration Structure

ZenML configs follow this structure:

```yaml
# Pipeline parameters (passed to pipeline function)
parameters:
  n_estimators: 100
  max_depth: 10

# Pipeline-level settings (docker, resources, etc.)
settings:
  docker:
    parent_image: python:3.11-slim
  resources:
    cpu_count: 4

# Step-specific overrides
steps:
  train_model:
    parameters:
      learning_rate: 0.01
    settings:
      resources:
        cpu_count: 8
```

## Environment-Specific Settings

### Staging
- Smaller models for faster iteration (`n_estimators: 50`)
- Lower validation thresholds (`min_accuracy: 0.70`)
- Standard resources (2 CPU, 4GB RAM)

### Production
- Full model capacity (`n_estimators: 100`)
- Strict validation (`min_accuracy: 0.80`)
- Higher resources (4 CPU, 8GB RAM)

## See Also

- [ZenML Configuration Docs](https://docs.zenml.io/how-to/pipeline-development/use-configuration-files)
- [Docker Settings](../governance/docker/docker_settings.py) - Platform-managed Docker configurations
