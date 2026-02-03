# Demo & Sales Guide

This document contains demo talking points, Pro vs OSS positioning, and success metrics for enterprise customer demos.

> **For technical demo execution**, see `demo/README.md`.
> **For customer-specific scripts**, see `demo/enterprise-stack/TALKING_POINTS.md`.

---

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

---

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

---

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

---

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

---

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

---

## See Also

- `demo/README.md` - Technical demo setup and execution
- `demo/enterprise-stack/TALKING_POINTS.md` - Customer-specific sales scripts
- `docs/ARCHITECTURE.md` - Complete architecture guide
- `docs/PRO_FEATURES.md` - ZenML Pro-specific features
