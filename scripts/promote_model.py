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

"""Model promotion script for GitOps workflows.

This script promotes models between stages based on validation criteria.
Typically triggered by GitHub Actions on PR merge or release creation.

Usage:
    # Promote latest model to staging
    python scripts/promote_model.py --model patient_readmission_predictor --to-stage staging

    # Promote specific version to production
    python scripts/promote_model.py --model patient_readmission_predictor --version 1.2.3 --to-stage production

    # Promote latest staging to production
    python scripts/promote_model.py --model patient_readmission_predictor --from-stage staging --to-stage production
"""

import click
from zenml.client import Client
from zenml.enums import ModelStages
from zenml.logger import get_logger

logger = get_logger(__name__)


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
        actual_value = float(metric_obj.value) if hasattr(metric_obj, 'value') else float(metric_obj)
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

    logger.info(f"🚀 Model Promotion Script")
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
            model_version = client.get_model_version(
                model, stage_map[from_stage]
            )
        else:
            logger.info("Promoting latest version")
            model_version = client.get_model_version(model, ModelStages.LATEST)

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
            if current_model_in_stage.version != model_version.number:
                if not force:
                    logger.error(
                        f"Model version {current_model_in_stage.version} is already in {to_stage}. "
                        f"Use --force to demote it."
                    )
                    raise ValueError(
                        f"Another model is already in {to_stage} stage"
                    )
                else:
                    logger.warning(
                        f"Demoting version {current_model_in_stage.version} from {to_stage}"
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

        logger.info(f"✅ Successfully promoted {model} v{model_version.number} to {to_stage}!")
        logger.info(
            f"Dashboard: https://cloud.zenml.io/workspaces/zenml-projects/projects/.../model-versions/{model_version.id}"
        )

        # Log promotion event for audit trail
        logger.info("📋 Promotion logged for compliance audit trail")

    except Exception as e:
        logger.error(f"❌ Promotion failed: {str(e)}")
        raise


if __name__ == "__main__":
    promote_model()
