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

"""Model rollback script for emergency recovery.

This script handles rollback scenarios when a promoted model underperforms:
1. Demotes the current production model
2. Promotes the previous production model back
3. Logs the rollback event for audit trail

Usage:
    # Rollback production to previous version
    python scripts/rollback_model.py --model patient_readmission_predictor

    # Rollback to a specific version
    python scripts/rollback_model.py --model patient_readmission_predictor --to-version 3

    # Dry run (show what would happen)
    python scripts/rollback_model.py --model patient_readmission_predictor --dry-run
"""

import click
from zenml.client import Client
from zenml.enums import ModelStages
from zenml.logger import get_logger

logger = get_logger(__name__)

MODEL_NAME = "patient_readmission_predictor"


def get_previous_production_version(
    client: Client, model_name: str, current_version: int
):
    """Find the most recent version that was previously in production.

    Searches through model versions to find the one that was in production
    before the current one, based on version number and metadata.
    """
    model = client.get_model(model_name)
    versions = client.list_model_versions(
        model_name_or_id=model.id, sort_by="desc:number"
    )

    # Find versions that are archived (previously promoted) or have production history
    for mv in versions:
        if mv.number < current_version:
            # Check if this version was ever in production (has production metadata)
            if mv.stage == ModelStages.ARCHIVED or mv.number == current_version - 1:
                return mv

    return None


@click.command()
@click.option(
    "--model",
    type=str,
    default=MODEL_NAME,
    help="Name of the model to rollback",
)
@click.option(
    "--to-version",
    type=int,
    default=None,
    help="Specific version to rollback to (defaults to previous production)",
)
@click.option(
    "--reason",
    type=str,
    default=None,
    help="Reason for rollback (logged for audit trail)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would happen without making changes",
)
def rollback_model(
    model: str,
    to_version: int | None,
    reason: str | None,
    dry_run: bool,
):
    """Rollback a model to a previous version.

    This script handles emergency rollback scenarios when a promoted model
    underperforms in production. It:

    1. Identifies the current production model
    2. Demotes it to 'archived' stage
    3. Promotes the previous (or specified) version back to production
    4. Logs the rollback event for compliance audit trail

    The rollback is atomic - if any step fails, no changes are made.
    """
    client = Client()

    logger.info("🔄 Model Rollback Script")
    logger.info(f"Model: {model}")

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")

    try:
        # Get current production model
        try:
            current_prod = client.get_model_version(model, ModelStages.PRODUCTION)
            logger.info(f"Current production: v{current_prod.number}")
        except KeyError:
            logger.error("No model currently in production. Nothing to rollback.")
            raise click.Abort()

        # Determine rollback target
        if to_version:
            logger.info(f"Rolling back to specified version: v{to_version}")
            rollback_target = client.get_model_version(model, to_version)
        else:
            logger.info("Finding previous production version...")
            rollback_target = get_previous_production_version(
                client, model, current_prod.number
            )

            if rollback_target is None:
                logger.error(
                    "Could not find a previous production version. "
                    "Use --to-version to specify explicitly."
                )
                raise click.Abort()

            logger.info(f"Found previous version: v{rollback_target.number}")

        # Validate rollback target
        if rollback_target.number == current_prod.number:
            logger.error("Rollback target is the same as current production!")
            raise click.Abort()

        # Show rollback plan
        logger.info("")
        logger.info("📋 Rollback Plan:")
        logger.info(f"  1. Demote v{current_prod.number} from production → archived")
        logger.info(f"  2. Promote v{rollback_target.number} to production")
        if reason:
            logger.info(f"  Reason: {reason}")
        logger.info("")

        if dry_run:
            logger.info("✅ Dry run complete. Use without --dry-run to execute.")
            return

        # Execute rollback
        logger.info("Executing rollback...")

        # Step 1: Demote current production
        logger.info(f"Demoting v{current_prod.number} to archived...")
        current_prod.set_stage(stage=ModelStages.ARCHIVED, force=True)

        # Step 2: Promote rollback target
        logger.info(f"Promoting v{rollback_target.number} to production...")
        rollback_target.set_stage(stage=ModelStages.PRODUCTION, force=True)

        # Step 3: Log rollback metadata for audit trail
        rollback_metadata = {
            "rollback_event": {
                "from_version": current_prod.number,
                "to_version": rollback_target.number,
                "reason": reason or "Not specified",
                "triggered_by": "scripts/rollback_model.py",
            }
        }
        rollback_target.log_metadata(rollback_metadata)

        logger.info("")
        logger.info("✅ Rollback completed successfully!")
        logger.info(f"  Previous production: v{current_prod.number} → archived")
        logger.info(f"  New production: v{rollback_target.number}")
        logger.info("")
        logger.info("📋 Rollback logged for compliance audit trail")

        # Provide next steps
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Verify the rollback in the ZenML dashboard")
        logger.info("  2. Monitor model performance in Arize/monitoring")
        logger.info("  3. Investigate why the demoted model underperformed")
        logger.info("  4. Create a post-mortem if this was a production incident")

    except click.Abort:
        raise
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e!s}")
        logger.error("No changes were made to model stages.")
        raise


if __name__ == "__main__":
    rollback_model()
