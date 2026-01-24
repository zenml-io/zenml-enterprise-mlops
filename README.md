# ZenML Enterprise MLOps Template

> **Production-ready MLOps patterns for regulated industries and enterprise teams**

This template demonstrates enterprise-grade machine learning operations using ZenML, showcasing best practices for:
- ✅ Multi-environment model promotion (dev → staging → production)
- ✅ GitOps-driven workflows with approval gates
- ✅ Platform team governance without developer friction
- ✅ Complete audit trails and lineage tracking
- ✅ Batch inference with model aliases
- ✅ Clean developer experience (no wrapper code!)

Built for healthcare and regulated industries, but applicable to any enterprise MLOps use case.

## 🎯 Use Case

**Patient Readmission Risk Prediction** - Predict 30-day hospital readmission risk using clinical and demographic data. Uses the UCI Diabetes dataset for demonstration purposes.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker (for containerized execution)
- Git and GitHub account (for GitOps features)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/zenml-io/zenml-enterprise-mlops
cd zenml-enterprise-mlops

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize ZenML
zenml init

# Start ZenML UI (optional but recommended)
zenml up

# Run the training pipeline
python run.py --pipeline training
```

### First Run

The training pipeline will:
1. Load and preprocess the diabetes dataset
2. Train a classification model
3. Evaluate performance
4. Register model with MLflow
5. Log all metadata to ZenML Model Control Plane

Check the ZenML dashboard at http://localhost:8237 to see your pipeline run!

## 📁 Repository Structure

```
zenml-enterprise-mlops/
├── platform/              # Platform team governance (hooks, base images, shared steps)
├── src/                   # Data scientist workspace (pipelines, steps, utils)
├── .github/workflows/     # GitOps automation (CI/CD, promotion, scheduling)
├── configs/               # Configuration files
├── scripts/               # Utility scripts
├── notebooks/             # Demo notebooks
└── docs/                  # Comprehensive documentation
```

## 🎭 Key Demonstrations

### 1. Clean Developer Experience

Data scientists write pure Python with no wrapper code:

```python
from zenml import pipeline, step, Model
from typing import Annotated
import pandas as pd

@step
def train_model(data: pd.DataFrame) -> Annotated[ClassifierMixin, "model"]:
    """Train model - that's it, no wrappers!"""
    model = RandomForestClassifier()
    model.fit(data[features], data[target])
    return model

@pipeline(model=Model(name="patient_readmission_predictor"))
def training_pipeline():
    data = load_data()
    model = train_model(data)
    evaluate_model(model)
```

### 2. Platform Team Governance

Platform team enforces governance without touching pipeline code:

```python
# platform/hooks/mlflow_hook.py
def mlflow_logging_hook():
    """Automatically logs metadata to MLflow after every step"""
    context = get_step_context()
    mlflow.log_metadata({
        "step": context.step_run.name,
        "user": context.user.name,
    })
```

Applied globally via pipeline decorator - developers never see it!

### 3. GitOps Model Promotion

```yaml
# .github/workflows/promote-production.yml
name: Promote to Production
on:
  release:
    types: [published]

jobs:
  promote:
    - run: python scripts/promote_model.py --stage production --version ${{ github.event.release.tag_name }}
```

### 4. Batch Inference with Model Aliases

```python
@step
def load_production_model() -> ClassifierMixin:
    """Always loads current production model"""
    model = Model(name="patient_readmission_predictor", version=ModelStages.PRODUCTION)
    return model.load_artifact("model")
```

### 5. Complete Lineage Tracing

```python
# Trace a prediction back to source
model = client.get_model_version("patient_readmission_predictor", "production")
training_run = model.get_pipeline_run()
training_data = training_run.steps["load_data"].outputs["data"]
code_commit = training_run.metadata["git_commit"]
```

## 📚 Documentation

- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - For data scientists using the platform
- **[Platform Guide](docs/PLATFORM_GUIDE.md)** - For MLOps engineers maintaining governance
- **[Architecture](docs/ARCHITECTURE.md)** - Design decisions and patterns
- **[Demo Script](docs/DEMO_SCRIPT.md)** - Step-by-step walkthrough

## 🔄 Typical Workflows

### Development Workflow

1. Data scientist creates feature branch
2. Writes pipeline code (clean Python, no wrappers)
3. Tests locally with `python run.py --pipeline training`
4. Creates PR to `staging` branch
5. GitHub Actions automatically trains model in staging
6. Reviews results, merges PR

### Production Promotion Workflow

1. Model validated in staging environment
2. Create GitHub release with version tag
3. GitHub Actions promotes model to production
4. Deployment pipeline updates endpoints
5. Batch inference uses new production model

### Monitoring Workflow

1. Scheduled batch inference runs daily
2. Predictions logged to monitoring system
3. Platform hooks ensure compliance tracking
4. Drift detection alerts on data changes

## 🛠️ Configuration

### Stack Configuration

```bash
# Local development stack
zenml stack register local \
  --orchestrator local \
  --artifact-store local

# Staging stack (example with GCP)
zenml stack register staging \
  --orchestrator vertex-staging \
  --artifact-store gcs-staging \
  --experiment-tracker mlflow-staging \
  --model-registry mlflow-staging
```

### Model Configuration

Edit `configs/model_config.yaml`:

```yaml
model:
  name: patient_readmission_predictor
  algorithm: random_forest
  hyperparameters:
    n_estimators: 100
    max_depth: 10
```

## 🎓 Learning Path

1. **Start here**: Run `python run.py --pipeline training` locally
2. **Understand structure**: Read [Architecture](docs/ARCHITECTURE.md)
3. **Developer view**: Follow [Developer Guide](docs/DEVELOPER_GUIDE.md)
4. **Platform view**: Study [Platform Guide](docs/PLATFORM_GUIDE.md)
5. **Advanced**: Set up GitOps workflows
6. **Expert**: Customize for your organization

## 🤝 Contributing

This is a template repository. Feel free to:
- Fork and adapt for your organization
- Submit PRs with improvements
- Share feedback via issues
- Use as a starting point for your MLOps platform

## 📝 License

Apache License 2.0 - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built with [ZenML](https://zenml.io) - The open-source MLOps framework for production-ready ML pipelines.

---

**Questions?** Check out the [ZenML Docs](https://docs.zenml.io) or join our [Slack Community](https://zenml.io/slack)
