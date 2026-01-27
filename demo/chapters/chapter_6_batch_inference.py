"""Chapter 6: Run Batch Inference.

Demonstrates:
- Loading production model by stage
- Automatic model versioning
- Prediction lineage
- Scheduled inference pattern

In two-workspace mode, this runs in enterprise-production workspace.
The workspace switch happens in run_demo.py before calling this chapter.
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run(two_workspace: bool = False):
    """Run Chapter 6: Batch Inference."""

    print_section("🎯 What We're Demonstrating")

    if two_workspace:
        print("  🏭 Workspace: enterprise-production\n")
        print(
            """
Batch inference runs in the PRODUCTION workspace using the imported model.

Key points to highlight:
  ✓ Model was imported from dev-staging via cross-workspace promotion
  ✓ Model loaded by STAGE, not version number
  ✓ Inference lineage is preserved in the production workspace
  ✓ Training lineage is preserved in dev-staging workspace
  ✓ Scheduled via cron in GitOps workflow
"""
        )
    else:
        print(
            """
Batch inference uses the PRODUCTION model automatically.

Key points to highlight:
  ✓ Model loaded by STAGE, not version number
  ✓ Predictions linked to model version for lineage
  ✓ Same code works as model versions change
  ✓ Scheduled via cron in GitOps workflow
"""
        )

    print_section("📝 Batch Inference Pattern")
    print(
        """
The key pattern - load model by STAGE:

    @pipeline(
        model=Model(
            name="breast_cancer_classifier",
            version=ModelStages.PRODUCTION,  # ← Always uses current production
        ),
    )
    def batch_inference_pipeline():
        data = load_inference_data()
        predictions = run_predictions(data)
        save_predictions(predictions)

Benefits:
  • No code changes when model is updated
  • Predictions automatically linked to model version
  • Easy to switch to staging for testing
  • Complete lineage maintained
"""
    )

    if two_workspace:
        print_section("🔗 Lineage Across Workspaces")
        print(
            """
  enterprise-dev-staging              enterprise-production
  ┌────────────────────────┐         ┌──────────────────────────────┐
  │ Training Lineage:      │         │ Inference Lineage:           │
  │   data → features →   │         │   model → predictions →     │
  │   model → metrics     │  audit  │   saved results             │
  │                        │  trail  │                              │
  │ Full training history  │ ◀─────▶ │ Model metadata links back   │
  │ preserved here         │         │ to source workspace         │
  └────────────────────────┘         └──────────────────────────────┘

  Training lineage: Fully preserved in dev-staging
  Inference lineage: Fully preserved in production
  Audit trail: Production model metadata links back to source
"""
        )

    print_section("🔍 Current Production Model")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()

        try:
            prod = client.get_model_version(
                "breast_cancer_classifier",
                ModelStages.PRODUCTION,
            )
            print(f"  Production Model: v{prod.number}")
            print(f"  Created: {str(prod.created)[:19]}")

            # Show metrics
            metrics = prod.run_metadata
            print("\n  Performance:")
            for key in ["accuracy", "precision", "recall"]:
                if key in metrics:
                    val = metrics[key]
                    val = float(val.value if hasattr(val, "value") else val)
                    print(f"    {key}: {val:.4f}")

            # Show source metadata if cross-workspace
            if two_workspace:
                print("\n  Source Metadata:")
                for key in [
                    "source_workspace",
                    "source_version",
                    "source_stage",
                    "promotion_timestamp",
                ]:
                    if key in metrics:
                        val = metrics[key]
                        val = val.value if hasattr(val, "value") else val
                        print(f"    {key}: {val}")

        except KeyError:
            print("  ⚠️  No production model found. Run Chapter 5 first!")
            return

    except Exception as e:
        print(f"Could not check model: {e}")
        return

    print_section("🚀 Running Batch Inference")

    # Ensure we're on default stack (or gcp-stack in production workspace)
    print("  Setting stack to 'default'...")
    subprocess.run(["zenml", "stack", "set", "default"], capture_output=True)
    print("  ✅ Stack: default\n")

    print("Executing: python run.py --pipeline batch_inference\n")

    try:
        result = subprocess.run(
            [sys.executable, "run.py", "--pipeline", "batch_inference"],
            capture_output=False,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("\n✅ Batch inference completed!")
        else:
            print(f"\n⚠️  Inference finished with code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Inference timed out")
    except FileNotFoundError:
        print("\n⚠️  run.py not found")

    print_section("📅 Scheduled Inference Pattern")

    if two_workspace:
        print(
            """
In production, batch inference runs on a schedule in the production workspace:

  .github/workflows/batch-inference.yml:

    env:
      ZENML_STORE_URL: ${{ secrets.ZENML_PRODUCTION_URL }}
      ZENML_STORE_API_KEY: ${{ secrets.ZENML_PRODUCTION_API_KEY }}

    on:
      schedule:
        - cron: '0 6 * * *'  # Daily at 6 AM UTC

    jobs:
      inference:
        steps:
          - run: python run.py --pipeline batch_inference

This enables:
  • Daily risk scoring in the production workspace
  • Automatic use of latest production model
  • Inference lineage preserved in production
  • Training lineage preserved in dev-staging
  • Complete audit trail across workspaces
"""
        )
    else:
        print(
            """
In production, batch inference runs on a schedule:

  .github/workflows/batch-inference.yml:

    on:
      schedule:
        - cron: '0 6 * * *'  # Daily at 6 AM UTC

    jobs:
      inference:
        steps:
          - run: python run.py --pipeline batch_inference

This enables:
  • Daily risk scoring for all patients
  • Automatic use of latest production model
  • Complete lineage for every prediction
  • Easy audit of what model made what predictions
"""
        )

    print_section("🎉 Demo Complete!")
    print(
        """
You've seen the complete enterprise MLOps workflow:

  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  1. TRAIN          Clean Python, automatic governance       │
  │       ↓            (enterprise-dev-staging)                 │
  │  2. VERSION        Model Control Plane tracks everything    │
  │       ↓            (enterprise-dev-staging)                 │
  │  3. STAGING        Validation gates, PR-triggered           │
  │       ↓            (enterprise-dev-staging)                 │
  │  4. COMPARE        Champion/Challenger for safe rollouts    │
  │       ↓            (enterprise-dev-staging)                 │
  │  5. PRODUCTION     Cross-workspace export/import            │
  │       ↓            (dev-staging → production)               │
  │  6. INFERENCE      Scheduled batch, complete lineage        │
  │                    (enterprise-production)                   │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

Key Enterprise Benefits:
  ✓ Clean developer experience (no wrapper code)
  ✓ Automatic governance (hooks enforce standards)
  ✓ Complete audit trail (compliance-ready)
  ✓ GitOps workflows (git = source of truth)
  ✓ Safe rollouts (champion/challenger pattern)
  ✓ ZenML version upgrade isolation (2 workspaces)

Dashboard: zenml login
Docs: docs/ARCHITECTURE.md
"""
    )


if __name__ == "__main__":
    run()
