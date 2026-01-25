# ZenML Enterprise MLOps Template - Claude Code Guidelines

This document provides comprehensive context for Claude Code when working with the ZenML Enterprise MLOps template repository.

## What Is This Repository?

This is a **production-ready enterprise MLOps template** demonstrating ZenML best practices for regulated industries. It serves as:

1. **Customer Demo** - Primary use case is demonstrating ZenML capabilities to enterprise customers
2. **Reference Implementation** - Shows enterprise patterns for multi-environment model promotion, GitOps, governance
3. **Template** - Customers can fork and customize for their own use cases

### Key Demo Scenario

**Target Audience**: Large enterprises in regulated industries (financial services, life sciences, etc.)

**Their #1 Pain Point**: Multi-environment model promotion (dev → staging → production) with proper governance and audit trails

**What We're Solving**:
- Clean developer experience (data scientists write pure Python, no wrapper code)
- Platform team governance (hooks enforce standards without touching ML code)
- GitOps workflows (GitHub Actions trigger training/promotion)
- Model Control Plane (single source of truth for models, metadata, lineage)
- Complete audit trails (regulatory compliance, track everything)

## Why This Structure?

### Separation of Concerns

```
governance/     # Platform team owns (hooks, validation, infrastructure)
src/            # Data scientists own (ML code, pipelines, steps)
```

**Rationale**: In regulated industries, the platform team enforces compliance/governance while data scientists focus on ML. Clean separation makes responsibilities clear.

### Single Workspace Architecture

**Decision**: Recommend single workspace + multiple projects (Pro) or single project + environment stacks (OSS)

**Why**:
- **Enterprise customers' #1 pain point is model promotion** - workspace isolation breaks promotion workflows
- Platform team needs visibility across all teams
- Shared governance components (hooks, base images, validation)
- Simpler credential management

**Why NOT multiple workspaces**:
- Physical isolation prevents model promotion across workspaces
- Breaks dev → staging → production workflow
- Only use for hard regulatory boundaries (e.g., different compliance zones)

### Pro-First, OSS-Compatible

**Primary target**: ZenML Pro users (enterprise customers with multiple teams)

**Secondary**: OSS users can follow single-team patterns

**Key differences**:
- Pro: Multiple projects, RBAC, pipeline snapshots, audit logs
- OSS: Single project, environment-based stacks, GitHub-based access control

Both get: Clean pipelines, hooks, GitOps, Model Control Plane, lineage tracking

## Repository Architecture

### Governance Folder (`governance/`)

**Owner**: Platform team

**Purpose**: Enforce standards automatically without touching ML code

**Contents**:
- `hooks/` - Automatic enforcement (MLflow logging, compliance)
- `steps/` - Shared validation (data quality, model performance)
- `materializers/` - Enhanced artifact handling with metadata
- `stacks/terraform/` - Infrastructure as Code

**Pattern**: Data scientists import from governance, never modify it

```python
from governance.hooks import mlflow_success_hook
from governance.steps import validate_data_quality

@pipeline(on_success=mlflow_success_hook)  # Automatic enforcement
def training_pipeline():
    data = load_data()
    data = validate_data_quality(data)  # Shared governance
    model = train_model(data)
    return model
```

### Source Folder (`src/`)

**Owner**: Data scientists

**Purpose**: ML code, pipelines, custom logic

**Contents**:
- `pipelines/` - training.py, batch_inference.py, champion_challenger.py, realtime_inference.py
- `steps/` - data_loader.py, model_trainer.py, etc.
- `utils/` - Helper functions

**Pattern**: Pure Python, no governance mixed in

### Dynamic Pipeline Pattern

**File**: `src/pipelines/training.py`

**Key Feature**: Pipeline adapts at runtime based on data characteristics

```python
# SMOTE resampling if class imbalance detected
X_train, y_train = check_and_apply_smote(
    X_train, y_train,
    enable_resampling=True,
    imbalance_threshold=0.3,  # Trigger if minority < 30%
)

# PCA if too many features
X_train, X_test, pca = check_and_apply_pca(
    X_train, X_test,
    enable_pca=True,
    max_features=50,  # Trigger if features > 50
)
```

**Why**: Shows ZenML can handle complex, adaptive workflows (not just static DAGs)

