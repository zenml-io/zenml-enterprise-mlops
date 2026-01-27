"""Chapter 1: Train Locally.

Demonstrates:
- Clean developer experience (pure Python)
- Platform governance via hooks
- Automatic MLflow logging
- Model versioning in Model Control Plane
- Fast iteration on dev-stack (local orchestrator)

This is what a data scientist does day-to-day: iterate locally with fast
feedback loops before pushing code for CI/CD.
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 1: Local Training."""

    print_section("🎯 What We're Demonstrating")
    print("  🔧 Workspace: enterprise-dev-staging")
    print("  📦 Stack: dev-stack (local orchestrator, GCS artifacts)")
    print(
        """
A data scientist iterates locally with fast feedback loops.

Key points to highlight:
  ✓ Data scientists write PURE PYTHON - no framework wrappers
  ✓ Platform governance is AUTOMATIC via hooks
  ✓ MLflow experiment tracking via stack component (zero code!)
  ✓ Model is versioned in the Model Control Plane
  ✓ Same code runs locally AND in CI/CD (just different configs)
"""
    )

    print_section("📝 The Training Pipeline Code")
    print(
        """
Here's what the training pipeline looks like (src/pipelines/training.py):

    from governance.hooks import pipeline_success_hook, pipeline_failure_hook

    @pipeline(
        model=Model(name="breast_cancer_classifier"),
        on_success=pipeline_success_hook,    # ← Automatic governance
        on_failure=pipeline_failure_hook,    # ← Automatic alerting
    )
    def training_pipeline():
        X_train, X_test, y_train, y_test = load_data()
        X_train = validate_data_quality(X_train)  # ← Platform validation
        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        validate_model_performance(metrics)       # ← Platform validation
        return model, metrics

Notice:
  • Clean, readable Python - no wrapper code
  • Governance is injected by platform team via hooks
  • Same pipeline runs on any stack (local, staging, production)
"""
    )

    print_section("🚀 Running the Training Pipeline (local)")

    # Note: run.py automatically sets dev-stack for local environment
    print("  Stack will be set automatically by run.py based on environment")
    print("  ✅ Environment: local → Stack: dev-stack\n")

    print("Command: python run.py --pipeline training --environment local\n")

    try:
        result = subprocess.run(
            [sys.executable, "run.py", "--pipeline", "training", "--environment", "local"],
            capture_output=False,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("\n✅ Local training completed successfully!")
        else:
            print(f"\n⚠️  Training finished with return code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Training timed out")
    except FileNotFoundError:
        print("\n⚠️  run.py not found - running from wrong directory?")

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
   • All metadata for audit trail

This is the fast inner loop. Now let's simulate pushing this
code as a PR and running it on the staging stack →
"""
    )


if __name__ == "__main__":
    run()
