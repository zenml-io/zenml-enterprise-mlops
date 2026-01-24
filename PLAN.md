# ZenML Enterprise MLOps Template - Implementation Plan

## Project Overview

This is an enterprise-ready MLOps template showcasing ZenML best practices for healthcare/regulated industries. Built specifically to address HCA Healthcare's requirements, but designed as a generic template for any enterprise customer.

**Demo Date:** January 27, 2026
**Target Audience:** Enterprise customers with complex governance, multi-environment promotion, and GitOps requirements

## Use Case

**Patient Readmission Risk Prediction**
- Healthcare-relevant but uses public data (UCI Diabetes dataset)
- Demonstrates compliance, audit trails, and governance
- Shows complete ML lifecycle from training to batch inference
- Production-ready patterns applicable to any supervised ML problem

## Key Demonstrations

### 1. Multi-Environment Model Promotion (HCA's #1 Pain Point)
- Train model → promote to staging → promote to production
- GitOps-based promotion (PR merge, release tags)
- Approval gates and RBAC
- Full lineage preservation across environments

### 2. Platform Team Control + Clean Developer Experience
- Data scientists write pure Python (no wrappers!)
- Platform team enforces governance via:
  - Pipeline hooks (auto-logging, monitoring)
  - Base Docker images
  - Required stack components
  - Shared validation steps

### 3. GitOps Integration
- Train on PR to staging branch
- Promote on release creation
- Scheduled batch inference
- Declarative deployment manifests

### 4. Audit & Lineage
- Trace predictions back to training data
- Track code commits via GitHub integration
- Full Model Control Plane lineage
- Compliance-ready audit trails

### 5. Batch Inference with Model Aliases
- Reference "production" model by stage
- Automatic model loading
- Monitoring integration
- Results versioning

## Repository Structure

```
zenml-enterprise-mlops/
├── .github/
│   └── workflows/
│       ├── train-staging.yml          # Auto-train on PR to staging
│       ├── promote-production.yml     # Promote on release
│       └── batch-inference.yml        # Scheduled daily inference
│
├── platform/                          # Platform team owns/maintains
│   ├── docker/
│   │   ├── Dockerfile.base           # Base image with MLflow, etc.
│   │   └── requirements.txt
│   ├── hooks/
│   │   ├── __init__.py
│   │   ├── mlflow_hook.py           # Auto-log to MLflow
│   │   ├── monitoring_hook.py       # Send metrics to monitoring
│   │   └── compliance_hook.py       # Data validation, audit
│   ├── steps/                       # Shared governed steps
│   │   ├── __init__.py
│   │   ├── data_validation.py
│   │   └── model_validation.py
│   └── stacks/
│       ├── local-stack.yaml
│       ├── staging-stack.yaml
│       └── production-stack.yaml
│
├── src/                              # Data scientists work here
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── training.py              # Model training pipeline
│   │   ├── promotion.py             # Model promotion pipeline
│   │   ├── deployment.py            # Deploy to endpoint (optional)
│   │   └── batch_inference.py       # Batch prediction pipeline
│   │
│   ├── steps/                       # Custom ML steps
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── feature_engineering.py
│   │   ├── model_trainer.py
│   │   ├── model_evaluator.py
│   │   └── predictor.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── model_utils.py
│
├── configs/
│   ├── model_config.yaml            # Model hyperparameters
│   └── deployment_config.yaml       # Deployment settings
│
├── scripts/
│   ├── setup_local.sh               # Local dev setup
│   ├── promote_model.py             # Model promotion CLI
│   └── setup_stacks.sh              # Configure ZenML stacks
│
├── notebooks/
│   └── 01_lineage_demo.ipynb       # Show lineage tracing
│
├── docs/
│   ├── ARCHITECTURE.md              # Architecture decisions
│   ├── DEVELOPER_GUIDE.md           # For data scientists
│   ├── PLATFORM_GUIDE.md            # For platform engineers
│   └── DEMO_SCRIPT.md               # Step-by-step demo
│
├── .dockerignore
├── .gitignore
├── LICENSE
├── README.md                        # Quick start guide
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Optional: for packaging
└── PLAN.md                          # This file
```

## Implementation Timeline

### Day 1 (Jan 24) - Foundation
- [x] Create repository structure
- [x] Write PLAN.md
- [ ] Create README.md with quick start
- [ ] Set up .gitignore and basic files
- [ ] Create requirements.txt
- [ ] Build basic training pipeline
- [ ] Create platform hooks (MLflow)
- [ ] Test locally

### Day 2 (Jan 25) - GitOps & Promotion
- [ ] Create GitHub Actions workflows
- [ ] Build promotion pipeline
- [ ] Build batch inference pipeline
- [ ] Create promotion script
- [ ] Set up model stages workflow
- [ ] Test promotion flow

### Day 3 (Jan 26) - Polish & Documentation
- [ ] Create lineage demo notebook
- [ ] Write comprehensive docs
- [ ] Create demo script
- [ ] Polish README
- [ ] End-to-end testing
- [ ] Record demo scenarios

### Demo Day (Jan 27)
- [ ] Live demonstration
- [ ] Q&A handling
- [ ] Gather feedback

