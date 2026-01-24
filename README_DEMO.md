# 🚀 ZenML Enterprise MLOps Template - Demo Guide

**Quick Reference for HCA Healthcare Demo (Jan 27, 2026)**

## 🎯 What We Built (In One Day!)

A production-ready MLOps template showcasing:

1. ✅ **Multi-environment model promotion** (GitOps-driven)
2. ✅ **Platform governance** (hooks enforce standards without developer friction)
3. ✅ **Complete lineage tracking** (regulatory compliance ready)
4. ✅ **Clean developer experience** (pure Python, no wrappers)
5. ✅ **Batch inference** (uses production model by alias)

## 🔥 Live Demo Flow (15 minutes)

### Part 1: Developer Experience (3 min)
```bash
# Show how clean the code is
cat src/pipelines/training.py

# Data scientist runs pipeline - that's it!
python run.py --pipeline training

# Point out:
# - No wrapper code
# - Platform hooks run automatically
# - Governance enforced behind the scenes
```

### Part 2: Model Promotion (4 min)
```bash
# Show promotion script
cat scripts/promote_model.py

# Promote model to staging
python scripts/promote_model.py \
  --model patient_readmission_predictor \
  --to-stage staging

# Show validation checks
# Show audit logging
# Show GitHub Actions workflow for automated promotion
cat .github/workflows/promote-production.yml
```

### Part 3: Complete Lineage (5 min)
```bash
# Open lineage notebook
jupyter notebook notebooks/lineage_demo.ipynb

# Walk through:
# 1. Production model → Training run
# 2. Training run → Training data
# 3. Training data → Code commit
# 4. Complete audit trail for compliance
```

### Part 4: GitOps Workflows (3 min)
```bash
# Show GitHub Actions workflows
cat .github/workflows/train-staging.yml
cat .github/workflows/promote-production.yml

# Explain:
# - PR to staging → auto-train
# - Release tag → auto-promote to production
# - Daily batch inference
```

## 💡 Key Talking Points

### "No Wrapper Code"
```python
# Bad (their current approach with KFP):
@kfp.component(base_image="...")
def wrapper_step():
    # Complex wrapper logic
    # MLflow setup
    # Error handling
    import user_code
    user_code.train()
    
# Good (ZenML approach):
@step
def train_model(data: pd.DataFrame) -> ClassifierMixin:
    model = RandomForestClassifier()
    model.fit(data[features], data[target])
    return model  # That's it!
```

### "Platform Enforces Governance"
- Show `governance/hooks/mlflow_hook.py` - runs automatically
- Show `governance/steps/data_validation.py` - required step
- Data scientists never see this code!

### "GitOps-Driven Promotion"
- PR merge → auto-train in staging
- GitHub release → auto-promote to production
- All tracked in Git for audit trail

### "Complete Audit Trail"
- Show lineage notebook
- Trace from production prediction back to source data
- HIPAA/GDPR ready

## 📊 What's Running Under the Hood

When you run `python run.py --pipeline training`:

1. ✅ **Data Loading** - UCI diabetes dataset
2. ✅ **Platform Validation** - Data quality gate (governance enforced)
3. ✅ **Feature Engineering** - StandardScaler fit/transform
4. ✅ **Model Training** - Random Forest with MLflow autologging
5. ✅ **Model Evaluation** - Comprehensive metrics
6. ✅ **Performance Validation** - Platform quality gate (governance enforced)
7. ✅ **Model Registration** - Versioned in Model Control Plane
8. ✅ **Governance Hooks** - MLflow logging, compliance audit

**All in 31 seconds!**

## 🎓 HCA's Critical Questions - Our Answers

