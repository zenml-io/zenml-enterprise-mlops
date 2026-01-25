"""Chapter 5: Promote to Production.

Demonstrates:
- Higher validation bar for production
- Force flag for existing production model
- Complete audit trail
- GitOps release workflow
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 5: Promote to Production."""

    print_section("🎯 What We're Demonstrating")
    print(
        """
Promotion to PRODUCTION has STRICTER requirements than staging.

Key points to highlight:
  ✓ Higher performance thresholds (80% vs 70%)
  ✓ Must come from STAGING (validated path)
  ✓ Requires --force to replace existing production model
  ✓ Complete audit trail for compliance
"""
    )

    print_section("📋 Production Requirements")
    print(
        """
To promote to PRODUCTION, a model must meet:

  ┌────────────────────────────────────┐
  │  PRODUCTION VALIDATION GATES       │
  ├────────────────────────────────────┤
  │  Accuracy  ≥ 0.80 (80%)            │
  │  Precision ≥ 0.80 (80%)            │
  │  Recall    ≥ 0.80 (80%)            │
  └────────────────────────────────────┘

  PLUS:
  ✓ Must be promoted FROM staging (--from-stage staging)
  ✓ Champion/Challenger comparison recommended
  ✓ Requires --force if replacing existing production model
"""
    )

    print_section("🔍 Checking Staging Model Metrics")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()

        try:
            staging = client.get_model_version(
                "breast_cancer_classifier",
                ModelStages.STAGING,
            )
        except KeyError:
            print("❌ No staging model found. Run Chapter 3 first!")
            return

        print(f"Staging Model: v{staging.number}\n")

        metrics = staging.run_metadata
        requirements = {"accuracy": 0.8, "precision": 0.8, "recall": 0.8}

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
            print("\n✅ Model meets production requirements!")
        else:
            print("\n⚠️  Model may not meet production thresholds.")
            print("   Using --skip-validation for demo purposes...")

    except Exception as e:
        print(f"Could not check metrics: {e}")
        return

    print_section("🚀 Promoting to Production")
    print(
        "Executing: python scripts/promote_model.py --model breast_cancer_classifier "
        "--from-stage staging --to-stage production --force --skip-validation\n"
    )

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/promote_model.py",
                "--model",
                "breast_cancer_classifier",
                "--from-stage",
                "staging",
                "--to-stage",
                "production",
                "--force",  # Replace existing if any
                "--skip-validation",  # For demo - normally wouldn't skip!
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ Promotion to production successful!")
        else:
            print(f"\n⚠️  Promotion failed (exit code: {result.returncode})")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Promotion timed out")
    except FileNotFoundError:
        print("\n⚠️  Script not found")

    print_section("🔄 GitOps Production Release")
    print(
        """
In production, this is triggered by a GitHub Release:

  .github/workflows/promote-production.yml:

    1. Create GitHub Release (tag: v1.0.0)
    2. Workflow triggers automatically
    3. Builds pipeline snapshot (Pro feature)
    4. Promotes staging → production
    5. Creates audit log entry

  Command used:
    python scripts/promote_model.py \\
        --model breast_cancer_classifier \\
        --from-stage staging \\
        --to-stage production \\
        --force

Benefits:
  • Release notes document the change
  • Git tag provides point-in-time reference
  • GitHub Actions provides audit trail
  • Easy rollback via previous release

Next: Let's run batch inference with the production model →
"""
    )


if __name__ == "__main__":
    run()