**Critical Pattern**: Logic inside steps, not pipeline-level conditionals (ZenML compiles to DAG before execution)

### GitOps Workflows

**Files**: `.github/workflows/`

**Pattern**: Git events trigger ML workflows

```
PR to staging branch → Auto-train model in staging
GitHub Release → Promote model to production
Schedule (daily) → Run batch inference
```

**Why**: Demonstrates production deployment patterns for enterprise customers

### Model Control Plane

**Pattern**: Single source of truth for all model metadata

```
Model: patient_readmission_predictor
├── Version 1 (archived)
├── Version 2 (staging)
└── Version 3 (production)
    ├── Artifacts: model, scaler, metrics
    ├── Metadata: git_commit, accuracy, f1_score
    └── Lineage: data → features → model → predictions
```

**Why**: Enterprises need complete audit trails for regulatory compliance

## Critical Patterns to Maintain

### 1. Hook-Based Governance

**Do**:
```python
@pipeline(on_success=mlflow_success_hook, on_failure=compliance_failure_hook)
def training_pipeline():
    # Clean ML code
    pass
```

**Don't**:
```python
@step
def train_model(data):
    model = fit_model(data)
    log_to_mlflow(model)  # Governance mixed in - BAD!
    return model
```

**Why**: Platform team controls governance without touching ML code

### 2. No Pipeline-Level Conditionals

**Don't**:
```python
@pipeline
def training_pipeline():
    needs_smote = check_imbalance()
    if needs_smote:  # This FAILS - needs_smote is artifact, not boolean
        apply_smote()
```

**Do**:
```python
@step
def check_and_apply_smote(...) -> tuple[X, y]:
    if imbalance_detected:  # Logic inside step
        return apply_smote(X, y)
    return X, y
```

**Why**: ZenML compiles pipeline to DAG before execution - can't use step outputs as booleans

### 3. Model Promotion via Stages

**Pattern**:
```python
# Training creates new version (no stage)
model = train_model()

# Validation passes → set to staging
if metrics["accuracy"] > 0.85:
    model_version.set_stage("staging")

# Promotion script validates → set to production
if meets_production_criteria():
    model_version.set_stage("production")
```

**Why**: Solves enterprise customers' #1 pain point - clear promotion workflow with validation gates

## Pro vs OSS Positioning

### For Pro Users (Primary Demo Audience)

**Show**:
- Multiple projects for team isolation
- RBAC with custom roles (data-scientist, ml-engineer, platform-admin)
- Pipeline snapshots for immutable deployments
- Cross-project visibility for platform team

**Architecture**:
```
Workspace: "enterprise-ml"
├── Project: risk-models (Team A)
├── Project: fraud-detection (Team B)
└── Project: platform-shared (Platform team)
```

### For OSS Users (Secondary)

**Show**:
- Single project with environment stacks
- Stack-based resource isolation (dev/staging/prod)
- GitHub-based access control
- Hook-based governance

**Architecture**:
```
Project: "default"
├── Stack: local-dev (local)
├── Stack: staging (GCP staging project)
└── Stack: production (GCP production project)
```

## What Works for Both

All core patterns work identically:
- ✅ Clean Python pipelines
- ✅ Hook-based governance
- ✅ Model Control Plane
- ✅ GitOps workflows
- ✅ Multi-environment promotion (via stacks for OSS, projects for Pro)
- ✅ Lineage tracking
- ✅ Dynamic preprocessing

## Documentation Strategy

### Single Consolidated Guide

**File**: `docs/ARCHITECTURE.md`

**Why**: Was 3 separate docs (~1,600 lines), now 1 consolidated doc (775 lines)

**Structure**:
1. Overview & Design Principles
2. Multi-Tenancy & Organization (Pro vs OSS)
3. Repository Structure & Component Responsibilities
4. Stack Organization & Access Control
5. Data Flow & Security
6. Deployment & Technology Stack
7. Design Trade-offs & Best Practices

**Rationale**: Easier to navigate, single source of truth, clear progression from principles to implementation

### Other Docs

- `docs/DEVELOPER_GUIDE.md` - For data scientists
- `docs/PLATFORM_GUIDE.md` - For platform engineers
- `governance/README.md` - Shared components usage

## Demo Talking Points

