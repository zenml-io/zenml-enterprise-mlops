# Training Report

**Model**: `breast_cancer_classifier` (v6)
**Pipeline**: `training_pipeline` (run: `3c6a2c20`)
**Commit**: `unknown`
**Generated**: 2026-01-28 16:48 UTC

---

## Overall Decision: ✅ **PASSED**

| Category | Status |
|----------|--------|
| Training Data Quality | ✅ PASS |
| Test Data Quality | ✅ PASS |
| Model Performance | ✅ PASS |

---

## Detailed Results


### Data Quality: Training Data

| Check | Threshold | Actual | Result |
|-------|-----------|--------|--------|
| Minimum rows | 100 | 455 | ✅ PASS |
| Missing values | ≤10.0% | 0.00% | ✅ PASS |
| Duplicate rows | - | 0 | ✅ OK |

**Summary**: 455 rows × 30 columns, 0 missing values



### Data Quality: Test Data

| Check | Threshold | Actual | Result |
|-------|-----------|--------|--------|
| Minimum rows | 20 | 114 | ✅ PASS |
| Missing values | ≤10.0% | 0.00% | ✅ PASS |
| Duplicate rows | - | 0 | ✅ OK |

**Summary**: 114 rows × 30 columns, 0 missing values



### Model Performance

| Metric | Threshold | Actual | Result |
|--------|-----------|--------|--------|
| Accuracy | ≥70.0% | 95.61% | ✅ PASS |
| Precision | ≥70.0% | 95.89% | ✅ PASS |
| Recall | ≥70.0% | 97.22% | ✅ PASS |
| F1 Score | - | 96.55% | ℹ️ INFO |
| ROC AUC | - | 99.37% | ℹ️ INFO |


---

## Next Steps


- ✅ Model meets all quality gates
- 🔄 Merge PR to promote to staging
- 🚀 Create a release to promote to production

---

## Links

- [ZenML Dashboard](https://cloud.zenml.io)
