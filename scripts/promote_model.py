#!/usr/bin/env python
# Apache Software License 2.0
#
# Copyright (c) ZenML GmbH 2026. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Model promotion script for WITHIN-WORKSPACE stage transitions.

This script promotes models between stages (none → staging → production) WITHIN
a single ZenML workspace. This is the appropriate script when:
- You're using a single-workspace architecture (OSS or simpler Pro setup)
- You're promoting within enterprise-dev-staging (e.g., none → staging)

For CROSS-WORKSPACE promotion (enterprise-dev-staging → enterprise-production),
use scripts/promote_cross_workspace.py instead. That script:
- Exports models to shared GCS bucket
- Imports with full metadata preservation
- Maintains audit trail across workspace boundary

2-Workspace Architecture:
- enterprise-dev-staging: Use THIS script (none → staging)
- enterprise-production: Use promote_cross_workspace.py (import from dev-staging)

Usage:
    # Promote latest model to staging (within dev-staging workspace)
    python scripts/promote_model.py --model breast_cancer_classifier --to-stage staging

    # Promote specific version to staging
    python scripts/promote_model.py --model breast_cancer_classifier --version 1.2.3 --to-stage staging

    # Promote from staging stage (still within same workspace)
    python scripts/promote_model.py --model breast_cancer_classifier --from-stage staging --to-stage production
"""

import click
from zenml.client import Client
from zenml.enums import ModelStages
from zenml.logger import get_logger

logger = get_logger(__name__)


def find_latest_with_metrics(client: Client, model_name: str) -> "ModelVersionResponse":
    """Find the latest model version that has metrics logged.

    When pipeline runs are fully cached, ZenML still creates a new model version
    but metrics aren't logged. This function finds the most recent version that
    actually has metrics for promotion validation.

    Args:
        client: ZenML client
        model_name: Name of the model

    Returns:
        The latest model version with metrics

    Raises:
        ValueError: If no version with metrics is found
    """
    required_metrics = ["accuracy", "precision", "recall"]
    versions = client.list_model_versions(model=model_name, size=20)

    # Sort by version number descending to get latest first
    sorted_versions = sorted(versions, key=lambda v: v.number, reverse=True)

    for version in sorted_versions:
        metrics = version.run_metadata
        if metrics and all(m in metrics for m in required_metrics):
            logger.info(f"Found version {version.number} with metrics")
            return version

    raise ValueError(
        f"No model version found with required metrics: {required_metrics}. "
        f"Run the training pipeline first."
    )


def validate_promotion(model_version, to_stage: str) -> bool:
    """Validate that model meets requirements for promotion.

    Args:
        model_version: Model version to validate
        to_stage: Target stage to promote to

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    # Get model metrics
    metrics = model_version.run_metadata

    # Check if required metrics exist
    required_metrics = ["accuracy", "precision", "recall"]
    missing_metrics = [m for m in required_metrics if m not in metrics]

    if missing_metrics:
        raise ValueError(
            f"Model missing required metrics for {to_stage} promotion: "
            f"{missing_metrics}"
        )

    # Define minimum requirements per stage
    requirements = {
        "staging": {
            "accuracy": 0.7,
            "precision": 0.7,
            "recall": 0.7,
        },
        "production": {
            "accuracy": 0.8,
            "precision": 0.8,
            "recall": 0.8,
        },
    }

    stage_requirements = requirements.get(to_stage, {})

    # Validate metrics
    failures = []
    for metric, min_value in stage_requirements.items():
        # Metrics are already stored as metadata values
        metric_obj = metrics.get(metric)
        actual_value = (
            float(metric_obj.value)
            if hasattr(metric_obj, "value")
            else float(metric_obj)
        )
        if actual_value < min_value:
            failures.append(
                f"{metric}: {actual_value:.3f} < {min_value:.3f} (required)"
            )

    if failures:
        failure_msg = (
            f"Model does not meet {to_stage} promotion requirements:\n"
            + "\n".join(f"  - {f}" for f in failures)
        )
        raise ValueError(failure_msg)

    logger.info(f"✅ Model validation passed for {to_stage} promotion")
    return True


