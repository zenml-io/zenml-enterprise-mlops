# ZenML Pro Features for Enterprise

This document outlines ZenML Pro features that address enterprise requirements for multi-tenancy, RBAC, and governance.

## Multi-Tenancy Architecture

### The Challenge

Enterprise organizations need to support multiple data science teams while maintaining:
- **Resource isolation** - Teams can't accidentally affect each other's work
- **Cost tracking** - Attribute compute costs to specific teams/projects
- **Access control** - Teams only see their own models and pipelines
- **Shared governance** - Platform team enforces standards across all teams

### ZenML Pro Solution: Projects

ZenML Pro provides **Projects** for logical isolation within a single workspace:

```
Workspace: "enterprise-ml"
├── Project: risk-models (Team A)
│   ├── Pipelines: credit_risk_training, fraud_detection
│   ├── Models: CreditRiskModel, FraudModel
│   └── Stacks: team-a-staging, team-a-production
│
├── Project: patient-outcomes (Team B)
│   ├── Pipelines: risk_training, outcome_prediction
│   ├── Models: RiskPredictor, OutcomeModel
│   └── Stacks: team-b-staging, team-b-production
│
└── Project: platform-shared (Platform Team)
    ├── Governance hooks and steps
    ├── Shared base images
    └── Cross-project visibility
```

### Key Benefits

| Feature | Benefit |
|---------|---------|
| **Project isolation** | Teams only see their own pipelines, models, and runs |
| **Shared stacks** | Platform team manages infrastructure, teams use it |
| **Cross-project visibility** | Platform admins can monitor all teams |
| **Cost attribution** | Pipeline runs tagged by project for billing |

## Role-Based Access Control (RBAC)

### Built-in Roles

ZenML Pro includes predefined roles:

| Role | Capabilities |
|------|--------------|
| **Viewer** | Read-only access to pipelines, models, artifacts |
| **Editor** | Run pipelines, create models, modify configurations |
| **Admin** | Full access including user management, stack configuration |

### Custom Roles for Enterprise

Create custom roles matching your organization:

```python
# Example: Data Scientist role
data_scientist_role = {
    "name": "data-scientist",
    "permissions": [
        "pipeline:run",
        "pipeline:read",
        "model:read",
        "model:create",
        "artifact:read",
        # Cannot modify stacks or promote to production
    ]
}

# Example: ML Engineer role
ml_engineer_role = {
    "name": "ml-engineer",
    "permissions": [
        "pipeline:*",
        "model:*",
        "stack:read",
        "model:promote:staging",
        # Cannot promote to production without approval
    ]
}

# Example: Platform Admin role
platform_admin_role = {
    "name": "platform-admin",
    "permissions": [
        "*",  # Full access
    ]
}
```

### RBAC for Model Promotion

Control who can promote models to each stage:

```yaml
# Promotion permissions by stage
staging:
  allowed_roles:
    - data-scientist
    - ml-engineer
    - platform-admin
  approval_required: false

production:
  allowed_roles:
    - ml-engineer
    - platform-admin
  approval_required: true
  min_approvers: 2
```

## Pipeline Snapshots (Immutable Deployments)

### What Are Snapshots?

Pipeline Snapshots capture the complete state of a pipeline at a point in time:
- Pipeline code and configuration
- Docker image specification
- Stack configuration
- Parameter defaults

### GitOps with Snapshots

```bash
# CI/CD creates snapshot on PR merge
python scripts/build_snapshot.py \
    --environment staging \
    --stack gcp-staging \
    --git-sha $GITHUB_SHA

# Snapshot name: STG_risk_model_abc1234
# This snapshot is immutable - same code runs every time
```

### Benefits for Enterprise

1. **Reproducibility** - Run the exact same pipeline months later
2. **Audit trail** - Know exactly what code produced each model
3. **Rollback** - Revert to previous snapshot if issues arise
4. **Approval workflows** - Create snapshot, get approval, then run

## Audit Logging

### What's Logged

ZenML Pro maintains detailed audit logs:

| Event | Details Captured |
|-------|------------------|
| Pipeline run | Who triggered, when, parameters, stack used |
| Model promotion | Who promoted, from/to stage, validation results |
| Access events | Who viewed/modified resources |
| Configuration changes | Stack modifications, role assignments |

### Retention

- **Standard**: 90 days
- **Enterprise**: Configurable up to 7 years (HIPAA/regulatory compliance)

### Export for Compliance

```python
from zenml.client import Client

client = Client()

# Export audit logs for compliance review
audit_logs = client.list_audit_logs(
    start_date="2024-01-01",
    end_date="2024-12-31",
    event_types=["model_promotion", "pipeline_run"],
    project="patient-outcomes",
)

# Export to your SIEM or compliance system
for log in audit_logs:
    send_to_compliance_system(log)
```

## Comparison: OSS vs Pro

| Feature | ZenML OSS | ZenML Pro |
|---------|-----------|-----------|
| Multi-environment stacks | ✅ | ✅ |
| Model Control Plane | ✅ | ✅ |
| GitOps workflows | ✅ | ✅ |
| Hook-based governance | ✅ | ✅ |
| **Projects (multi-tenancy)** | ❌ | ✅ |
| **RBAC** | ❌ | ✅ |
| **Pipeline Snapshots** | ❌ | ✅ |
| **Audit logging** | Basic | Extended |
| **SSO/SAML** | ❌ | ✅ |
| **Support SLA** | Community | Enterprise |

