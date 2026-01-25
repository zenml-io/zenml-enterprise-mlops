# ZenML Pipeline Configurations

This directory contains environment-specific configurations for ZenML pipelines.

## Usage

### Via CLI

```bash
# Run with staging config
zenml pipeline run src.pipelines.training.training_pipeline \
    --config configs/staging.yaml

# Run with production config
zenml pipeline run src.pipelines.training.training_pipeline \
    --config configs/production.yaml
```

### Via Python

```python
from src.pipelines.training import training_pipeline

# Run with config file
training_pipeline.with_options(
    config_path="configs/staging.yaml"
)()
```

### Via run.py (Local Development)

```bash
# Run locally with environment-specific config
python run.py --environment local
python run.py --environment staging
```

### Via build_snapshot.py (CI/CD Snapshots)

```bash
# Create staging snapshot (auto-run)
python scripts/build_snapshot.py --environment staging --stack my-stack --run

# Create production snapshot (manual approval required)
python scripts/build_snapshot.py --environment production --stack my-stack
```

## Configuration Files

| File | Cache | Thresholds | Use Case |
|------|-------|------------|----------|
| `local.yaml` | Enabled | 70% accuracy | Fast local iteration |
| `staging.yaml` | Disabled | 70% accuracy | Pre-release validation |
| `production.yaml` | Disabled | 80% accuracy | Production deployment |

## Configuration Structure

ZenML configs follow this structure:

```yaml
# Run naming (uses ZenML substitution placeholders: {date}, {time})
run_name: "training_staging_{date}_{time}"

# Cache behavior
enable_cache: false

# Pipeline parameters
parameters:
  n_estimators: 100
  max_depth: 10

# Tags for this environment
tags:
  - "staging"

# Settings (docker, resources, etc.)
settings:
  docker:
    parent_image: python:3.11-slim
```

## See Also

- [ZenML Configuration Docs](https://docs.zenml.io/how-to/pipeline-development/use-configuration-files)