@click.command()
@click.option(
    "--model",
    type=str,
    required=True,
    help="Name of the model to promote",
)
@click.option(
    "--version",
    type=str,
    default=None,
    help="Specific version to promote (defaults to latest)",
)
@click.option(
    "--from-stage",
    type=click.Choice(["staging", "production", "latest"]),
    default=None,
    help="Promote from this stage (e.g., staging -> production)",
)
@click.option(
    "--to-stage",
    type=click.Choice(["staging", "production", "archived"]),
    required=True,
    help="Stage to promote to",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force promotion even if another model is in target stage",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    default=False,
    help="Skip validation checks (use with caution!)",
)
def promote_model(
    model: str,
    version: str,
    from_stage: str,
    to_stage: str,
    force: bool,
    skip_validation: bool,
):
    """Promote a model to a new stage with validation.

    This script is used in GitOps workflows to promote models between
    environments (e.g., staging -> production) with proper validation
    and audit logging.
    """
    client = Client()

    logger.info("🚀 Model Promotion Script")
    logger.info(f"Model: {model}")
    logger.info(f"Target stage: {to_stage}")

    try:
        # Determine which version to promote
        if version:
            logger.info(f"Promoting specific version: {version}")
            model_version = client.get_model_version(model, version)
        elif from_stage:
            logger.info(f"Promoting from stage: {from_stage}")
            # Map string stage to ModelStages enum
            stage_map = {
                "staging": ModelStages.STAGING,
                "production": ModelStages.PRODUCTION,
                "latest": ModelStages.LATEST,
            }
            model_version = client.get_model_version(model, stage_map[from_stage])
        else:
            logger.info("Finding latest version with metrics...")
            model_version = find_latest_with_metrics(client, model)

        logger.info(f"Model version: {model_version.number}")
        logger.info(f"Current stage: {model_version.stage}")

        # Validate promotion (unless skipped)
        if not skip_validation:
            logger.info("Running promotion validation checks...")
            validate_promotion(model_version, to_stage)
        else:
            logger.warning("⚠️  Skipping validation checks (--skip-validation)")

        # Check if another model is in target stage
        try:
            current_model_in_stage = client.get_model_version(
                model,
                ModelStages.STAGING
                if to_stage == "staging"
                else ModelStages.PRODUCTION,
            )
            if current_model_in_stage.number != model_version.number:
                if not force:
                    logger.error(
                        f"Model version {current_model_in_stage.number} is already in {to_stage}. "
                        f"Use --force to demote it."
                    )
                    raise ValueError(f"Another model is already in {to_stage} stage")
                else:
                    logger.warning(
                        f"Demoting version {current_model_in_stage.number} from {to_stage}"
                    )
        except KeyError:
            # No model in target stage, proceed
            pass

        # Perform promotion
        logger.info(f"Promoting model to {to_stage}...")

        # Map string stage to ModelStages enum
        stage_map = {
            "staging": ModelStages.STAGING,
            "production": ModelStages.PRODUCTION,
            "archived": ModelStages.ARCHIVED,
        }

        model_version.set_stage(stage=stage_map[to_stage], force=force)

        logger.info(
            f"✅ Successfully promoted {model} v{model_version.number} to {to_stage}!"
        )
        logger.info(
            f"Dashboard: https://cloud.zenml.io/workspaces/zenml-projects/projects/.../model-versions/{model_version.id}"
        )

        # Log promotion event for audit trail
        logger.info("📋 Promotion logged for compliance audit trail")

    except Exception as e:
        logger.error(f"❌ Promotion failed: {e!s}")
        raise


if __name__ == "__main__":
    promote_model()
