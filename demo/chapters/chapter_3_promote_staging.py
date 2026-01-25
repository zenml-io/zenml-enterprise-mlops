"""Chapter 3: Promote to Staging.

Demonstrates:
- Model promotion with validation gates
- Minimum performance requirements
- Audit trail for promotions
- GitOps integration pattern
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 3: Promote to Staging."""

    print_section("🎯 What We're Demonstrating")
    print(
        """
Promotion to STAGING requires passing validation gates.

Key points to highlight:
  ✓ Automatic validation before promotion
  ✓ Minimum performance thresholds enforced
  ✓ Audit trail created for compliance
  ✓ Same script used in GitOps workflows
"""
    )

    print_section("📋 Staging Requirements")
    print(
        """
To promote to STAGING, a model must meet:

  ┌────────────────────────────────────┐
  │  STAGING VALIDATION GATES          │
  ├────────────────────────────────────┤
  │  Accuracy  ≥ 0.70 (70%)            │
  │  Precision ≥ 0.70 (70%)            │
  │  Recall    ≥ 0.70 (70%)            │
  └────────────────────────────────────┘

These thresholds are defined in: scripts/promote_model.py
Platform team controls these - data scientists don't modify.
"""
    )

    print_section("🔍 Checking Current Model Metrics")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()
        latest = client.get_model_version(
            "patient_readmission_predictor",
            ModelStages.LATEST,
        )

        print(f"Latest Model: v{latest.number}\n")

        metrics = latest.run_metadata
        requirements = {"accuracy": 0.7, "precision": 0.7, "recall": 0.7}

        print(f"{'Metric':<12} {'Value':<10} {'Required':<10} {'Status':<10}")
        print("-" * 45)

        all_pass = True
        for metric, required in requirements.items():
            if metric in metrics:
                val_obj = metrics[metric]
                val = float(val_obj.value if hasattr(val_obj, "value") else val_obj)
                status = "✅ PASS" if val >= required else "❌ FAIL"
                if val < required:
                    all_pass = False
                print(f"{metric:<12} {val:<10.4f} {required:<10.2f} {status:<10}")
            else:
                print(f"{metric:<12} {'N/A':<10} {required:<10.2f} {'⚠️ MISSING':<10}")
                all_pass = False

        if all_pass:
            print("\n✅ Model meets staging requirements!")
        else:
            print("\n❌ Model does NOT meet staging requirements.")

    except Exception as e:
        print(f"Could not check metrics: {e}")
        print("Run Chapter 1 first to train a model.")
        return

    print_section("🚀 Promoting to Staging")
    print(
        "Executing: python scripts/promote_model.py --model patient_readmission_predictor --to-stage staging --force\n"
    )

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/promote_model.py",
                "--model",
                "patient_readmission_predictor",
                "--to-stage",
                "staging",
                "--force",  # For demo - replace existing staging model
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ Promotion to staging successful!")
        else:
            print(f"\n⚠️  Promotion failed (exit code: {result.returncode})")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Promotion timed out")
    except FileNotFoundError:
        print("\n⚠️  Script not found - running from wrong directory?")

    print_section("📋 GitOps Integration")
    print(
        """
In production, this promotion happens automatically via GitHub Actions:

  .github/workflows/train-staging.yml:

    1. PR opened to 'staging' branch
    2. Training pipeline runs automatically
    3. If validation passes → model promoted to STAGING
    4. PR comment added with results

This enables:
  • Code review before model changes
  • Automatic validation gates
  • Complete audit trail in git history

Next: Let's compare staging vs production (Champion/Challenger) →
"""
    )


if __name__ == "__main__":
    run()
