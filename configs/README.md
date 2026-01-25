# Configuration Files

This directory contains **reference configuration templates** for different environments.

## Important Note

⚠️ **These configuration files are NOT automatically loaded by the pipelines.** They serve as:

1. **Documentation** - Showing recommended settings for each environment
2. **Reference templates** - Demonstrating configuration patterns
3. **Manual guidance** - Settings to consider when deploying

## Using These Configurations

### Option 1: Manual Parameter Passing

Pass parameters directly when running pipelines:

```bash
python run.py --pipeline training \
  --n-estimators 50 \
  --max-depth 5 \
  --min-accuracy 0.70
```

### Option 2: Load in Code

Modify your pipeline invocation to load from YAML:

```python
import yaml
from pathlib import Path

# Load config
config_path = Path("configs/staging.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Run pipeline with config values
training_pipeline(
    n_estimators=config["model"]["hyperparameters"]["n_estimators"],
    max_depth=config["model"]["hyperparameters"]["max_depth"],
    min_accuracy=config["model"]["validation"]["min_accuracy"],
)
```

### Option 3: ZenML with_options (Pro Feature)

Use ZenML's `with_options` to apply configuration:

```python
from src.pipelines.training import training_pipeline

# Create snapshot with config
snapshot = training_pipeline.with_options(
    config_path="configs/staging.yaml",
).create_snapshot(name="STG_model_abc123")
```

> **Note**: The `config_path` feature requires specific ZenML configuration structure and may need adaptation based on your ZenML version.

## Configuration Files

- **`staging.yaml`** - Settings for staging environment (faster iteration, lower thresholds)
- **`production.yaml`** - Settings for production environment (stricter validation, compliance)

## Environment-Specific Settings

### Staging
- Smaller models for faster iteration (`n_estimators: 50`)
- Lower validation thresholds (`min_accuracy: 0.70`)
- Manual triggers only
- Single replica serving

### Production
- Full-size models (`n_estimators: 100+`)
- Strict validation thresholds (`min_accuracy: 0.85`)
- Approval gates required
- Multi-replica serving with autoscaling
- Enhanced monitoring and compliance logging

## Extending Configuration

To add custom configuration:

1. Add new fields to the YAML files following the existing structure
2. Update your pipeline code to read these values
3. Document the new settings in this README
4. Consider adding validation for critical configuration values

## Best Practices

- Keep sensitive values (API keys, passwords) in environment variables or secrets managers, NOT in these files
- Use version control to track configuration changes
- Test configuration changes in staging before applying to production
- Document any non-obvious configuration choices
