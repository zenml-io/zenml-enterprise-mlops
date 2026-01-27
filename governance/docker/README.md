# Docker Configuration for ML Pipelines

This folder contains platform-managed Docker configurations for containerized pipeline execution.

## Overview

The platform team maintains Docker settings to ensure:
- **Consistent environments** across all teams
- **Security patches** applied centrally
- **Compliance requirements** pre-configured
- **Optimized builds** using uv package installer

Data scientists use these settings without modification.

## Quick Start

```python
from governance.docker import STANDARD_DOCKER_SETTINGS

@pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
def my_pipeline():
    ...
```

## Available Configurations

### STANDARD_DOCKER_SETTINGS

Standard settings for most ML training pipelines.

```python
from governance.docker import STANDARD_DOCKER_SETTINGS

@pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
def training_pipeline():
    data = load_data()
    model = train_model(data)
    return model
```

**Includes:**
- Python 3.11 slim base image
- sklearn integration
- uv for fast package installation

### GPU_DOCKER_SETTINGS

GPU-enabled settings for deep learning workloads.

```python
from governance.docker import GPU_DOCKER_SETTINGS

@step(settings={"docker": GPU_DOCKER_SETTINGS})
def train_neural_network(data):
    import torch
    # GPU training code
    ...
```

**Includes:**
- PyTorch with CUDA 11.8 support
- cuDNN for optimized operations
- OpenCV dependencies

### LIGHTWEIGHT_DOCKER_SETTINGS

Minimal settings for quick iteration.

```python
from governance.docker import LIGHTWEIGHT_DOCKER_SETTINGS

@step(settings={"docker": LIGHTWEIGHT_DOCKER_SETTINGS})
def preprocess_data(raw_data):
    # Light preprocessing, no heavy ML frameworks
    return cleaned_data
```

**Use for:**
- Data preprocessing
- Feature engineering
- Development/testing
- Lightweight inference

## Customizing Settings

Use `get_docker_settings()` to extend platform configurations:

```python
from governance.docker import get_docker_settings

# Add HuggingFace support to standard settings
custom_settings = get_docker_settings(
    base="standard",
    extra_integrations=["huggingface"],
    extra_requirements=["transformers>=4.30.0"],
)

@pipeline(settings={"docker": custom_settings})
def nlp_pipeline():
    ...
```

### Available Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `base` | Base configuration | `"standard"`, `"gpu"`, `"lightweight"` |
| `extra_apt_packages` | Additional system packages | `["ffmpeg", "libsndfile1"]` |
| `extra_integrations` | Additional ZenML integrations | `["huggingface", "wandb"]` |
| `extra_requirements` | Additional Python packages | `["transformers>=4.30.0"]` |
| `extra_environment` | Additional env variables | `{"MY_VAR": "value"}` |
| `parent_image` | Override parent image | `"custom/image:tag"` |

## Base Dockerfile

For advanced use cases, build from the platform base image:

```bash
# Build the base image
docker build -t your-registry/zenml-base:v1.0.0 \
    -f governance/docker/Dockerfile.base .

# Push to your registry
docker push your-registry/zenml-base:v1.0.0
```

Then reference in your settings:

```python
from zenml.config import DockerSettings

custom_settings = DockerSettings(
    parent_image="your-registry/zenml-base:v1.0.0",
    skip_build=True,  # Use parent image directly
)
```

## Per-Step Docker Settings

Apply different settings to specific steps:

```python
from governance.docker import STANDARD_DOCKER_SETTINGS, GPU_DOCKER_SETTINGS

@step(settings={"docker": STANDARD_DOCKER_SETTINGS})
def preprocess():
    # Runs on CPU
    ...

@step(settings={"docker": GPU_DOCKER_SETTINGS})
def train():
    # Runs on GPU
    ...

@pipeline
def ml_pipeline():
    data = preprocess()
    model = train(data)
```

## YAML Configuration

Define Docker settings in configuration files. See [`configs/`](../../configs/) for environment-specific examples (local, staging, production).

```yaml
# config.yaml
settings:
  docker:
    parent_image: python:3.11-slim
    required_integrations:
      - sklearn

steps:
  train:
    settings:
      docker:
        parent_image: pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime
```

Run with configuration:

```bash
python run.py --config config.yaml
```

## Build Optimization

### Reuse Builds

ZenML automatically caches Docker builds. To force a fresh build:

```python
settings = DockerSettings(
    prevent_build_reuse=True,
)
```

### List Existing Builds

```bash
zenml pipeline builds list --pipeline_id='startswith:training'
```

### Run with Specific Build

```python
pipeline.run(build="<build-id>")
```

## Troubleshooting

### Build Fails with Missing Packages

Add system packages via `extra_apt_packages`:

```python
settings = get_docker_settings(
    base="standard",
    extra_apt_packages=["libpq-dev"],  # PostgreSQL
)
```

### Slow Builds

1. Use `uv` (default) instead of `pip`
2. Use a pre-built base image with `skip_build=True`
3. Enable build caching in your container registry

### GPU Not Detected

Ensure your orchestrator/step operator has GPU support:

```python
# Check CUDA availability in step
@step(settings={"docker": GPU_DOCKER_SETTINGS})
def check_gpu():
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"GPU count: {torch.cuda.device_count()}")
```

## For Platform Engineers

### Adding New Base Configurations

1. Define in `docker_settings.py`
2. Export in `__init__.py`
3. Document in this README
4. Announce to teams

### Updating Base Image

1. Update `Dockerfile.base`
2. Test with representative pipelines
3. Bump version label
4. Build and push to registry
5. Update `STANDARD_DOCKER_SETTINGS` parent image
6. Announce changes

### Security Updates

1. Rebuild base image with latest patches
2. Push with new version tag
3. Update references in `docker_settings.py`
4. Teams automatically get updates on next build

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release with standard, GPU, and lightweight configs |

## Support

- **Slack**: #mlops-platform
- **Email**: platform-team@company.com
