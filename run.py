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

"""Run ZenML pipelines locally.

Usage:
    python run.py                                        # training, local mode
    python run.py --pipeline batch_inference             # other pipelines
    python run.py --environment staging                  # with governance hooks
    python run.py --environment staging --stack my-stack # explicit stack
"""

from pathlib import Path

import click
from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)

# Config files per environment (docker settings, parameters, etc.)
CONFIG_DIR = Path("configs")

# Default stacks per environment
STACK_DEFAULTS = {
    "local": "dev-stack",
    "staging": "staging-stack",
}


def activate_stack(stack_name: str) -> None:
    """Activate a stack, with fallback to current stack if not found."""
    client = Client()
    try:
        client.activate_stack(stack_name)
        logger.info(f"Using stack: {stack_name}")
    except KeyError:
        logger.warning(f"Stack '{stack_name}' not found, using: {client.active_stack_model.name}")


@click.command()
@click.option(
    "--pipeline",
    type=click.Choice(["training", "batch_inference", "champion_challenger"]),
    default="training",
)
@click.option(
    "--environment",
    type=click.Choice(["local", "staging"]),
    default="local",
    help="local = fast iteration, staging = with governance hooks",
)
@click.option(
    "--stack",
    type=str,
    default=None,
    help="Stack to use (default: dev-stack for local, staging-stack for staging)",
)
def main(pipeline: str, environment: str, stack: str | None):
    """Run ZenML pipelines for patient readmission prediction."""
    # Set stack (explicit override or environment default)
    stack_name = stack or STACK_DEFAULTS.get(environment)
    if stack_name:
        activate_stack(stack_name)

    logger.info(f"Running {pipeline} pipeline ({environment} mode)")

    if pipeline == "training":
        from src.pipelines.training import training_pipeline

        # Load config (docker settings, parameters, tags, etc.)
        config_path = CONFIG_DIR / f"{environment}.yaml"
        if config_path.exists():
            pipeline_to_run = training_pipeline.with_options(config_path=str(config_path))
            logger.info(f"Loaded config: {config_path}")
        else:
            pipeline_to_run = training_pipeline

        if environment == "local":
            # Local: fast iteration, no governance steps or hooks
            pipeline_to_run(environment=environment, enable_governance=False)
        else:
            # Staging: add governance hooks
            from governance.hooks import (
                pipeline_failure_hook,
                pipeline_governance_success_hook,
            )

            pipeline_to_run.with_options(
                on_success=pipeline_governance_success_hook,
                on_failure=pipeline_failure_hook,
            )(environment=environment, enable_governance=True)

    elif pipeline == "batch_inference":
        from src.pipelines.batch_inference import batch_inference_pipeline

        batch_inference_pipeline()

    elif pipeline == "champion_challenger":
        from src.pipelines.champion_challenger import champion_challenger_pipeline

        champion_challenger_pipeline()


if __name__ == "__main__":
    main()