### 1. Clean Developer Experience

**Show**: `src/pipelines/training.py`

**Point**: "Data scientists write pure Python - no wrapper code, no boilerplate. Just `@step` and `@pipeline`."

### 2. Platform Governance

**Show**: `governance/hooks/` and how pipelines use them

**Point**: "Platform team enforces governance automatically via hooks. Data scientists never see it - it just works."

### 3. Multi-Environment Promotion

**Show**: `scripts/promote_model.py` and `.github/workflows/promote-production.yml`

**Point**: "This solves your #1 pain point. Models promote through dev → staging → production with validation gates and complete audit trails."

### 4. GitOps Integration

**Show**: `.github/workflows/`

**Point**: "All deployments triggered by Git events. PR to staging auto-trains model. GitHub release promotes to production."

### 5. Model Control Plane

**Show**: `notebooks/lineage_demo.ipynb`

**Point**: "Single source of truth for all model metadata. Complete lineage from prediction back to source data and code."

### 6. Dynamic Workflows

**Show**: `src/pipelines/training.py` SMOTE and PCA logic

**Point**: "Not just static DAGs. Pipeline adapts at runtime based on data characteristics."

### 7. Champion/Challenger Pattern

**Show**: `src/pipelines/champion_challenger.py`

**Point**: "Safe model rollouts. Compare production model against staging candidate side-by-side before promotion. Get agreement rates, probability differences, and automatic promotion recommendations."

**Run**: `python run.py --pipeline champion_challenger`

### 8. Real-Time Inference (Pipeline Deployments)

**Show**: `src/pipelines/realtime_inference.py`

**Point**: "Pipeline Deployments turn pipelines into HTTP services. Full pipeline logic per request - not just model serving. Cloud Run backend for production scale."

**Deploy**: `zenml pipeline deploy src.pipelines.realtime_inference.inference_service --name readmission-api`

**Invoke**: `curl -X POST http://localhost:8000/invoke -d '{"parameters": {"patient_data": {"age": 72}}}'`

### 9. Platform-Managed Docker Settings

**Show**: `governance/docker/docker_settings.py`

**Point**: "Platform team controls containerization. Data scientists get consistent, secure environments without writing Dockerfiles. GPU, CPU, lightweight configs ready to use."

**Usage**:
```python
from governance.docker import STANDARD_DOCKER_SETTINGS, GPU_DOCKER_SETTINGS

@pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
def training_pipeline():
    ...

@step(settings={"docker": GPU_DOCKER_SETTINGS})
def train_with_gpu():
    ...
```

## Common Issues & Solutions

### Issue: "Why not use if/else in pipeline?"

**Answer**: ZenML compiles pipeline to DAG before execution. Step outputs are artifacts, not Python values. Put conditional logic inside steps.

### Issue: "Why single workspace instead of multiple?"

**Answer**: Multiple workspaces create physical isolation - models can't be promoted across workspaces. This breaks the multi-environment promotion use case. Use single workspace with projects for team isolation.

### Issue: "Why not mix governance into ML code?"

**Answer**: Separation of concerns. Platform team needs to update governance (add logging, change validation) without touching 100+ ML pipelines. Hooks make this possible.

### Issue: "Do I need ZenML Pro for this template?"

**Answer**: No - all core patterns work with OSS. Pro adds multi-project isolation, RBAC, pipeline snapshots, and audit logs. OSS users use single project with environment stacks.

## Development Guidelines

### When Adding Code

1. **Governance code** → `governance/` (platform team)
2. **ML code** → `src/` (data scientists)
3. **Never mix governance into ML steps**

### When Adding Documentation

1. **Architecture/organization** → `docs/ARCHITECTURE.md`
2. **Developer patterns** → `docs/DEVELOPER_GUIDE.md`
3. **Platform patterns** → `docs/PLATFORM_GUIDE.md`

### When Adding Infrastructure

1. **Terraform configs** → `governance/stacks/terraform/`
2. **Docker images** → `governance/docker/`
3. **GitHub Actions** → `.github/workflows/`

### Best Practices

- Use `Annotated` for artifact names: `Annotated[pd.DataFrame, "X_train"]`
- Never use pipeline-level conditionals (put logic in steps)
- Use hooks for governance, not step decorators
- Reference Model Control Plane as single source of truth
- Keep environment isolation via stacks, not projects/workspaces

