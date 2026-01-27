"""Chapter 5: Promote to Production (Cross-Workspace).

Demonstrates:
- Cross-workspace model promotion (dev-staging → production)
- Model export/import with metadata preservation
- Audit trail across workspaces
- GitOps release workflow

In two-workspace mode, this calls scripts/promote_cross_workspace.py.
In single-workspace mode, falls back to scripts/promote_model.py.
"""

import subprocess
import sys


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run(two_workspace: bool = False):
    """Run Chapter 5: Promote to Production."""

    if two_workspace:
        _run_two_workspace()
    else:
        _run_single_workspace()


def _run_two_workspace():
    """Cross-workspace promotion: dev-staging → production."""

    print_section("🎯 What We're Demonstrating")
    print("  🔧 Workspace: enterprise-dev-staging → 🏭 enterprise-production\n")
    print(
        """
Cross-workspace model promotion exports a validated model from
dev-staging and imports it into the production workspace.

Key points to highlight:
  ✓ Model exported with all metadata (metrics, git commit, lineage)
  ✓ Imported into production workspace with audit trail
  ✓ ZenML version upgrade isolation (workspaces upgrade independently)
  ✓ Single lineage break at staging → production boundary
"""
    )

    print_section("📋 Cross-Workspace Promotion Flow")
    print(
        """
  enterprise-dev-staging                 enterprise-production
  ┌────────────────────────┐            ┌────────────────────────┐
  │ Model v3 (staging)     │            │                        │
  │   ├── metrics          │  EXPORT    │  Model v3 (production) │
  │   ├── artifacts        │ ────────▶  │   ├── metrics          │
  │   ├── git commit       │            │   ├── source metadata  │
  │   └── training lineage │            │   └── audit trail      │
  └────────────────────────┘            └────────────────────────┘

  The export preserves:
  • All model metrics (accuracy, precision, recall, f1)
  • Source workspace, version, and git commit
  • Promotion timestamp and operator identity
  • Full audit trail for regulatory compliance
"""
    )

    print_section("🔍 Checking Staging Model in dev-staging")

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

        print(f"  Staging Model: v{staging.number}")

        metrics = staging.run_metadata
        for key in ["accuracy", "precision", "recall"]:
            if key in metrics:
                val_obj = metrics[key]
                val = float(val_obj.value if hasattr(val_obj, "value") else val_obj)
                print(f"    {key}: {val:.4f}")

    except Exception as e:
        print(f"  Could not check metrics: {e}")
        return

    print_section("🚀 Cross-Workspace Promotion")

    cmd = [
        sys.executable,
        "scripts/promote_cross_workspace.py",
        "--model", "breast_cancer_classifier",
        "--source-workspace", "enterprise-dev-staging",
        "--dest-workspace", "enterprise-production",
        "--source-stage", "staging",
        "--dest-stage", "production",
        "--skip-validation",
    ]
    print(f"  Executing: {' '.join(cmd[1:])}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ Cross-workspace promotion successful!")
            print("   Model is now available in enterprise-production workspace.")
        else:
            print(f"\n⚠️  Promotion failed (exit code: {result.returncode})")

    except subprocess.TimeoutExpired:
        print("\n⏱️  Promotion timed out")
    except FileNotFoundError:
        print("\n⚠️  Script not found - running from wrong directory?")

    print_section("🔍 Audit Trail Metadata")
    print(
        """
The promoted model in production carries metadata linking back to source:

  production model metadata:
    source_workspace: enterprise-dev-staging
    source_version: v3
    source_stage: staging
    promotion_timestamp: 2026-01-27T10:30:00Z
    git_commit: abc123
    promoted_by: platform-admin

This enables full traceability for regulatory audits.
"""
    )

    print_section("🔄 GitOps Production Release")
    print(
        """
In production, this is triggered by a GitHub Release:

  .github/workflows/promote-to-production.yml:

    1. Create GitHub Release (tag: v1.0.0)
    2. Workflow triggers automatically
    3. Runs promote_cross_workspace.py
    4. Exports from enterprise-dev-staging
    5. Imports into enterprise-production
    6. Creates audit log entry

Benefits:
  • Release notes document the change
  • Cross-workspace promotion with full metadata
  • ZenML versions can be upgraded independently
  • Easy rollback via previous release

Next: Let's run batch inference in the production workspace →
"""
    )


def _run_single_workspace():
    """Fallback: within-workspace promotion (staging → production)."""

    print_section("🎯 What We're Demonstrating")
    print("  Mode: Single-Workspace (fallback)\n")
    print(
        """
Promotion to PRODUCTION has STRICTER requirements than staging.

Key points to highlight:
  ✓ Higher performance thresholds (80% vs 70%)
  ✓ Must come from STAGING (validated path)
  ✓ Requires --force to replace existing production model
  ✓ Complete audit trail for compliance

Note: In 2-workspace mode, this uses cross-workspace promotion instead.
      Set ZENML_DEV_STAGING_URL/API_KEY and ZENML_PRODUCTION_URL/API_KEY
      in .env to enable.
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
                "--force",
                "--skip-validation",
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

  .github/workflows/promote-to-production.yml:

    1. Create GitHub Release (tag: v1.0.0)
    2. Workflow triggers automatically
    3. Runs cross-workspace promotion (2-workspace mode)
    4. Or within-workspace promotion (single-workspace mode)
    5. Creates audit log entry

Next: Let's run batch inference with the production model →
"""
    )


if __name__ == "__main__":
    run()
