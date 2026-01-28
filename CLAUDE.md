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

### 2-Workspace Architecture

**Decision**: Recommend 2 workspaces for environment isolation (Pro) or 2 separate ZenML servers (OSS)

```
Organization: Enterprise MLOps
│
├── Workspace: enterprise-dev-staging
│   ├── Project: cancer-detection
│   ├── Stack: dev-stack (local orchestrator, fast iteration)
│   ├── Stack: staging-stack (Vertex AI, production-like testing)
│   ├── Training pipeline runs (FULL LINEAGE)
│   └── Model versions (none → staging stages)
│
└── Workspace: enterprise-production
    ├── Project: cancer-detection
    ├── Stack: gcp-stack (Vertex AI, production)
    ├── Imported model versions (production stage)
    └── Production batch inference runs (INFERENCE LINEAGE)
```

**Why 2 workspaces (not 1, not 3)?**:
- **ZenML version upgrade isolation** - upgrade dev-staging first, test, then production
- **Full training lineage preserved** in dev-staging workspace
- **Inference lineage preserved** in production workspace
- **Single lineage break** at the staging → production boundary (not two breaks)
- **Clear workflow**: Dev → Staging (same workspace, full lineage) → Production (cross-workspace)

**Why NOT single workspace?**:
- ZenML version upgrades in single workspace affect all environments
- Production disruption risk during upgrades
- No isolation between development experimentation and production stability

**Why NOT 3 workspaces (one per environment)?**:
- Two lineage breaks instead of one
- More complex promotion workflow
- Staging validation loses connection to training lineage

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
- `hooks/` - Automatic enforcement (alerting, policy validation)
- `steps/` - Shared validation (data quality, model performance)
- `materializers/` - Enhanced artifact handling with metadata
- `stacks/terraform/` - Infrastructure as Code

**Pattern**: Data scientists import from governance, never modify it

```python
from governance.hooks import pipeline_success_hook
from governance.steps import validate_data_quality

@pipeline(on_success=pipeline_success_hook)  # Automatic governance
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
Model: breast_cancer_classifier
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

**Do** (environment-driven hooks):
```python
# Pipeline code stays clean - no hardcoded hooks
@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        tags=["use_case:breast_cancer", "owner_team:ml-platform"],
    ),
)
def training_pipeline():
    # Clean ML code
    pass

# run.py applies hooks based on environment
if environment == "staging" or environment == "production":
    from governance.hooks import (
        pipeline_governance_success_hook,  # Combines alerting + governance
        pipeline_failure_hook,
    )

    training_pipeline.with_options(
        on_success=pipeline_governance_success_hook,
        on_failure=pipeline_failure_hook,
    )(**kwargs)
else:
    # Local dev: no hooks, fast iteration
    training_pipeline(**kwargs)
```

**Don't** (governance mixed into ML code):
```python
@step
def train_model(data):
    model = fit_model(data)
    send_slack_notification(model)  # Governance mixed in - BAD!
    return model
```

**Why**:
- Pipeline code stays clean and testable
- Platform team controls governance without touching ML code
- Local dev is fast (no Slack spam)
- Staging/production get full governance

**Available Hooks**:
- `alerter_*_hook`, `pipeline_*_hook` - Send Slack/PagerDuty notifications
- `model_governance_hook` - Enforce required tags and naming conventions
- `monitoring_success_hook` - Send metrics to Datadog/Prometheus

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
- 2 workspaces for environment isolation (dev-staging + production)
- RBAC with custom roles (data-scientist, ml-engineer, platform-admin)
- Pipeline snapshots for immutable deployments
- Cross-workspace model promotion with metadata preservation
- ZenML version upgrade isolation

**Architecture**:
```
Organization: Enterprise MLOps
├── Workspace: enterprise-dev-staging (can upgrade ZenML freely)
│   ├── Project: cancer-detection
│   ├── Stack: dev-stack (local, fast iteration)
│   └── Stack: staging-stack (Vertex AI, production-like)
│
└── Workspace: enterprise-production (upgrade cautiously)
    ├── Project: cancer-detection
    └── Stack: gcp-stack (Vertex AI, production)
