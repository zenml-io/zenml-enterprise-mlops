# Enterprise MLOps Demo

Interactive demo showcasing the complete model lifecycle and promotion flow.

## Quick Start

```bash
# Run the full demo (interactive)
python demo/run_demo.py

# Run specific chapter
python demo/run_demo.py --chapter 2

# Auto-advance without prompts
python demo/run_demo.py --auto

# List all chapters
python demo/run_demo.py --list
```

## Chapters

| # | Chapter | What It Demonstrates |
|---|---------|---------------------|
| 1 | **Train a Model** | Clean Python code, automatic governance via hooks |
| 2 | **Model Control Plane** | Single source of truth, lineage, audit trail |
| 3 | **Promote to Staging** | Validation gates (70% threshold), GitOps pattern |
| 4 | **Champion vs Challenger** | A/B comparison, safe rollout decision |
| 5 | **Promote to Production** | Higher bar (80%), release-triggered workflow |
| 6 | **Batch Inference** | Load by stage, scheduled predictions, lineage |

## Demo Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Chapter 1: TRAIN ──▶ Chapter 2: EXPLORE ──▶ Chapter 3: STAGING             │
│                                                       │                     │
│                                                       ▼                     │
│  Chapter 6: INFERENCE ◀── Chapter 5: PRODUCTION ◀── Chapter 4: COMPARE      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Talking Points

### Chapter 1: Clean Developer Experience
> "Data scientists write pure Python - just `@step` and `@pipeline`. No wrapper code, no boilerplate. Platform governance happens automatically via hooks."

### Chapter 2: Single Source of Truth
> "The Model Control Plane tracks every model version with complete lineage. From any prediction, trace back to training data and code commit."

### Chapter 3: Validation Gates
> "Platform team sets the rules. Models must meet 70% accuracy/precision/recall before staging. This happens automatically - data scientists don't bypass it."

### Chapter 4: Safe Rollouts
> "Before promoting to production, run champion/challenger. Both models predict on the same data - you see exactly how they differ before risking production."

### Chapter 5: Higher Bar for Production
> "Production requires 80% performance - higher than staging. Triggered by GitHub release for complete audit trail. Requires explicit `--force` to replace existing model."

### Chapter 6: Automatic Model Loading
> "Batch inference loads model by STAGE, not version. When you promote a new model, inference automatically uses it. Complete lineage preserved."

## Prerequisites

```bash
# From project root
pip install -r requirements.txt
zenml init
```

## Running Individual Chapters

Each chapter can be run standalone:

```bash
# Chapter 1: Train
python demo/chapters/chapter_1_training.py

# Chapter 2: Explore Model Control Plane
python demo/chapters/chapter_2_model_control_plane.py

# Chapter 3: Promote to Staging
python demo/chapters/chapter_3_promote_staging.py

# Chapter 4: Champion/Challenger
python demo/chapters/chapter_4_champion_challenger.py

# Chapter 5: Promote to Production
python demo/chapters/chapter_5_promote_production.py

# Chapter 6: Batch Inference
python demo/chapters/chapter_6_batch_inference.py
```

## Tips for Demos

1. **Start with dashboard open**: `zenml up` in another terminal
2. **Use `--chapter` for focused demos**: Skip to relevant chapters
3. **Show code alongside**: Open `src/pipelines/training.py` to show clean code
4. **Highlight governance**: Show `governance/hooks/` to explain automatic enforcement
5. **Emphasize audit trail**: Click through dashboard to show lineage

## Customizing for Customer Demos

The demo uses synthetic healthcare data. To customize:

1. **Change domain language**: Update model name in `src/pipelines/`
2. **Adjust thresholds**: Modify `scripts/promote_model.py` validation requirements
3. **Add industry hooks**: Create domain-specific hooks in `governance/hooks/`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No model found" | Run Chapter 1 first to train a model |
| "No staging model" | Run Chapter 3 to promote to staging |
| "Comparison failed" | Need both staging AND production models |
| "Permission denied" | Check ZenML connection: `zenml status` |
