"""Chapter 3: Champion vs Challenger.

Demonstrates:
- Safe model rollouts via A/B comparison
- Comparing new staging-trained model vs current staging model
- Data-driven promotion decisions
- Pipeline snapshots for immutable deployments (Pro)

This mirrors the validation step after train-staging.yml completes:
  - test-batch-inference.yml validates the new model
  - Champion/Challenger compares before promotion
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 3: Champion/Challenger comparison."""

    print_section("🎯 What We're Demonstrating")
    print("  🔧 Workspace: enterprise-dev-staging")
    print("  📦 Stack: dev-stack (local orchestrator, GCS artifacts)")
    print(
        """
After the staging training (Ch2), we validate the new model before promoting.

In the GitOps flow:
  1. train-staging.yml trains the model on staging-stack
  2. test-batch-inference.yml validates inference works
  3. Champion/Challenger compares new vs current staging model
  4. If safe → merge PR → promote to staging (Ch4)

We compare the newly trained model (challenger) against the current
staging model (champion) to ensure we're not regressing.
"""
    )

    print_section("🥊 Champion vs Challenger Pattern")
    print(
        """
  ┌─────────────────────────────────────────────────────────────┐
  │                      INFERENCE DATA                         │
  └─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
  ┌───────────────────┐       ┌───────────────────┐
  │     CHAMPION      │       │    CHALLENGER     │
  │   (Current        │       │   (Newly trained  │
  │    Staging)       │       │    from Ch2)      │
  └───────────────────┘       └───────────────────┘
              │                           │
              ▼                           ▼
  ┌───────────────────┐       ┌───────────────────┐
  │   Predictions A   │       │   Predictions B   │
  └───────────────────┘       └───────────────────┘
              │                           │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │      COMPARISON           │
              │  • Agreement Rate         │
              │  • Probability Diff       │
              │  • Risk Assessment        │
              └───────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │   PROMOTION DECISION      │
              │  SAFE / REVIEW / CAUTION  │
              └───────────────────────────┘
"""
    )

    print_section("📊 Current Model Versions (dev-staging workspace)")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()

        # Check staging (champion)
        staging = None
        try:
            staging = client.get_model_version(
                "breast_cancer_classifier",
                ModelStages.STAGING,
            )
            print(f"  🏆 Champion (Current Staging):  v{staging.number}")
        except KeyError:
            print("  🏆 Champion (Current Staging):  None")

        # Check latest (challenger = newly trained from ch2)
        latest = None
        try:
            latest = client.get_model_version(
                "breast_cancer_classifier",
                ModelStages.LATEST,
            )
            print(f"  🥊 Challenger (Latest trained):  v{latest.number}")
        except KeyError:
            print("  🥊 Challenger (Latest trained):  None - run Chapter 1/2 first")

    except Exception as e:
        print(f"Could not check models: {e}")
        staging = None

    print_section("🚀 Running Champion/Challenger Comparison")

    # Ensure we're on dev-stack
    print("  Setting stack to 'dev-stack'...")
    subprocess.run(["zenml", "stack", "set", "dev-stack"], capture_output=True)
    print("  ✅ Stack: dev-stack\n")

    # The champion_challenger_pipeline compares STAGING (champion) vs LATEST (challenger).
    # If no staging exists (first run), show narrative about what happens.
    if staging is not None:
        print("Command: python run.py --pipeline champion_challenger\n")
        try:
            result = subprocess.run(
                [sys.executable, "run.py", "--pipeline", "champion_challenger"],
                capture_output=False,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                print("\n✅ Champion/Challenger comparison completed!")
            else:
                print(f"\n⚠️  Comparison finished with code: {result.returncode}")
        except subprocess.TimeoutExpired:
            print("\n⏱️  Comparison timed out")
        except FileNotFoundError:
            print("\n⚠️  run.py not found")
    else:
        print(
            """
Note: The champion_challenger_pipeline compares STAGING vs LATEST models.
No staging model exists yet (first demo run).

This is expected! On first run:
  - Ch1/Ch2 train a model (becomes LATEST)
  - Ch4 will promote it to STAGING
  - On subsequent runs, Ch3 will compare new LATEST vs current STAGING

Command: python run.py --pipeline champion_challenger

Expected comparison report (on subsequent runs):

  ┌────────────────────────────────────────────────────────┐
  │  CHAMPION vs CHALLENGER COMPARISON REPORT              │
  ├────────────────────────────────────────────────────────┤
  │  Champion (Current Staging):  v1                       │
  │  Challenger (Latest Trained): v2                       │
  │                                                        │
  │  Total Samples: 1,000                                  │
  │  Agreement Rate: 94.2%                                 │
  │  Avg Probability Diff: 0.032                           │
  │  Max Probability Diff: 0.156                           │
  │                                                        │
  │  RECOMMENDATION: SAFE TO PROMOTE                       │
  └────────────────────────────────────────────────────────┘
"""
        )

    print_section("📸 Pipeline Snapshots (Pro Feature)")
    print(
        """
In CI/CD, validations can be deployed as immutable snapshots:

  # Build snapshot for staging validation
  python scripts/build_snapshot.py \\
      --pipeline champion_challenger \\
      --environment staging \\
      --stack staging-stack

  # Build batch inference snapshot for validation
  python scripts/build_snapshot.py \\
      --pipeline batch_inference \\
      --environment staging \\
      --stack staging-stack \\
      --run

This mirrors test-batch-inference.yml which:
  1. Runs after train-staging.yml completes
  2. Validates batch inference with the new model
  3. Uses staging-stack (Vertex AI) for production-like testing
  4. Builds an immutable snapshot for reproducibility
"""
    )

    print_section("📋 Interpreting the Comparison")
    print(
        """
  RECOMMENDATION LEVELS
  ─────────────────────
  • SAFE TO PROMOTE: Agreement ≥95%, Prob diff <5%
    → Merge PR, promote to staging

  • REVIEW RECOMMENDED: Agreement 85-95%
    → Review disagreement cases, then decide

  • CAUTION: Agreement <85%
    → Investigate before promoting

This data-driven approach reduces production risk!

Next: Let's promote the validated model to staging →
"""
    )


if __name__ == "__main__":
    run()
