"""Chapter 2: Explore Model Control Plane.

Demonstrates:
- Single source of truth for all models
- Complete lineage tracking
- Metadata and metrics access
- Audit trail for compliance
"""


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def run():
    """Run Chapter 2: Model Control Plane exploration."""

    print_section("🎯 What We're Demonstrating")
    print(
        """
The Model Control Plane is the SINGLE SOURCE OF TRUTH for all models.

Key points to highlight:
  ✓ Every model version tracked with full metadata
  ✓ Complete lineage from prediction → training data → code
  ✓ All artifacts accessible programmatically
  ✓ Audit trail for regulatory compliance (HIPAA, GDPR, etc.)
"""
    )

    print_section("🔍 Exploring the Model Registry")

    try:
        from zenml.client import Client
        from zenml.enums import ModelStages

        client = Client()

        # List all versions
        print("📋 All Model Versions:\n")
        try:
            versions = client.list_model_versions(
                model="patient_readmission_predictor",
            )

            if not versions:
                print("   No model versions found. Run Chapter 1 first!")
                return

            print(f"{'Version':<10} {'Stage':<15} {'Created':<25}")
            print("-" * 50)

            for v in versions:
                # Handle stage which could be enum, string, or None
                if v.stage is None:
                    stage = "none"
                elif hasattr(v.stage, "value"):
                    stage = v.stage.value
                else:
                    stage = str(v.stage)
                created = str(v.created)[:19] if v.created else "unknown"
                print(f"{v.number:<10} {stage:<15} {created:<25}")

        except Exception as e:
            print(f"   Could not list versions: {e}")
            print("   Run Chapter 1 first to create a model.")
            return

    except ImportError:
        print("   ZenML not installed. Run: pip install zenml")
        return

    print_section("📊 Latest Model Metrics")

    try:
        # Get latest version
        latest = client.get_model_version(
            "patient_readmission_predictor",
            ModelStages.LATEST,
        )

        print(f"Model: patient_readmission_predictor v{latest.number}\n")

        metrics = latest.run_metadata
        if metrics:
            print("Performance Metrics:")
            for key, value in metrics.items():
                val = value.value if hasattr(value, "value") else value
                if isinstance(val, float):
                    print(f"   {key}: {val:.4f}")
                elif key in ["accuracy", "precision", "recall", "f1_score"]:
                    print(f"   {key}: {val}")
        else:
            print("   No metrics found on this version.")

    except Exception as e:
        print(f"   Could not get latest model: {e}")

    print_section("🔗 Lineage & Artifacts")

    try:
        # Get artifacts
        print(f"Artifacts for v{latest.number}:\n")

        artifacts = latest.data_artifacts
        if artifacts:
            for name, artifact_list in artifacts.items():
                print(f"   📦 {name}")
                for art in artifact_list[:1]:  # Just show first
                    print(f"      URI: {art.uri[:60]}...")
        else:
            print("   No artifacts found.")

        # Pipeline runs
        runs = latest.pipeline_runs
        if runs:
            run = runs[0]
            print(f"\n   🔄 Training Pipeline: {run.name}")
            print(f"      Status: {run.status}")
            print(f"      Started: {str(run.start_time)[:19]}")

    except Exception as e:
        print(f"   Could not get lineage info: {e}")

    print_section("🏷️ Model Stages Explained")
    print(
        """
Models progress through stages:

  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   LATEST    │ ──▶ │   STAGING   │ ──▶ │ PRODUCTION  │
  │  (created)  │     │ (validated) │     │   (live)    │
  └─────────────┘     └─────────────┘     └─────────────┘

  • LATEST: New model version, not yet validated
  • STAGING: Passed validation, ready for comparison
  • PRODUCTION: Serving live predictions
  • ARCHIVED: Deprecated, kept for audit

Stage transitions require validation gates!

Next: Let's promote a model to staging →
"""
    )


if __name__ == "__main__":
    run()