```

**Cross-Workspace Promotion**:
```bash
# Train in dev-staging
zenml login enterprise-dev-staging
python run.py --pipeline training

# Promote to production
python scripts/promote_cross_workspace.py \
  --model breast_cancer_classifier \
  --source-workspace enterprise-dev-staging \
  --dest-workspace enterprise-production
```

### For OSS Users (Secondary)

**Show**:
- 2 separate ZenML servers (one for dev-staging, one for production)
- Same project/stack names in each server
- Same cross-workspace promotion script
- Same GitOps workflows

**Architecture**:
```
ZenML Server: dev-staging.company.com
├── Project: cancer-detection
├── Stack: dev-stack
└── Stack: staging-stack

ZenML Server: production.company.com
├── Project: cancer-detection
└── Stack: gcp-stack
```

## What Works for Both

All core patterns work identically:
- ✅ Clean Python pipelines
- ✅ Hook-based governance
- ✅ Model Control Plane
- ✅ GitOps workflows
- ✅ Cross-workspace promotion (2 workspaces for Pro, 2 servers for OSS)
- ✅ Training lineage (in dev-staging workspace)
- ✅ Inference lineage (in production workspace)
- ✅ Metadata-based audit trails (preserved across workspaces)
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

### 3. Multi-Environment Promotion (Cross-Workspace)

**Show**: `scripts/promote_cross_workspace.py` and `.github/workflows/promote-to-production.yml`

**Point**: "This solves your #1 pain point AND ZenML version isolation. Train in dev-staging workspace with full lineage. Promote to production workspace with metadata preservation. Upgrade ZenML versions independently - test in dev-staging first, then production."

**Lineage Story**:
- Training lineage: Fully preserved in dev-staging workspace
- Production lineage: Inference runs show model → predictions
- Audit trail: Production model metadata links back to source workspace, version, git commit

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

### Issue: "Why 2 workspaces instead of 1 or 3?"

**Answer**: 2 workspaces (dev-staging + production) provides ZenML version upgrade isolation while preserving maximum lineage. Training lineage is fully preserved in dev-staging. Production has inference lineage plus metadata linking back to source. Only one lineage break at the staging→production boundary. Single workspace risks production disruption during upgrades; 3 workspaces creates two lineage breaks.

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
- Use 2 workspaces: dev-staging (full lineage) + production (inference lineage)
- Cross-workspace promotion preserves metadata for audit trails
- Same project name (`cancer-detection`) in both workspaces for consistency

## Files to Never Modify (Core Patterns)

These demonstrate key patterns - changing them breaks the demo:

- ✋ `src/pipelines/training.py` - Shows dynamic preprocessing pattern
- ✋ `src/pipelines/batch_inference.py` - Shows loading production model by stage
- ✋ `src/pipelines/champion_challenger.py` - Shows A/B model comparison pattern
- ✋ `src/pipelines/realtime_inference.py` - Shows Pipeline Deployments for serving
- ✋ `governance/hooks/alerting_hook.py` - Shows hook-based governance and notifications
- ✋ `scripts/promote_cross_workspace.py` - Shows cross-workspace promotion with metadata
- ✋ `.github/workflows/promote-to-production.yml` - Shows cross-workspace GitOps pattern

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
zenml login
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
3. **"Why 2 workspaces?"** → ZenML version upgrade isolation while preserving maximum lineage
4. **"Why Model Control Plane?"** → Single source of truth for audit trails
5. **"Why GitOps?"** → Production deployment pattern for enterprises
6. **"Why no pipeline conditionals?"** → ZenML compiles to DAG before execution
7. **"Why cross-workspace promotion?"** → Models validated in staging, then exported to production with metadata

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