## ZenML Best Practices to Follow

### 1. Use Annotated for Artifact Naming
```python
from typing import Annotated
from sklearn.base import ClassifierMixin

@step
def train_model() -> Annotated[ClassifierMixin, "trained_model"]:
    return model
```

### 2. Model Control Plane Integration
```python
from zenml import Model, pipeline

@pipeline(
    model=Model(
        name="patient_readmission_predictor",
        version="production",
        description="Predicts 30-day readmission risk"
    )
)
def training_pipeline():
    ...
```

### 3. Use ArtifactConfig for Model Artifacts
```python
from zenml import ArtifactConfig

@step
def train() -> Annotated[
    ClassifierMixin,
    ArtifactConfig(name="model", is_model_artifact=True)
]:
    return model
```

### 4. Proper Hook Usage
```python
from zenml import pipeline
from platform.hooks import mlflow_hook, compliance_hook

@pipeline(
    on_success=mlflow_hook,
    on_failure=compliance_hook
)
def training_pipeline():
    ...
```

### 5. Clean Step Interfaces
```python
# Good: Clear inputs/outputs, typed
@step
def preprocess_data(
    raw_data: pd.DataFrame,
    target_column: str
) -> Annotated[pd.DataFrame, "processed_data"]:
    return processed_data

# Avoid: Unclear interfaces, no types
@step
def preprocess(data):
    return data
```

### 6. Use get_step_context and get_pipeline_context
```python
from zenml import get_step_context

@step
def log_metadata():
    context = get_step_context()
    model = context.model
    model.log_metadata({"accuracy": 0.95})
```

### 7. Experiment Tracker Integration
```python
from zenml.client import Client

experiment_tracker = Client().active_stack.experiment_tracker

@step(experiment_tracker=experiment_tracker.name)
def train_with_tracking():
    import mlflow
    mlflow.autolog()
    ...
```

### 8. Model Registry Integration
```python
from zenml.integrations.mlflow.steps import mlflow_register_model_step

@step
def register_model(model: ClassifierMixin, name: str):
    mlflow_register_model_step.entrypoint(model, name=name)
```

### 9. GitHub Code Repository Integration
```python
# In setup script
zenml code-repository register enterprise-ml \
    --type=github \
    --owner=zenml-io \
    --repository=zenml-enterprise-mlops \
    --token={{github_secret.token}}
```

### 10. Proper Materializer Usage
- Let ZenML auto-detect materializers
- Only create custom ones when needed
- Use built-in materializers for common types

## Key Files to Create First

### Priority 1 (Core Functionality)
1. `README.md` - Quick start guide
2. `requirements.txt` - Dependencies
3. `.gitignore` - Standard Python/ZenML ignores
4. `src/pipelines/training.py` - Main training pipeline
5. `src/steps/model_trainer.py` - Training step
6. `platform/hooks/mlflow_hook.py` - Auto-logging hook

### Priority 2 (GitOps & Promotion)
7. `.github/workflows/train-staging.yml` - CI/CD
8. `scripts/promote_model.py` - Promotion script
9. `src/pipelines/batch_inference.py` - Inference pipeline

### Priority 3 (Documentation & Demo)
10. `docs/DEMO_SCRIPT.md` - Demo walkthrough
11. `notebooks/01_lineage_demo.ipynb` - Lineage showcase
12. `docs/ARCHITECTURE.md` - Design decisions

## Testing Strategy

### Local Testing
1. Train pipeline locally with local MLflow
2. Verify artifacts are created
3. Test model promotion
4. Run batch inference

### Integration Testing
1. Test with remote artifact store (optional)
2. Test GitHub Actions (in fork)
3. Test promotion workflow
4. End-to-end pipeline run

## Success Criteria

- [ ] Clean developer experience (no wrapper code)
- [ ] Platform governance enforcement (hooks work)
- [ ] Model promotion flow demonstrated
- [ ] GitOps integration working
- [ ] Lineage tracing demonstrated
- [ ] Comprehensive documentation
- [ ] Demo-ready by Jan 26

## Questions to Address in Demo

### For HCA Healthcare
1. ✅ Multi-environment promotion → Show stage transitions
2. ✅ Platform control → Show hooks enforcing MLflow
3. ✅ GitOps → Show GitHub Actions
4. ✅ Lineage → Show notebook tracing
5. ✅ Clean dev experience → Show simple pipeline code
6. ✅ Batch inference → Show production model usage

### For Other Customers
- How to adapt to their cloud (AWS/Azure/GCP)
- How to integrate their tools (not just MLflow)
- How to customize governance policies
- How to scale to multiple teams

## Post-Demo Next Steps

1. Gather feedback from HCA demo
2. Polish based on feedback
3. Add AWS/Azure variations (optional)
4. Propose as official ZenML project
5. Blog post about enterprise patterns
6. Add to ZenML docs as reference

## Notes

- Keep it simple but production-ready
- Focus on patterns, not complexity
- Make it forkable/templatable
- Document everything clearly
- Use real-world naming (not "foo", "bar")
- Show compliance considerations