## Architecture for HCA's Requirements

Based on HCA's hub-and-spoke architecture needs, we recommend a **2-Workspace Architecture** that provides ZenML version upgrade isolation while maintaining promotion workflows.

### 2-Workspace Architecture (Recommended)

```
Organization: Enterprise MLOps
│
├── Workspace: enterprise-dev-staging
│   │   # Development + Staging (full lineage)
│   │
│   ├── Project: cancer-detection
│   │   ├── Stack: dev-stack (local orchestrator, fast iteration)
│   │   ├── Stack: staging-stack (Vertex AI, production-like testing)
│   │   ├── Training pipeline runs (FULL LINEAGE)
│   │   ├── Model versions (none → staging stages)
│   │   └── Test batch inference runs
│   │
│   └── Stacks registered to GCP:
│       ├── dev-stack → local orchestrator
│       └── staging-stack → Vertex AI (staging resources)
│
└── Workspace: enterprise-production
    │   # Production only (imported models, inference lineage)
    │
    ├── Project: cancer-detection
    │   ├── Stack: gcp-stack (Vertex AI, production)
    │   ├── Imported model versions (production stage)
    │   ├── Batch inference pipeline runs
    │   └── Real-time inference deployments
    │
    └── Cross-workspace lineage via metadata:
        └── Links back to source workspace, version, pipeline run
```

### Why 2 Workspaces?

| Benefit | How It Works |
|---------|--------------|
| **ZenML Version Isolation** | Upgrade dev-staging first, test thoroughly, then production |
| **Full Training Lineage** | All training artifacts and lineage preserved in dev-staging |
| **Production Stability** | Production workspace isolated from development changes |
| **Cross-Workspace Promotion** | Export/import with rich metadata preserves audit trail |

### Cross-Workspace Model Promotion

Models promote from dev-staging to production via a shared GCS bucket:

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitOps Flow (GitHub Actions)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┴──────────────────┐
           ▼                                      ▼
┌─────────────────────────┐            ┌─────────────────────────┐
│  enterprise-dev-staging │            │  enterprise-production  │
│                         │            │                         │
│  Training Pipeline      │            │  Import Pipeline        │
│  └─> Model v1          │            │  └─> Model v1          │
│      (staging stage)    │            │      (production stage) │
│                         │   Export   │                         │
│  Full Lineage:          │ ────────> │  Metadata Links:        │
│  - Data artifacts       │   via     │  - Source workspace     │
│  - Feature pipeline     │   shared  │  - Source version       │
│  - Training metrics     │   GCS     │  - Pipeline run URL     │
│  - Git commit           │  bucket   │  - All metrics          │
└─────────────────────────┘            └─────────────────────────┘
```

### Promotion Script

```bash
# Export from dev-staging (in GitHub Actions or manually)
python scripts/promote_cross_workspace.py \
    --model breast_cancer_classifier \
    --source-workspace enterprise-dev-staging \
    --source-stage staging \
    --export-only

# Import to production (requires approval)
python scripts/promote_cross_workspace.py \
    --model breast_cancer_classifier \
    --dest-workspace enterprise-production \
    --import-from gs://zenml-core-model-exchange/exports/... \
    --dest-stage production
```

### GCP Infrastructure

Single GCP project with label-based cost tracking:

```
GCP Project: zenml-core
│
├── Dev-Staging Resources (label: environment=dev-staging)
│   ├── GCS: zenml-dev-staging-artifacts
│   ├── Artifact Registry: zenml-dev-staging
│   └── Vertex AI Pipelines (staging workloads)
│
├── Production Resources (label: environment=production)
│   ├── GCS: zenml-production-artifacts
│   ├── Artifact Registry: zenml-production
│   └── Vertex AI Pipelines (production workloads)
│
└── Shared Resources (label: purpose=cross-workspace)
    └── GCS: zenml-core-model-exchange
        └── Used for model export/import between workspaces
```

### ZenML Pro Features Used

| Feature | How We Use It |
|---------|---------------|
| **Multiple Workspaces** | Separate dev-staging and production |
| **Projects** | Team isolation within each workspace |
| **Pipeline Snapshots** | Immutable deployments in production |
| **RBAC** | Control who can promote to production |
| **Audit Logs** | Track all promotions and deployments |

### Alternative: Single Workspace (Simpler, Less Isolation)

For teams that don't need ZenML version isolation:

```
ZenML Pro Workspace: enterprise-ml
├── Project: cancer-detection
│   ├── Stack: dev-stack (local)
│   ├── Stack: staging-stack (Vertex AI staging)
│   └── Stack: gcp-stack (Vertex AI production)
│
└── Model promotion via stages (within workspace):
    └── none → staging → production
```

**Trade-off**: Simpler promotion, but ZenML upgrades affect all environments simultaneously.

## Next Steps

1. **Trial ZenML Pro** - Request access at https://zenml.io/pro
2. **Architecture review** - Schedule call to discuss your specific topology
3. **POC** - Run this template against your GCP infrastructure

## Questions?

Contact your ZenML solutions engineer or email enterprise@zenml.io.
