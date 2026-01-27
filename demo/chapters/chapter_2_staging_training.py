"""Chapter 2: Simulate PR → Staging Training.

Demonstrates:
- CI/CD triggered training (PR → staging stack)
- Production-like environment validation
- Staging config (cache disabled, SMOTE enabled)
- Running on staging-stack (Vertex AI orchestrator, GCS artifacts)

This mirrors what happens in train-staging.yml when a PR is opened:
  1. Code change triggers CI/CD
  2. Pipeline runs on staging-stack (Vertex AI)
  3. Model is trained with staging config (no cache, SMOTE enabled)
  4. Results are available for review before merge
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 2: Staging Training."""

    print_section("🎯 What We're Demonstrating")
    print("  🔧 Workspace: enterprise-dev-staging")
    print("  📦 Stack: staging-stack (Vertex AI orchestrator, GCS artifacts)")
    print(
        """
We simulate opening a PR. In the real GitOps flow:

  1. Data scientist pushes code → opens PR
  2. train-staging.yml triggers automatically
  3. Pipeline runs on staging-stack (Vertex AI, not local)
  4. Model trained with production-like settings
  5. PR comment shows results for review

This is the outer loop - validate that local work runs in production-like infra.
"""
    )

    print_section("📋 Local vs Staging Config Differences")
    print(
        """
  ┌─────────────────┬──────────────────┬──────────────────┐
  │ Setting         │ Local (Ch1)      │ Staging (Ch2)    │
  ├─────────────────┼──────────────────┼──────────────────┤
  │ Stack           │ dev-stack        │ staging-stack    │
  │ Orchestrator    │ Local            │ Vertex AI        │
  │ Artifact Store  │ GCS              │ GCS              │
  │ Governance      │ DISABLED         │ ENABLED          │
  │ Cache           │ Enabled          │ Disabled         │
  │ Config          │ configs/local    │ configs/staging  │
  └─────────────────┴──────────────────┴──────────────────┘

  Same pipeline code, different infrastructure & config.
  This is the power of ZenML stack abstraction.
"""
    )

    print_section("🔄 GitHub Actions Flow (what we're simulating)")
    print(
        """
  .github/workflows/train-staging.yml:

    on:
      pull_request:
        branches: [main]
        paths: ['src/**', 'governance/**', 'configs/**']

    jobs:
      train-staging:
        steps:
          # 1. Connect to dev-staging workspace
          - env:
              ZENML_STORE_URL: ${{ secrets.ZENML_DEV_STAGING_URL }}

          # 2. Set staging stack
          - run: zenml stack set staging-stack

          # 3. Train with staging config
          - run: python run.py --pipeline training --environment staging

          # 4. Or build a Pro pipeline snapshot
          - run: python scripts/build_snapshot.py \\
                   --environment staging --stack staging-stack --run
"""
    )

    print_section("🚀 Running Training on Staging Stack")

    # Check if staging-stack exists
    stack_check = subprocess.run(
        ["zenml", "stack", "describe", "staging-stack"],
        capture_output=True,
        text=True,
    )
    has_staging_stack = stack_check.returncode == 0

    if has_staging_stack:
        print("  📦 staging-stack found (Vertex AI orchestrator)!\n")
        print(
            """
  In CI/CD, this would run:
    zenml stack set staging-stack
    python run.py --pipeline training --environment staging

  ⏳ Vertex AI training takes several minutes (Docker build + job execution).
     For this demo, we'll run locally with staging CONFIG instead.
"""
        )
    else:
        print("  ℹ️  staging-stack not configured.\n")
        print(
            """
  In production, staging-stack would be configured with:
    - Orchestrator: Vertex AI
    - Artifact Store: GCS
    - Container Registry: Google Artifact Registry
"""
        )

    # Run with staging environment but on dev-stack for faster execution
    print("  Running: python run.py --pipeline training --environment staging --stack dev-stack")
    print("  (Staging config + governance, but local orchestrator for speed)\n")

    try:
        result = subprocess.run(
            [sys.executable, "run.py", "--pipeline", "training", "--environment", "staging", "--stack", "dev-stack"],
            capture_output=False,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            print("\n✅ Training completed (with staging config)!")
        else:
            print(f"\n⚠️  Training finished with code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("\n⏱️  Training timed out")
    except FileNotFoundError:
        print("\n⚠️  run.py not found")

    print_section("📊 Local vs Staging: What Changed?")
    print(
        """
We ran with STAGING environment (enable_governance=True).

  WHAT'S DIFFERENT FROM LOCAL (Ch1)
  ─────────────────────────────────
  • Governance steps ENABLED:
    - validate_data_quality (checks missing values, min rows)
    - validate_model_performance (checks accuracy, precision, recall)
  • Model tagged with environment="staging" (not "local")
  • Full 9-step DAG (vs 7 steps in local mode)

  WHAT'S THE SAME
  ───────────────
  • Same pipeline code: src/pipelines/training.py
  • Same governance hooks (MLflow logging, compliance)
  • Same Model Control Plane versioning

  IN CI/CD (train-staging.yml)
  ────────────────────────────
  • Would run on staging-stack (Vertex AI orchestrator)
  • Artifacts stored in GCS
  • Docker container built and pushed to GAR

  KEY DEMO POINT: Same code, different governance & stacks.
  The model version now shows environment="staging" in metadata.

Next: Let's compare this model against the current staging model →
"""
    )


if __name__ == "__main__":
    run()
