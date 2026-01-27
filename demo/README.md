# Enterprise MLOps Demo

Interactive demo showcasing the complete model lifecycle with 2-workspace architecture, mirroring the GitHub Actions CI/CD flow.

## Quick Start

```bash
# Run the full demo (interactive, auto-detects workspace mode)
python demo/run_demo.py

# Run specific chapter
python demo/run_demo.py --chapter 2

# Auto-advance without prompts
python demo/run_demo.py --auto

# List all chapters
python demo/run_demo.py --list

# Force single-workspace mode
python demo/run_demo.py --workspace-mode single-workspace
```

## Prerequisites

```bash
pip install -r requirements.txt
zenml init
```

### 2-Workspace Mode (Recommended)

Create a `.env` file in the project root:

```env
ZENML_DEV_STAGING_URL=https://enterprise-dev-staging.zenml.io
ZENML_DEV_STAGING_API_KEY=your-dev-staging-api-key
ZENML_PRODUCTION_URL=https://enterprise-production.zenml.io
ZENML_PRODUCTION_API_KEY=your-production-api-key
```

The demo auto-detects 2-workspace mode when both sets of credentials are present.

### Stacks Required

In the dev-staging workspace:
- `default` — Local orchestrator for fast iteration (Ch1)
- `staging-stack` — Vertex AI orchestrator, GCS artifacts (Ch2)

In the production workspace:
- `default` or `gcp-stack` — For batch inference (Ch6)

## Demo Flow

```
  enterprise-dev-staging                    enterprise-production
  ┌───────────────────────────────┐        ┌─────────────────────────────┐
  │ Ch1: Train locally (dev)      │        │                             │
  │ Ch2: PR → staging-stack       │        │                             │
  │ Ch3: Champion vs Challenger   │        │                             │
  │ Ch4: Promote to staging       │        │                             │
  │ Ch5: Export model ────────────────────▶│ Ch5: Import model           │
  │                               │        │      (set to production)    │
  │                               │        │ Ch6: Batch inference        │
  └───────────────────────────────┘        └─────────────────────────────┘
```

## Chapters

| # | Chapter | Stack | What It Demonstrates |
|---|---------|-------|---------------------|
| 1 | **Train Locally** | default (local) | Clean Python, fast iteration, automatic governance |
| 2 | **Simulate PR → Staging Training** | staging-stack (Vertex AI) | CI/CD training, production-like infra, staging config |
| 3 | **Champion vs Challenger** | default | New model vs current staging, safe rollout validation |
| 4 | **Promote to Staging** | — | Validation gates (70% threshold), MCP exploration |
| 5 | **Promote to Production** | — | Cross-workspace export/import with metadata |
| 6 | **Batch Inference** | production workspace | Load by stage, scheduled predictions, lineage |

## GitHub Actions Alignment

The demo chapters directly mirror the CI/CD workflows:

| Workflow | Chapter | Trigger |
|----------|---------|---------|
| `train-staging.yml` | Ch1 + Ch2 | PR to main (trains on staging-stack) |
| `test-batch-inference.yml` | Ch3 | After training completes (validates model) |
| PR merge | Ch4 | Merge PR (promotes to staging) |
| `promote-to-production.yml` | Ch5 | GitHub Release (cross-workspace export/import) |
| `batch-inference.yml` | Ch6 | Daily cron (production workspace) |

## Key Talking Points

### Chapter 1: Fast Local Iteration
> "Data scientists iterate locally with instant feedback. Same pipeline code, local stack. `@step` and `@pipeline` — no wrappers."

### Chapter 2: CI/CD Staging Training
> "Push code, open PR, staging training runs automatically on Vertex AI. Same pipeline, different stack. That's the power of ZenML's stack abstraction."

### Chapter 3: Safe Rollouts
> "Before promoting, compare new model against current staging. Agreement rate, probability diff, data-driven recommendation."

### Chapter 4: Governed Promotion
> "Platform team sets the gates — 70% accuracy, precision, recall. Model promoted to staging only if it passes. Full audit trail."

### Chapter 5: Cross-Workspace Deployment
> "This solves your #1 pain point: multi-environment promotion. Export from dev-staging, import into production. Full metadata preserved. ZenML version upgrade isolation."

### Chapter 6: Production Inference
> "Batch inference in production workspace. Model loaded by stage. Inference lineage preserved here, training lineage preserved in dev-staging."

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No model found" | Run Chapter 1 first to train a model |
| "staging-stack not found" | Check `zenml stack list` in dev-staging workspace |
| "Missing credentials" | Set env vars in `.env` |
| "Cross-workspace failed" | Check GCS bucket access and both workspace credentials |
| Vertex AI timeout | Staging training takes longer than local — this is expected |
