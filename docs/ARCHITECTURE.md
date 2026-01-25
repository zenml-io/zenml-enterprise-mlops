# Architecture & Organization Guide

> **Target Audience**: This guide is primarily for **ZenML Pro** users building enterprise MLOps platforms. OSS users can follow the single-team patterns.

This document describes the architectural decisions, organization patterns, and best practices for building production-ready MLOps systems with ZenML.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [Multi-Tenancy & Organization](#multi-tenancy--organization)
- [Repository Structure](#repository-structure)
- [Component Responsibilities](#component-responsibilities)
- [Stack Organization](#stack-organization)
- [Access Control & RBAC](#access-control--rbac)
- [Data Flow & Workflows](#data-flow--workflows)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Technology Stack](#technology-stack)
- [Design Trade-offs](#design-trade-offs)
- [Best Practices](#best-practices)

## Overview

This template implements a **production-ready MLOps architecture** designed for regulated industries and enterprise teams. The architecture separates concerns between platform governance and developer productivity while maintaining complete audit trails and lineage tracking.

### Key Architectural Goals

1. **Clean Separation of Concerns**: Platform team controls governance, data scientists write pure Python
2. **Multi-Environment Promotion**: Smooth transition from dev → staging → production
3. **GitOps Integration**: All deployments triggered by Git events
4. **Complete Auditability**: Full lineage from prediction back to source data and code
5. **Cloud-Agnostic**: Works with GCP, AWS, Azure, or on-premise

### Who This Template Is For

- **Primary**: **ZenML Pro** users building enterprise MLOps platforms for multiple teams/departments
- **Secondary**: **ZenML OSS** users can follow single-team patterns - all core features work with OSS

## Design Principles

### 1. Platform as a Product

The platform team treats the MLOps infrastructure as a product:
- **Governance hooks** enforce standards automatically
- **Base Docker images** provide curated dependencies
- **Shared validation steps** ensure quality gates
- **Stack configurations** control infrastructure

Data scientists consume this platform without needing to understand the internals.

### 2. Developer Experience First

Data scientists write **pure Python** with no wrapper code:

```python
@step
def train_model(data: pd.DataFrame) -> Annotated[ClassifierMixin, "model"]:
    """Just train the model - no wrappers, no boilerplate"""
    model = RandomForestClassifier()
    model.fit(data[features], data[target])
    return model
```

All governance (logging, validation, compliance) happens transparently via hooks.

### 3. Immutable Deployments

Production deployments use **pipeline snapshots** (ZenML Pro):
- Create immutable pipeline definition in staging
- Test and validate
- Promote snapshot to production (not code!)
- Ensures exact reproducibility

### 4. Defense in Depth

Multiple layers of validation and security:
1. **Data validation** - Check quality before training
2. **Model validation** - Ensure performance thresholds
3. **Promotion validation** - Verify before moving to production
4. **Runtime validation** - Monitor in production

## Multi-Tenancy & Organization

### OSS vs Pro Capabilities

| Feature | OSS | Pro |
|---------|-----|-----|
| **Projects** | 1 (single) | Multiple |
| **Workspaces** | ❌ | ✅ (with caveats) |
| **RBAC** | Basic (GitHub-based) | Fine-grained roles |
| **Pipeline Snapshots** | ❌ | ✅ |
| **Audit Logs** | Basic | Comprehensive |
| **SSO/SAML** | ❌ | ✅ |

### Single Workspace Architecture (Recommended)

For most enterprises, use a **single workspace with multiple projects** (Pro) or **single project with environment stacks** (OSS):

```
ZenML Instance
└── Workspace: "enterprise-ml"
    ├── Project: "healthcare-models" (Pro) / "default" (OSS)
    │   ├── Stacks: dev, staging, production
    │   ├── Models: patient_readmission_predictor
    │   └── Pipelines: training, batch_inference
    │
    ├── Project: "fraud-detection" (Pro only)
    │   ├── Stacks: dev, staging, production
    │   └── Models: transaction_classifier
    │
    └── Project: "platform-shared" (Pro only)
        └── Governance: hooks, validation steps, base images
```

**Key Architectural Decisions**:

1. **Single Workspace** (not multiple workspaces)
   - Enables cross-project model visibility
   - Supports model promotion workflows (workspace isolation would break this)
   - Allows shared infrastructure and governance components
   - Matches the multi-environment promotion pattern in this template

2. **Resource Isolation via Stacks** (not ZenML projects/workspaces)
   - Each environment (dev/staging/prod) uses separate GCP/AWS projects
   - Stack isolation provides infrastructure boundaries
   - Credential separation at cloud provider level
   - Works identically for OSS and Pro

3. **Projects for Team Isolation** (Pro only)
   - Separate projects per team/department
   - RBAC controls access within projects
   - Shared platform components in dedicated project
   - OSS users use single "default" project with environment stacks

### Design Rationale

**Why single workspace?**
- Solves multi-environment model promotion (HCA's #1 pain point)
- Platform team needs visibility across all teams
- Shared governance components (hooks, base images, validation steps)
- Simpler credential and access management

**Why not multiple workspaces?**
- Workspaces create physical isolation
- Models cannot be promoted across workspaces
- Breaks the dev → staging → production workflow
- Only use multiple workspaces for hard regulatory boundaries (e.g., HIPAA vs non-HIPAA data)

### Basic Setup (OSS & Pro Single-Team)

```bash
# Install ZenML
pip install "zenml[server]>=0.92.0"

# Initialize
zenml init

# Start local server (OSS) or connect to Pro
zenml up  # OSS
zenml connect --url https://your-org.zenml.io  # Pro

# Configure environment stacks
zenml stack register local-dev --orchestrator local --artifact-store local
zenml stack register staging --orchestrator vertex-staging --artifact-store gcs-staging
zenml stack register production --orchestrator vertex-production --artifact-store gcs-production
```

### Advanced Multi-Team Setup (Pro Only)

```bash
# Create projects per team
zenml project create healthcare-models --description "Healthcare ML models"
zenml project create fraud-detection --description "Fraud detection models"
zenml project create platform-shared --description "Shared governance components"

# Create RBAC roles
zenml role create data-scientist --permissions "read:model,write:model,execute:pipeline"
zenml role create ml-engineer --permissions "read:stack,write:stack,admin:pipeline"
zenml role create platform-admin --permissions "admin:*"

# Assign users to projects
zenml project assign-user healthcare-models --user alice@company.com --role data-scientist
zenml project assign-user platform-shared --user bob@company.com --role platform-admin
```

## Repository Structure

```
zenml-enterprise-mlops/
├── governance/               # Platform team owns this
│   ├── hooks/               # Governance enforcement
│   │   ├── mlflow_hook.py           # MLflow auto-logging
│   │   └── compliance_hook.py       # Audit trail
│   ├── steps/               # Shared validation steps
│   │   ├── validate_data_quality.py
│   │   └── validate_model_performance.py
│   └── stacks/              # Infrastructure config
│       └── terraform/               # IaC for cloud resources
│
├── src/                     # Data scientists own this
│   ├── pipelines/          # ML workflows
│   │   ├── training.py
│   │   └── batch_inference.py
│   ├── steps/              # Custom ML logic
│   │   ├── data_loader.py
│   │   ├── feature_engineering.py
│   │   ├── model_trainer.py
│   │   └── model_evaluator.py
│   └── utils/              # Helper functions
│       └── mlflow_utils.py
│
├── configs/                 # Configuration files
│   ├── model_config.yaml
│   └── pipeline_config.yaml
│
├── scripts/                 # Automation utilities
│   ├── promote_model.py
│   └── build_snapshot.py
│
├── .github/workflows/       # GitOps automation
│   ├── train-on-pr.yml
│   ├── promote-production.yml
│   └── schedule-batch-inference.yml
│
├── notebooks/               # Exploratory analysis
├── .dockerignore            # Docker build optimization
├── .gitignore               # Version control
├── requirements.txt         # Dependencies
└── .zen/                    # ZenML source root
```

### Key Patterns

1. **Separation of Concerns**: `governance/` (platform) vs `src/` (ML code)
2. **Shared Components**: Platform team maintains reusable governance in `governance/`
3. **GitOps Integration**: All automation in `.github/workflows/`
4. **Infrastructure as Code**: Terraform configs in `governance/stacks/terraform/`

## Component Responsibilities

### Platform Team

**Owns**: `governance/`, `.github/workflows/`, Docker images, stack configs

**Responsibilities**:
- Define and maintain base Docker images
- Implement governance hooks
- Create shared validation steps
- Configure and manage stacks
- Set up GitOps workflows
- Monitor infrastructure health
- Manage secrets and credentials
- Enforce security policies

**Does NOT**: Write ML code, define features, tune hyperparameters

### Data Science Team

**Owns**: `src/`, `configs/`, `notebooks/`

**Responsibilities**:
- Develop ML pipelines and steps
- Define features and transformations
- Train and evaluate models
- Tune hyperparameters
- Write documentation
- Test pipelines locally
- Create PRs for new models

**Does NOT**: Manage infrastructure, configure stacks, handle secrets, deploy to production

### MLOps/Platform Engineering Team

**Owns**: All infrastructure, CI/CD, production deployments

**Responsibilities**:
- Approve production promotions
- Monitor model performance
- Respond to alerts
- Manage incidents
- Perform rollbacks if needed
- Capacity planning
- Cost optimization

## Stack Organization

### Stack Hierarchy

```
Stacks
├── Local Development
│   ├── local-dev (OSS: default, Pro: per-project)
│   └── Local orchestrator + local artifact store
│
├── Cloud Development
│   ├── {project}-dev (Pro) or dev (OSS)
│   └── Cloud orchestrator + cloud storage (isolated by GCP project)
│
├── Staging
│   ├── {project}-staging (Pro) or staging (OSS)
│   └── Cloud orchestrator + cloud storage + experiment tracker
│
└── Production
    ├── {project}-prod (Pro) or production (OSS)
    └── Cloud orchestrator + cloud storage + experiment tracker + model registry
```

### Naming Conventions

**Stacks**: `{project}-{environment}` (Pro) or `{environment}` (OSS)
- Examples: `healthcare-staging`, `fraud-production` (Pro)
- Examples: `dev`, `staging`, `production` (OSS)

**Models**: `{purpose}_{type}`
- Examples: `patient_readmission_predictor`, `diagnosis_classifier`

**Pipelines**: `{purpose}_pipeline`
- Examples: `training_pipeline`, `batch_inference_pipeline`

### Resource Isolation

Each environment uses separate cloud projects:
```
GCP Projects:
- my-company-ml-dev       (development)
- my-company-ml-staging   (staging)
- my-company-ml-prod      (production)
```

This provides:
- Infrastructure boundaries
- Credential separation
- Cost tracking per environment
- Independent scaling

## Access Control & RBAC

### ZenML Pro RBAC

**Common Role Patterns**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| `data-scientist` | Read/write models & pipelines in project | ML developers |
| `ml-engineer` | Read/write + execute pipelines | MLOps engineers |
| `platform-admin` | Admin on stacks, read-only on models | Platform team |
| `auditor` | Read-only across all projects | Compliance team |

**Permission Matrix**:

| Action | Data Scientist | ML Engineer | Platform Admin | Auditor |
|--------|----------------|-------------|----------------|---------|
| View models | ✅ | ✅ | ✅ | ✅ |
| Create models | ✅ | ✅ | ✅ | ❌ |
| Promote to staging | ✅ | ✅ | ✅ | ❌ |
| Promote to production | ❌ | ✅ | ✅ | ❌ |
| View stacks | ✅ | ✅ | ✅ | ✅ |
| Modify stacks | ❌ | ✅ | ✅ | ❌ |
| Execute pipelines | ✅ | ✅ | ✅ | ❌ |
| Delete resources | ❌ | ❌ | ✅ | ❌ |

### OSS Access Control

OSS doesn't have fine-grained RBAC, but you can implement controls via:

1. **Repository access**: Limit who can merge to main/staging branches
2. **Stack credentials**: Separate credentials per environment
3. **GitHub Actions**: Approval gates for production promotion
4. **Custom validation**: Add permission checks in promotion scripts

## Data Flow & Workflows

### Hook-Based Governance

Platform team enforces governance through hooks:

```python
@pipeline(
    on_success=mlflow_success_hook,      # Log to MLflow
    on_failure=compliance_failure_hook,  # Alert on failure
)
def training_pipeline():
    # Developer code remains clean
    pass
```

Hooks run automatically and transparently:
- **MLflow hook**: Logs metrics, parameters, models
- **Monitoring hook**: Sends telemetry to observability platform
- **Compliance hook**: Ensures audit trail for failures

### Model Control Plane

ZenML's Model Control Plane serves as the **single source of truth**:

```
Model: patient_readmission_predictor
├── Version 1 (archived)
├── Version 2 (staging)
└── Version 3 (production) ← Active version
    ├── Artifacts: model, scaler, metrics
    ├── Metadata: git_commit, accuracy, f1_score
    ├── Pipeline Run: training_run_abc123
    └── Lineage: data → features → model → predictions
```

All components reference the Model Control Plane:
- Training pipelines register new versions
- Promotion script changes stages
- Batch inference loads by stage (e.g., "production")
- Complete lineage preserved across environments

### Training Flow

```
1. Developer creates feature branch
2. Writes pipeline code in src/
3. Tests locally with local-dev stack
4. Creates PR to staging branch
5. GitHub Actions triggers:
   ├─ Build pipeline snapshot (Pro)
   └─ Run training pipeline
6. Results logged to Model Control Plane
7. PR review and merge
```

### Promotion Flow

```
1. Model validated in staging
2. Create GitHub release (e.g., v1.0.0)
3. GitHub Actions triggers:
   ├─ Run promotion script
   ├─ Validate model meets thresholds
   └─ Set model stage to "production"
4. Batch inference picks up new model automatically
```

### Batch Inference Flow

```
1. Scheduled daily (2 AM UTC)
2. Load "production" model by stage
3. Fetch new data from source
4. Generate predictions
5. Store results in artifact store
6. Log metadata to Model Control Plane
7. Send monitoring metrics
```

## Security Architecture

### Secrets Management

- All secrets stored in ZenML secrets backend
- Never committed to Git
- Rotated regularly
- Access controlled by RBAC (Pro) or stack credentials (OSS)

### Access Control

```
Development:
- Data Scientists: Read/write to staging
- Platform Team: Admin access

Production:
- Data Scientists: Read-only
- MLOps Team: Read/write with approval
- Platform Team: Admin access
```

### Audit Trail

Every action is logged:
- Pipeline executions
- Model promotions
- Predictions (sampled)
- Infrastructure changes
- Access events

Logs retained for compliance (HIPAA: 7 years, GDPR: as needed).

### Network Security

- VPC peering for cloud resources
- Private endpoints for databases
- TLS for all external communication
- IAM roles with least privilege

## Deployment Architecture

### Multi-Environment Strategy

```
┌─────────────┐
│ Development │  ← Data scientists iterate
├─────────────┤
│   Staging   │  ← Automated testing (CI/CD)
├─────────────┤
│ Production  │  ← Manual approval required
└─────────────┘
```

Each environment has:
- Isolated infrastructure
- Separate credentials
- Different performance thresholds
- Environment-specific configurations

### High Availability (Production)

- Multiple replicas for serving
- Auto-scaling based on load
- Health checks and readiness probes
- Circuit breakers for failure handling
- Multi-region (optional)

### Disaster Recovery

- Daily backups of Model Control Plane
- Artifact store versioning enabled
- Pipeline snapshots for rollback (Pro)
- Documented incident response procedures

## Technology Stack

### Core Components

- **ZenML**: Pipeline orchestration and Model Control Plane
- **MLflow**: Experiment tracking and model registry
- **Scikit-learn**: ML framework (example)
- **Docker**: Containerization
- **GitHub Actions**: CI/CD automation
- **Terraform**: Infrastructure as Code

### Cloud Components (Environment-Specific)

- **Orchestrator**: Vertex AI, Kubernetes, Airflow, Databricks
- **Artifact Store**: GCS, S3, Azure Blob
- **Container Registry**: GCR, ECR, ACR
- **Secrets Manager**: GCP Secret Manager, AWS Secrets Manager, Azure Key Vault
- **Log Store**: OTEL, Datadog, Artifact Log Store (default)

### Monitoring & Observability

- **MLflow**: Experiment and model tracking
- **Evidently**: Data drift detection
- **Custom hooks**: Telemetry and alerts
- **OTEL/Datadog**: (Optional) Centralized logging
- **Prometheus/Grafana**: (Optional) Infrastructure metrics

## Design Trade-offs

### Why Hooks Instead of Decorators?

**Decision**: Use `@pipeline(on_success=hook)` instead of step decorators

**Rationale**:
- Platform team controls governance without touching ML code
- Data scientists write pure Python
- Hooks can be added/removed without changing pipelines
- Easier to test and maintain

### Why Model Control Plane Instead of Direct Registry?

**Decision**: Use ZenML Model Control Plane as single source of truth

**Rationale**:
- Unified interface across all tools (MLflow, S3, etc.)
- Complete lineage tracking built-in
- Stage-based deployment (staging/production)
- Metadata and artifact co-location
- Cloud-agnostic abstraction

### Why Pipeline Snapshots?

**Decision**: Use snapshots for production deployments (Pro feature)

**Rationale**:
- Immutable pipeline definitions
- Exact reproducibility
- GitOps-style deployment
- Rollback capability
- Separation between code and deployment

### Why Multi-Environment Instead of Canary?

**Decision**: Promote models through environments rather than canary deployments

**Rationale**:
- Simpler for most enterprise use cases
- Clear approval gates
- Full testing in staging before production
- Easier rollback (change stage back)
- Can still add canary within production environment

## Best Practices

### 1. Start Simple, Scale Gradually

**Phase 1: Single Team** (OSS or Pro)
- One project (or default project for OSS)
- Environment stacks (dev, staging, prod)
- Basic governance hooks
- GitOps for promotion

**Phase 2: Multiple Teams** (Pro)
- Create projects per team/department
- Implement RBAC
- Shared platform components
- Cross-team standards

**Phase 3: Enterprise Scale** (Pro)
- Advanced monitoring and alerting
- Pipeline snapshots for immutable deployments
- Multi-region deployments
- Automated retraining

### 2. Organize by Business Domain

**Good** (domain-driven):
```
Projects:
- healthcare-models (clinical ML)
- operations-models (hospital operations)
- research-models (clinical trials)
```

**Bad** (technology-driven):
```
Projects:
- pytorch-models
- sklearn-models
- tensorflow-models
```

### 3. Establish Naming Conventions Early

- **Stacks**: `{project}-{environment}` (Pro) or `{environment}` (OSS)
- **Models**: `{purpose}_{type}`
- **Pipelines**: `{purpose}_pipeline`
- **Artifacts**: Use `ArtifactConfig` with descriptive names

### 4. Separate Governance from ML Logic

**Do**:
```python
# ML team writes clean code
@pipeline
def training_pipeline():
    data = load_data()
    model = train_model(data)
    return model

# Platform team adds governance via hooks
training_pipeline = training_pipeline.with_options(
    on_success=mlflow_success_hook,
    on_failure=compliance_failure_hook,
)
```

**Don't**:
```python
# Mixing governance into ML logic
@step
def train_model(data):
    model = fit_model(data)
    log_to_mlflow(model)  # Governance mixed in (bad!)
    send_compliance_event(model)
    return model
```

### 5. Use Model Control Plane as Single Source of Truth

All systems reference the Model Control Plane:
- Training pipeline registers new versions
- Promotion script updates stages
- Batch inference loads by stage
- Monitoring tracks model by ID
- Audit queries lineage from Model Control Plane

### 6. Automate Everything

- **CI/CD**: GitHub Actions for training, promotion, deployment
- **Testing**: Automated pipeline tests on PR
- **Monitoring**: Automatic drift detection
- **Retraining**: Trigger retraining on drift or schedule
- **Promotion**: Automated validation gates

### 7. Implement Progressive Rollout

```
Development → Staging → Canary (10%) → Production (100%)
```

Even with environment-based promotion, you can implement canary deployments within production.

### 8. Document Your Conventions

Create a team playbook documenting:
- Naming conventions
- Branching strategy
- Promotion criteria
- Rollback procedures
- Incident response
- Contact information

## Migration Path: OSS → Pro

When upgrading from OSS to Pro:

### 1. Plan Your Project Structure

```
Before (OSS):
└── default project
    ├── All models
    └── All pipelines

After (Pro):
├── Project: team-a
│   ├── Team A models
│   └── Team A pipelines
├── Project: team-b
│   ├── Team B models
│   └── Team B pipelines
└── Project: platform-shared
    ├── Governance
    └── Shared components
```

### 2. Migrate Incrementally

1. **Week 1**: Connect to Pro, keep single project
2. **Week 2**: Create new projects, test isolation
3. **Week 3**: Migrate one team as pilot
4. **Week 4**: Migrate remaining teams
5. **Week 5**: Implement RBAC and cleanup

### 3. Preserve Lineage

Models migrated to new projects maintain their history:
- Version numbers preserved
- Lineage links intact
- Metadata retained

## Future Enhancements

Potential architectural improvements:

1. **Real-time Serving**: Add model deployer component (Seldon/KServe)
2. **Feature Store**: Integrate Feast for feature management
3. **Advanced Monitoring**: Add dedicated monitoring stack (Prometheus/Grafana/OTEL)
4. **Multi-Region**: Deploy across multiple regions for HA
5. **A/B Testing**: Implement champion/challenger patterns
6. **Auto-Retraining**: Trigger retraining on drift detection

---

## References

### Internal Documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - For data scientists
- [Platform Guide](PLATFORM_GUIDE.md) - For platform engineers

### External Documentation
- [ZenML Documentation](https://docs.zenml.io)
- [Model Control Plane Guide](https://docs.zenml.io/user-guide/production-guide/model-management-metrics)
- [Pipeline Snapshots](https://docs.zenml.io/user-guide/production-guide/deploying-zenml/best-practices)
- [Enterprise Best Practices](https://docs.zenml.io/user-guide/production-guide)
- [ZenML Pro Setup](https://docs.zenml.io/how-to/setup-zenml/setup-zenml-pro)
- [ZenML Pro RBAC](https://docs.zenml.io/pro/access-management/roles)
