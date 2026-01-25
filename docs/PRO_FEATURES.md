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
│   ├── Pipelines: readmission_training, mortality_prediction
│   ├── Models: ReadmissionPredictor, MortalityModel
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

# Snapshot name: STG_readmission_model_abc1234
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

Based on HCA's hub-and-spoke architecture needs:

### Option 1: Single Workspace with Projects (Recommended)

```
ZenML Pro Workspace
├── Project: hca-platform (Platform Team)
│   ├── Shared governance components
│   ├── Base Docker images
│   └── Cross-project monitoring
│
├── Project: hca-risk-models (Risk Team)
│   └── Uses platform stacks, isolated models
│
├── Project: hca-patient-outcomes (Outcomes Team)
│   └── Uses platform stacks, isolated models
│
└── Stacks (shared across projects):
    ├── gcp-staging (Vertex AI + GCS in staging project)
    └── gcp-production (Vertex AI + GCS in prod project)
```

**Benefits**:
- Model promotion works across projects (same workspace)
- Platform team has visibility into all projects
- Teams isolated via RBAC
- Single source of truth for models

### Option 2: Consolidated GCP Projects

If consolidating from hub-and-spoke to central projects:

```
GCP Projects:
├── hca-ml-staging
│   └── ZenML Stack: gcp-staging
│       ├── Vertex AI Pipelines (orchestrator)
│       ├── GCS bucket (artifacts)
│       └── Artifact Registry (containers)
│
└── hca-ml-production
    └── ZenML Stack: gcp-production
        ├── Vertex AI Pipelines (orchestrator)
        ├── GCS bucket (artifacts)
        └── Artifact Registry (containers)

ZenML Pro provides:
- RBAC for team isolation within shared GCP projects
- Cost attribution via pipeline/project tags
- Audit trail for compliance
```

## Next Steps

1. **Trial ZenML Pro** - Request access at https://zenml.io/pro
2. **Architecture review** - Schedule call to discuss your specific topology
3. **POC** - Run this template against your GCP infrastructure

## Questions?

Contact your ZenML solutions engineer or email enterprise@zenml.io.