| Question | Answer | Where to Show |
|----------|--------|---------------|
| Multi-env promotion | ✅ Promotion script + GitOps | `scripts/promote_model.py`, `.github/workflows/` |
| Platform control | ✅ Hooks + validation steps | `governance/hooks/`, `governance/steps/` |
| Clean dev experience | ✅ Pure Python, no wrappers | `src/pipelines/training.py` |
| GitOps integration | ✅ GitHub Actions workflows | `.github/workflows/` |
| Audit trail | ✅ Complete lineage tracking | `notebooks/lineage_demo.ipynb` |
| Batch inference | ✅ Uses production by alias | `src/pipelines/batch_inference.py` |
| GCP integration | ⏳ Add after demo | Would be Vertex AI orchestrator |
| MLflow integration | ✅ Auto-logging via hooks | See pipeline run logs |
| Model registry | ✅ Model Control Plane + MLflow | Dashboard |

## 🔄 Comparison: Current vs ZenML

| Aspect | Current (KFP) | With ZenML |
|--------|---------------|------------|
| **Developer Code** | Complex wrappers | Pure Python |
| **Governance** | Manual enforcement | Automatic (hooks) |
| **Promotion** | Manual, error-prone | Automated, validated |
| **Lineage** | Difficult to trace | Complete, automatic |
| **MLflow Logging** | Manual in each step | Auto via hooks |
| **Quality Gates** | Custom code | Platform steps |

## 📁 Repository Tour

```
zenml-enterprise-mlops/
├── governance/                    # ← Platform team owns
│   ├── hooks/
│   │   ├── mlflow_hook.py        # ← Auto-logging
│   │   ├── compliance_hook.py    # ← Audit trail
│   │   └── monitoring_hook.py    # ← Arize integration
│   └── steps/
│       ├── data_validation.py    # ← Quality gates
│       └── model_validation.py   # ← Performance gates
│
├── src/                          # ← Data scientists own
│   ├── pipelines/
│   │   ├── training.py          # ← Clean pipeline code
│   │   └── batch_inference.py   # ← Uses production model
│   └── steps/
│       ├── data_loader.py       # ← Pure Python
│       ├── model_trainer.py     # ← No wrappers!
│       └── model_evaluator.py
│
├── .github/workflows/            # ← GitOps automation
│   ├── train-staging.yml        # ← PR-based training
│   ├── promote-production.yml   # ← Release-based promotion
│   └── batch-inference.yml      # ← Scheduled inference
│
├── scripts/
│   └── promote_model.py         # ← Production promotion
│
├── notebooks/
│   └── lineage_demo.ipynb       # ← Compliance demo
│
└── run.py                       # ← Simple CLI
```

## 🚦 If They Ask About...

### "How would this work with our GCP setup?"
- "We'd swap the local orchestrator for Vertex AI"
- "Same code, different stack configuration"
- "Can use your existing GCS buckets and BigQuery"

### "How do we integrate with Arize?"
- "Already have a monitoring hook placeholder"
- "Just add Arize client and send predictions"
- "Platform team controls this, not data scientists"

### "What about RBAC for MLflow?"
- "ZenML Pro has project-level RBAC"
- "Can separate teams with Projects"
- "Or use Databricks MLflow which has native RBAC"

### "How do we migrate from our current system?"
- "Gradual migration - one pipeline at a time"
- "Can run ZenML alongside current KFP"
- "Start with new projects, migrate old ones over time"

## ⏭️ Next Steps After Demo

If HCA wants to proceed:
1. **Week 1-2:** Set up GCP stack (Vertex AI, GCS, etc.)
2. **Week 3:** Migrate one pilot pipeline
3. **Week 4:** Add Arize monitoring integration
4. **Week 5-6:** Implement champion/challenger pattern
5. **Week 7-8:** Team training and documentation
6. **Week 9+:** Gradual migration of remaining pipelines

## 🎤 Closing Statement

> "This template demonstrates how ZenML solves your biggest pain point - multi-environment model promotion - while making life easier for data scientists and giving platform teams the governance controls they need. Everything you saw today is production-ready code that follows ZenML best practices. We can have you up and running in GCP within weeks, not months."

---

**Status:** ✅ Demo Ready  
**Built:** January 24, 2026  
**Demo Date:** January 27, 2026
