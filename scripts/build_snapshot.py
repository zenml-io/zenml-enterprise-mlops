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

"""Build pipeline snapshots for GitOps workflows.

Pipeline snapshots are a ZenML Pro feature that enables:
- Version-controlled pipeline definitions
- Immutable pipeline deployments
- GitOps-style promotion workflows
- Triggered execution via API/UI

This script creates snapshots for staging and production environments,
typically called from CI/CD (GitHub Actions).

2-Workspace Architecture:
- enterprise-dev-staging: Create training + staging inference snapshots
- enterprise-production: Create production inference snapshots

NOTE: Connect to the appropriate workspace before running this script:
    zenml login enterprise-dev-staging --api-key $ZENML_DEV_STAGING_API_KEY
    zenml login enterprise-production --api-key $ZENML_PRODUCTION_API_KEY

Usage:
    # Staging training (in enterprise-dev-staging workspace)
    python scripts/build_snapshot.py --environment staging --stack staging-stack --run

    # Production inference (in enterprise-production workspace)
    python scripts/build_snapshot.py --environment production --stack gcp-stack --pipeline batch_inference
"""

import os
from typing import Optional

import click
from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)

SNAPSHOT_PREFIX = "readmission_model"


def get_snapshot_name(
    environment: str,
    git_sha: Optional[str] = None,
) -> str:
    """Generate a snapshot name following GitOps conventions.

    Args:
        environment: "staging" or "production"
        git_sha: Git commit SHA (from CI/CD)

    Returns:
        Snapshot name like "STG_readmission_model_abc1234"
    """
    env_prefix = "STG" if environment == "staging" else "PROD"

    if git_sha:
        short_sha = git_sha[:7]
        return f"{env_prefix}_{SNAPSHOT_PREFIX}_{short_sha}"
    else:
        return f"{env_prefix}_{SNAPSHOT_PREFIX}_local"


@click.command()
@click.option(
    "--environment",
    type=click.Choice(["staging", "production"]),
    default="staging",
    show_default=True,
    help="Environment to build snapshot for",
)
@click.option(
    "--stack",
    type=str,
    required=True,
    help="Stack to use for the snapshot",
)
@click.option(
    "--name",
    type=str,
    default=None,
    help="Custom snapshot name (auto-generated if not provided)",
)
@click.option(
    "--git-sha",
    type=str,
    default=None,
    envvar="ZENML_GITHUB_SHA",
    help="Git SHA for snapshot naming (auto from ZENML_GITHUB_SHA env var)",
)
@click.option(
    "--run",
    is_flag=True,
    help="Trigger pipeline run immediately after creating snapshot",
)
@click.option(
    "--pipeline",
    type=click.Choice(["training", "batch_inference"]),
    default="training",
    help="Which pipeline to snapshot",
)
def main(
    environment: str,
    stack: str,
    name: Optional[str] = None,
    git_sha: Optional[str] = None,
    run: bool = False,
    pipeline: str = "training",
):
    """Build a pipeline snapshot for deployment.

    Snapshots enable GitOps workflows:
    - Staging: Create snapshot AND run (continuous training)
    - Production: Create snapshot only (manual approval to run)
    """
    client = Client()

    # Set active stack
    remote_stack = client.get_stack(stack)
    os.environ["ZENML_ACTIVE_STACK_ID"] = str(remote_stack.id)
    logger.info(f"Using stack: {remote_stack.name}")

    # Generate snapshot name if not provided
    if name is None:
        name = get_snapshot_name(environment=environment, git_sha=git_sha)

    logger.info(f"Creating snapshot: {name}")
    logger.info(f"Environment: {environment}")
    logger.info(f"Pipeline: {pipeline}")

    # Import and snapshot the appropriate pipeline
    if pipeline == "training":
        from src.pipelines.training import training_pipeline

        snapshot = training_pipeline.with_options(
            config_path=f"configs/{environment}.yaml",
        ).create_snapshot(name=name)

    elif pipeline == "batch_inference":
        from src.pipelines.batch_inference import batch_inference_pipeline

        snapshot = batch_inference_pipeline.create_snapshot(name=name)

    logger.info(f"Snapshot created: {snapshot.id}")
    logger.info(f"   Name: {snapshot.name}")

    # Optionally trigger the run
    if run:
        logger.info("Triggering pipeline run from snapshot...")

        run_config = snapshot.config_template
        run_response = client.trigger_pipeline(
            snapshot_name_or_id=snapshot.id,
            run_configuration=run_config,
        )

        logger.info(f"Pipeline run triggered: {run_response.id}")
    else:
        logger.info(
            "Snapshot created but not run. Trigger manually via UI or API when ready."
        )


if __name__ == "__main__":
    main()
