"""Chapter 4: Promote to Staging.

Demonstrates:
- Model promotion with validation gates
- Minimum performance requirements
- Audit trail for promotions
- Exploring the Model Control Plane
- GitOps merge pattern

This mirrors merging a PR after champion/challenger validation:
  - PR is approved, merged
  - Model promoted from none → staging
  - Model Control Plane tracks the promotion
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 4: Promote to Staging."""

    # Ensure we're on dev-stack
    subprocess.run(["zenml", "stack", "set", "dev-stack"], capture_output=True)

    print_section("🎯 What We're Demonstrating")
    print("  🔧 Workspace: enterprise-dev-staging")
    print("  📦 Stack: dev-stack (promotion is a metadata operation, not a pipeline)")
    print(
        """
The champion/challenger passed (Ch3). Now we merge the PR and promote.

In the GitOps flow:
  1. PR approved after champion/challenger review
  2. Merge to main triggers promotion
  3. Model validated against staging thresholds
  4. Model stage set to "staging" in Model Control Plane

This is the gateway to production - only validated models get here.
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

    print_section("🔍 Checking Latest Model Metrics")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()
        latest = client.get_model_version(
            "breast_cancer_classifier",
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
        print("Run Chapters 1-2 first to train a model.")
        return

    print_section("🚀 Promoting to Staging")
    print(
        "Command: python scripts/promote_model.py --model breast_cancer_classifier"
        " --to-stage staging --force\n"
    )

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/promote_model.py",
                "--model",
                "breast_cancer_classifier",
                "--to-stage",
                "staging",
                "--force",
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
        print("\n⚠️  Script not found")

    print_section("📊 Exploring the Model Control Plane")
    print(
        """
The Model Control Plane is the SINGLE SOURCE OF TRUTH for all models.
Let's see what's registered:
"""
    )

    try:
        from zenml.client import Client

        client = Client()
        model = client.get_model("breast_cancer_classifier")
        versions = client.list_model_versions("breast_cancer_classifier")

        print(f"  Model: {model.name}")
        print(f"  Total Versions: {len(versions)}\n")

        for v in versions:
            stage = v.stage.value if hasattr(v.stage, "value") else str(v.stage)
            stage_display = f" ← {stage.upper()}" if stage and stage != "None" else ""
            print(f"    v{v.number}: {stage_display}")

        print(
            """
  Every version tracks:
  • Full lineage (data → features → model → predictions)
  • Metrics (accuracy, precision, recall, f1)
  • Git commit (if repo configured)
  • Pipeline run details
  • Promotion history
"""
        )

    except Exception as e:
        print(f"  Could not list versions: {e}")

    print_section("📋 GitOps Flow (what we just simulated)")
    print(
        """
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  Ch1: Train locally (dev-stack)    → Fast iteration          │
  │       ↓                                                      │
  │  Ch2: PR → staging training        → Production-like infra   │
  │       ↓                                                      │
  │  Ch3: Champion/Challenger          → Validate vs current     │
  │       ↓                                                      │
  │  Ch4: Merge PR → promote staging   → YOU ARE HERE            │
  │       ↓                                                      │
  │  Ch5: Release → promote production → Cross-workspace export  │
  │       ↓                                                      │
  │  Ch6: Scheduled batch inference    → Production workspace    │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘

Next: Let's promote the staging model to the production workspace →
"""
    )


if __name__ == "__main__":
    run()
