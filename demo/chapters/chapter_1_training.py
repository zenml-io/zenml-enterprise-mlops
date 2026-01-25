"""Chapter 1: Train a Model.

Demonstrates:
- Clean developer experience (pure Python)
- Platform governance via hooks
- Automatic MLflow logging
- Model versioning in Model Control Plane
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 1: Training a Model."""

    print_section("🎯 What We're Demonstrating")
    print(
        """
In this chapter, we train a risk prediction model using the breast cancer dataset.

Key points to highlight:
  ✓ Data scientists write PURE PYTHON - no framework wrappers
  ✓ Platform governance is AUTOMATIC via hooks
  ✓ MLflow experiment tracking via stack component (zero code!)
  ✓ Slack notifications on success/failure
  ✓ Model is versioned in the Model Control Plane
"""
    )

    print_section("📝 The Training Pipeline Code")
    print(
        """
Here's what the training pipeline looks like (src/pipelines/training.py):

    from governance.hooks import pipeline_success_hook, pipeline_failure_hook

    @pipeline(
        model=Model(name="patient_readmission_predictor"),
        on_success=pipeline_success_hook,    # ← Slack notification
        on_failure=pipeline_failure_hook,    # ← Slack alert + compliance log
    )
    def training_pipeline():
        X_train, X_test, y_train, y_test = load_data()
        X_train = validate_data_quality(X_train)  # ← Platform validation
        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        validate_model_performance(metrics)       # ← Platform validation
        return model, metrics

Notice:
  • MLflow tracking is automatic (experiment_tracker in stack)
  • Slack alerts on success/failure (alerter in stack)
  • Just clean, readable Python
"""
    )

    print_section("🚀 Running the Training Pipeline")
    print("Executing: python run.py --pipeline training\n")

    try:
        result = subprocess.run(
            [sys.executable, "run.py", "--pipeline", "training"],
            capture_output=False,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("\n✅ Training completed successfully!")
        else:
            print(f"\n⚠️  Training finished with return code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Training timed out (this is normal for long runs)")
    except FileNotFoundError:
        print("\n⚠️  run.py not found - running from wrong directory?")
        print("   Run from project root: cd zenml-enterprise-mlops")

    print_section("📊 What Happened Behind the Scenes")
    print(
        """
1. Pipeline executed with automatic governance:
   • Data quality validation checked for missing values, min rows
   • Model performance validation checked accuracy, precision, recall

2. MLflow logged everything automatically (via hook):
   • Model parameters (n_estimators, max_depth)
   • Metrics (accuracy, precision, recall, f1)
   • Model artifact

3. Model Control Plane recorded:
   • New model version created
   • Full lineage (data → model → metrics)
   • Git commit (if code repo configured)
   • All metadata for audit trail

Next: Let's explore this in the Model Control Plane →
"""
    )


if __name__ == "__main__":
    run()