## Files to Never Modify (Core Patterns)

These demonstrate key patterns - changing them breaks the demo:

- ✋ `src/pipelines/training.py` - Shows dynamic preprocessing pattern
- ✋ `src/pipelines/batch_inference.py` - Shows loading production model by stage
- ✋ `src/pipelines/champion_challenger.py` - Shows A/B model comparison pattern
- ✋ `src/pipelines/realtime_inference.py` - Shows Pipeline Deployments for serving
- ✋ `governance/hooks/mlflow_hook.py` - Shows hook-based governance
- ✋ `scripts/promote_model.py` - Shows promotion with validation gates
- ✋ `.github/workflows/promote-production.yml` - Shows GitOps pattern

## What Can Be Extended

These are meant to be extended/customized:

- ✅ Add more orchestrators (Kubernetes, Databricks)
- ✅ Add log stores (OTEL, Datadog)
- ✅ Add shared governance steps
- ✅ Add Docker settings for specialized workloads (NLP, vision, etc.)
- ✅ Add base Docker images with custom dependencies
- ✅ Add more validation logic
- ✅ Add monitoring integrations

## Running the Demo

The `demo/` folder contains an interactive demo with chapters:

```bash
# Run full interactive demo
python demo/run_demo.py

# Run specific chapter
python demo/run_demo.py --chapter 2

# List all chapters
python demo/run_demo.py --list
```

**Demo Chapters:**
1. Train a Model (clean code, automatic governance)
2. Explore Model Control Plane (lineage, audit trail)
3. Promote to Staging (validation gates)
4. Champion vs Challenger (safe rollouts)
5. Promote to Production (higher bar, GitOps)
6. Batch Inference (scheduled, load by stage)

## Testing Locally

```bash
# Install dependencies (using uv for speed)
uv pip install -r requirements.txt

# Initialize ZenML
zenml init

# Run training pipeline
python run.py --pipeline training

# Run batch inference
python run.py --pipeline batch_inference

# Run champion/challenger comparison
python run.py --pipeline champion_challenger

# Deploy real-time inference service
zenml pipeline deploy src.pipelines.realtime_inference.inference_service \
    --name readmission-api

# Check results in dashboard
zenml up
```

## Key Metrics for Success

For enterprise demos, we need to show:

1. ✅ **Clean code** - Pure Python, no wrappers
2. ✅ **Automatic governance** - Hooks enforce without code changes
3. ✅ **Multi-environment promotion** - Dev → staging → production
4. ✅ **Complete audit trails** - Full lineage, metadata, compliance
5. ✅ **GitOps workflows** - Git events trigger ML operations
6. ✅ **Production-ready** - Real Terraform, GitHub Actions, not toys
7. ✅ **Champion/Challenger** - Safe model rollouts with A/B comparison
8. ✅ **Real-time serving** - Pipeline Deployments for HTTP inference
9. ✅ **Containerization** - Platform-managed Docker settings for consistent environments

## Context for Questions

If asked "Why X?" - the answer is usually:

1. **"Why this structure?"** → Separation of concerns for enterprise teams
2. **"Why hooks?"** → Platform controls governance without touching ML code
3. **"Why single workspace?"** → Model promotion (enterprise customers' #1 pain point)
4. **"Why Model Control Plane?"** → Single source of truth for audit trails
5. **"Why GitOps?"** → Production deployment pattern for enterprises
6. **"Why no pipeline conditionals?"** → ZenML compiles to DAG before execution

## Summary

This template demonstrates **enterprise MLOps patterns** for **regulated industries**. It solves **enterprise customers' #1 pain point** (multi-environment model promotion) while maintaining **clean developer experience**, **platform governance**, and **complete audit trails**.

**Primary audience**: ZenML Pro users with multiple teams

**Key patterns**: Hook-based governance, Model Control Plane, GitOps, dynamic pipelines

**Core value**: Shows how ZenML enables enterprise MLOps without sacrificing developer experience

---

**For questions or clarifications, see**:
- `docs/ARCHITECTURE.md` - Complete architecture and organization guide
- `governance/README.md` - Shared components documentation
- `CHANGES_SUMMARY.md` - Recent changes and rationale
