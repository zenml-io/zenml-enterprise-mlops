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
                model="breast_cancer_classifier",
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
            "breast_cancer_classifier",
            ModelStages.LATEST,
        )

        print(f"Model: breast_cancer_classifier v{latest.number}\n")

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
        print(f"Artifacts for v{latest.number}:\n")

        # Use the new API to get artifact names
        artifact_names = ["model", "scaler", "X_train", "X_test", "y_train", "y_test"]
        found_any = False

        for name in artifact_names:
            try:
                artifact = latest.get_artifact(name)
                if artifact:
                    found_any = True
                    print(f"   📦 {name}")
                    print(f"      Type: {artifact.type}")
                    uri = str(artifact.uri) if artifact.uri else "N/A"
                    if len(uri) > 50:
                        uri = uri[:50] + "..."
                    print(f"      URI: {uri}")
            except KeyError:
                pass  # Artifact not found, skip
            except Exception:
                pass  # Other error, skip

        if not found_any:
            print("   Artifacts linked to model (check dashboard for full list)")

        # Get pipeline run info
        print("\n   🔄 Pipeline Run Info:")
        print(f"      Model ID: {latest.id}")
        print(f"      Created: {str(latest.created)[:19]}")
        if latest.updated:
            print(f"      Updated: {str(latest.updated)[:19]}")

    except Exception as e:
        print(f"   Could not get lineage info: {e}")

    print_section("💡 Loading Artifacts Programmatically")
    print(
        """
To load artifacts from a model version in your code:

    from zenml.client import Client
    from zenml.enums import ModelStages

    # Get the production model
    client = Client()
    model = client.get_model_version(
        "breast_cancer_classifier",
        ModelStages.PRODUCTION
    )

    # Load specific artifacts
    classifier = model.get_artifact("model")
    scaler = model.get_artifact("scaler")

    # Use them for inference
    X_scaled = scaler.transform(new_data)
    predictions = classifier.predict(X_scaled)

This is how batch_inference_pipeline loads the production model!
"""
    )

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
