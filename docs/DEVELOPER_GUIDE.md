# Developer Guide

Welcome! This guide is for data scientists and ML engineers who will be developing and running ML pipelines using this template.

## Table of Contents

- [Getting Started](#getting-started)
- [Local Development](#local-development)
- [Writing Pipelines](#writing-pipelines)
- [Running Pipelines](#running-pipelines)
- [Working with Models](#working-with-models)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Docker (optional, for containerized execution)
- Text editor or IDE (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-company/zenml-enterprise-mlops
   cd zenml-enterprise-mlops
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize ZenML**:
   ```bash
   zenml init
   ```

5. **Set up local stack** (see [Local Development](#local-development))

## Local Development

### Setting Up Your Local Stack

The local stack allows you to develop and test pipelines on your laptop:

```bash
# Option 1: Use the setup script
./scripts/setup_local.sh

# Option 2: Manual setup
zenml orchestrator register local-orchestrator --flavor=local
zenml artifact-store register local-artifact-store --flavor=local --path=./.zenml/local_store
zenml experiment-tracker register local-mlflow --flavor=mlflow --tracking_uri=http://localhost:5000

zenml stack register local-dev \
    -o local-orchestrator \
    -a local-artifact-store \
    -e local-mlflow

zenml stack set local-dev
```

### Start MLflow Server

For experiment tracking, start a local MLflow server:

```bash
mlflow server --host 127.0.0.1 --port 5000
```

Access the MLflow UI at: http://localhost:5000

### Start ZenML Dashboard

To visualize pipeline runs and models:

```bash
zenml login
```

Access the dashboard at: http://localhost:8237

## Writing Pipelines

### Pipeline Structure

Pipelines in this template follow a clean structure:

```python
from zenml import pipeline, step, Model
from typing import Annotated
import pandas as pd

@step
def load_data() -> Annotated[pd.DataFrame, "raw_data"]:
    """Load training data"""
    # Your data loading logic
    return data

@step
def train_model(
    data: pd.DataFrame
) -> Annotated[ClassifierMixin, "trained_model"]:
    """Train ML model"""
    # Your training logic
    return model

@pipeline(
    model=Model(
        name="my_model",
        description="Description of what this model does",
        tags=["classification", "production"]
    )
)
def training_pipeline():
    """Complete training workflow"""
    data = load_data()
    model = train_model(data)
    return model
```

### Key Conventions

1. **Use `Annotated` for artifact names**:
   ```python
   @step
   def my_step() -> Annotated[pd.DataFrame, "my_artifact_name"]:
       return data
   ```

2. **Type hint everything**:
   ```python
   @step
   def process(data: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
       # Clear inputs and outputs
       pass
   ```

3. **Use `Model` for production pipelines**:
   ```python
   @pipeline(model=Model(name="my_model"))
   def my_pipeline():
       pass
   ```

4. **Keep steps focused**:
   - One clear responsibility per step
   - Reusable across pipelines
   - Easy to test independently

### Example: Creating a New Pipeline

1. **Create pipeline file**: `src/pipelines/my_new_pipeline.py`

2. **Define your steps**:
   ```python
   from zenml import step
   from typing import Annotated
   import pandas as pd

   @step
   def load_custom_data() -> Annotated[pd.DataFrame, "custom_data"]:
       """Load your custom dataset"""
       # Your data loading logic
       data = pd.read_csv("path/to/data.csv")
       return data

   @step
   def custom_preprocessing(
       data: pd.DataFrame
   ) -> Annotated[pd.DataFrame, "processed_data"]:
       """Custom preprocessing logic"""
       # Your preprocessing
       processed = data.dropna()
       return processed
   ```

3. **Compose the pipeline**:
   ```python
   from zenml import pipeline, Model
   # Hooks are applied automatically in staging/production via run.py
   from governance.steps.data_validation import validate_data_quality

   @pipeline(
       model=Model(
           name="my_custom_model",
           description="Custom model for specific use case",
           tags=["custom", "experiment"]
       ),
       # Hooks applied dynamically by run.py based on environment
   )
   def my_custom_pipeline():
       """My custom ML pipeline"""
       raw_data = load_custom_data()
       validated_data = validate_data_quality(raw_data)  # Platform step
       processed_data = custom_preprocessing(validated_data)
       # Continue with training...
   ```

4. **Add to `run.py`** for easy execution

5. **Test locally**:
   ```bash
   python run.py --pipeline my_custom_pipeline
   ```

## Running Pipelines

### Local Execution

```bash
# Run training pipeline
python run.py --pipeline training

# Run with custom parameters
python run.py --pipeline training --n-estimators 200 --max-depth 15

# Run batch inference
python run.py --pipeline batch_inference

# Run dynamic pipeline
python run.py --pipeline dynamic_training
```

### View Results

1. **ZenML Dashboard**:
   ```bash
   zenml login
   # Navigate to http://localhost:8237
   ```

2. **MLflow UI**:
   ```
   # Navigate to http://localhost:5000
   ```

3. **Command line**:
   ```bash
   # List recent runs
   zenml pipeline runs list

   # Show run details
   zenml pipeline runs describe <run-name>

   # List models
   zenml model list

   # Show model details
   zenml model describe breast_cancer_classifier
   ```

## Working with Models

### Registering Models

Models are automatically registered when you use `@pipeline(model=Model(...))`:

```python
@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        version="1.0.0",  # Optional: semantic versioning
        description="Binary classification for risk prediction",
        tags=["healthcare", "classification"]
    )
)
def training_pipeline():
    pass
```

### Loading Models

Load models by name and version or stage:

```python
from zenml import Model
from zenml.client import Client

# Load by version number
model = Model(name="breast_cancer_classifier", version="1")
trained_model = model.load_artifact("model")

# Load by stage (production, staging, etc.)
model = Model(name="breast_cancer_classifier", version=ModelStages.PRODUCTION)
production_model = model.load_artifact("model")
```

### Logging Metadata

```python
from zenml import get_step_context

@step
def evaluate_model(model, test_data) -> dict:
    """Evaluate model and log metrics"""
    metrics = calculate_metrics(model, test_data)

    # Log to Model Control Plane
    context = get_step_context()
    context.model.log_metadata(metrics)

    return metrics
```

## Testing

### Unit Testing Steps

Create tests in `tests/` directory:

```python
# tests/test_steps.py
import pytest
from src.steps.feature_engineering import engineer_features

def test_feature_engineering():
    """Test feature engineering step"""
    # Create sample data
    X_train = pd.DataFrame({...})
    X_test = pd.DataFrame({...})

    # Run step
    X_train_scaled, X_test_scaled, scaler = engineer_features(
        X_train, X_test
    )

    # Assertions
    assert X_train_scaled.shape == X_train.shape
    assert X_test_scaled.shape == X_test.shape
```

### Integration Testing Pipelines

Test full pipeline locally before pushing:

```bash
# Run pipeline with test data
python run.py --pipeline training --test-size 0.3

# Check ZenML dashboard for results
zenml login
```

## Git Workflow

### Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-new-model
   ```

2. **Make changes** in `src/`

3. **Test locally**:
   ```bash
   python run.py --pipeline training
   ```

4. **Commit and push**:
   ```bash
   git add src/
   git commit -m "Add new model training pipeline"
   git push origin feature/my-new-model
   ```

5. **Create Pull Request** to `staging` or `develop` branch

6. **CI/CD runs automatically**:
   - Trains model in staging environment
   - Runs validation checks
   - Comments results on PR

7. **Review and merge**

### Production Deployment

You don't deploy to production directly! Instead:

1. **Model is validated in staging**
2. **Platform team creates GitHub release**
3. **GitHub Actions promotes model to production**
4. **Batch inference picks up new model automatically**

See [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md) for deployment details.

## Troubleshooting

### Common Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'src'
```

**Solution**: Run from repository root, not from subdirectories:
```bash
cd /path/to/zenml-enterprise-mlops
python run.py --pipeline training
```

#### 2. MLflow Connection Error

```
ConnectionError: Cannot connect to MLflow tracking server
```

**Solution**: Start MLflow server:
```bash
mlflow server --host 127.0.0.1 --port 5000
```

#### 3. Stack Not Set

```
RuntimeError: No active stack set
```

**Solution**: Set your local stack:
```bash
zenml stack set local-dev
```

#### 4. Permission Errors

```
PermissionError: Cannot write to artifact store
```

**Solution**: Check artifact store path permissions:
```bash
ls -la .zenml/local_store
chmod -R u+w .zenml/local_store
```

### Getting Help

1. **Check logs**:
   ```bash
   # ZenML logs
   cat .zen/logs/zenml.log

   # Pipeline run logs
   zenml pipeline runs logs <run-name>
   ```

2. **Enable debug mode**:
   ```bash
   export ZENML_DEBUG=true
   python run.py --pipeline training
   ```

3. **Ask the platform team**:
   - Slack: #mlops-support
   - Email: mlops-team@company.com

4. **Check ZenML docs**:
   - https://docs.zenml.io
   - https://zenml.io/slack (Community Slack)

## Best Practices

### Do's ✅

- Write clean, typed Python code
- Test pipelines locally before creating PR
- Use meaningful model and artifact names
- Log relevant metrics and metadata
- Keep steps small and focused
- Reuse platform validation steps
- Follow naming conventions

### Don'ts ❌

- Don't commit secrets or credentials
- Don't modify `governance/` without approval
- Don't push directly to `main` or `staging`
- Don't hardcode file paths or URLs
- Don't skip validation steps
- Don't modify stack configurations
- Don't deploy to production directly

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Check [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md) for deployment workflows
- Explore [examples/](../examples/) for more patterns
- Review existing pipelines in `src/pipelines/`

---

**Need help?** Reach out to the platform team on Slack (#mlops-support) or email mlops-team@company.com
