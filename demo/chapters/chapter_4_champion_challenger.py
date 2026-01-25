"""Chapter 4: Champion vs Challenger.

Demonstrates:
- Safe model rollouts
- A/B comparison before promotion
- Data-driven promotion decisions
- Risk mitigation pattern
"""


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 4: Champion/Challenger comparison."""

    print_section("🎯 What We're Demonstrating")
    print(
        """
Before promoting to production, we compare the STAGING model (challenger)
against the current PRODUCTION model (champion).

Key points to highlight:
  ✓ Run BOTH models on the same data
  ✓ Compare predictions side-by-side
  ✓ Get data-driven promotion recommendation
  ✓ Reduce risk of production incidents
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
  │   (Production)    │       │    (Staging)      │
  │    Model v1.0     │       │    Model v2.0     │
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

    print_section("📊 Current Model Stages")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()

        # Check production
        try:
            prod = client.get_model_version(
                "patient_readmission_predictor",
                ModelStages.PRODUCTION,
            )
            print(f"  🏆 Champion (Production): v{prod.number}")
        except KeyError:
            print("  🏆 Champion (Production): None - no production model yet")
            prod = None

        # Check staging
        try:
            staging = client.get_model_version(
                "patient_readmission_predictor",
                ModelStages.STAGING,
            )
            print(f"  🥊 Challenger (Staging):   v{staging.number}")
        except KeyError:
            print("  🥊 Challenger (Staging):   None - run Chapter 3 first")
            staging = None

        if not prod and not staging:
            print("\n⚠️  Need both production and staging models to compare.")
            print("   Run Chapters 1-3 first, then train again to have two versions.")
            return

    except Exception as e:
        print(f"Could not check models: {e}")
        return

    print_section("🚀 Running Champion/Challenger Comparison")
    print("Command: python run.py --pipeline champion_challenger\n")

    print(
        """
Note: The champion/challenger pipeline requires models with linked artifacts.
In a full setup, this pipeline would:

  1. Load inference data
  2. Run predictions with PRODUCTION model (champion)
  3. Run predictions with STAGING model (challenger)
  4. Compare predictions side-by-side
  5. Generate a comparison report

For this demo, we'll show the expected output:

  ┌────────────────────────────────────────────────────────┐
  │  CHAMPION vs CHALLENGER COMPARISON REPORT              │
  ├────────────────────────────────────────────────────────┤
  │  Champion (Production): v2                             │
  │  Challenger (Staging):  v3                             │
  │                                                        │
  │  Total Samples: 1,000                                  │
  │  Agreement Rate: 94.2%                                 │
  │  Avg Probability Diff: 0.032                           │
  │  Max Probability Diff: 0.156                           │
  │                                                        │
  │  RECOMMENDATION: REVIEW RECOMMENDED                    │
  │  Models show reasonable agreement but some divergence. │
  │  Review disagreement cases before promotion.           │
  └────────────────────────────────────────────────────────┘
"""
    )

    print_section("📋 Understanding the Report")
    print(
        """
The comparison report includes:

  AGREEMENT METRICS
  ─────────────────
  • Agreement Rate: % of samples where both models agree
  • Disagreement Rate: % of samples with different predictions

  PROBABILITY CALIBRATION
  ───────────────────────
  • Avg Probability Diff: Mean difference in confidence scores
  • Max Probability Diff: Largest confidence gap

  RECOMMENDATION
  ──────────────
  • SAFE TO PROMOTE: Agreement ≥95%, Prob diff <5%
  • REVIEW RECOMMENDED: Agreement 85-95%
  • CAUTION: Agreement <85% - investigate before promoting

This data-driven approach reduces production risk!

Next: Let's promote to production →
"""
    )


if __name__ == "__main__":
    run()
