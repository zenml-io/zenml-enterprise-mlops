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

"""Main script to run ZenML pipelines locally.

This script is for local development. For CI/CD deployments, use
scripts/build_snapshot.py which creates immutable pipeline snapshots.

Usage:
    # Run with environment config
    python run.py --pipeline training --environment local
    python run.py --pipeline training --environment staging

    # Run with direct parameters (overrides config)
    python run.py --pipeline training --n-estimators 200

    # Other pipelines
    python run.py --pipeline batch_inference
    python run.py --pipeline champion_challenger

For real-time inference (Pipeline Deployments):
    zenml pipeline deploy src.pipelines.realtime_inference.inference_service \\
        --name readmission-api
"""

from pathlib import Path

import click
from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)


def set_stack_for_environment(environment: str, stack_override: str | None = None) -> None:
    """Set the appropriate stack based on environment.

    Args:
        environment: Environment name (local, staging, production)
        stack_override: Optional explicit stack name (overrides environment default)
    """
    client = Client()

    # Use override if provided, otherwise map from environment
    if stack_override:
        stack_name = stack_override
    else:
        stack_map = {
            "local": "dev-stack",  # GCS artifact store
            "staging": "staging-stack",
        }
        stack_name = stack_map.get(environment)

    if stack_name:
        try:
            client.activate_stack(stack_name)
            logger.info(f"Activated stack: {stack_name}")
        except KeyError:
            logger.warning(f"Stack '{stack_name}' not found, using current stack: {client.active_stack_model.name}")


@click.command()
@click.option(
    "--pipeline",
    type=click.Choice(["training", "batch_inference", "champion_challenger"]),
    default="training",
    help="Which pipeline to run",
)
@click.option(
    "--environment",
    type=click.Choice(["local", "staging", "production"]),
    default="local",
    help="Environment config to use (loads configs/{environment}.yaml)",
)
@click.option(
    "--test-size",
    type=float,
    default=None,
    help="Fraction of data for testing (overrides config)",
)
@click.option(
    "--n-estimators",
    type=int,
    default=None,
    help="Number of trees in Random Forest (overrides config)",
)
@click.option(
    "--max-depth",
    type=int,
    default=None,
    help="Maximum depth of trees (overrides config)",
)
@click.option(
    "--min-accuracy",
    type=float,
    default=None,
    help="Minimum accuracy required for validation (overrides config)",
)
@click.option(
    "--stack",
    type=str,
    default=None,
    help="Stack to use (overrides environment default: local→dev-stack, staging→staging-stack)",
)
def main(
    pipeline: str,
    environment: str,
    test_size: float | None,
    n_estimators: int | None,
    max_depth: int | None,
    min_accuracy: float | None,
    stack: str | None,
):
    """Run ZenML pipelines for patient readmission prediction.

    Uses environment-specific config from configs/{environment}.yaml.
    Command-line arguments override config file values.
    """
    config_path = Path(f"configs/{environment}.yaml")
    logger.info(f"Running {pipeline} pipeline with {environment} config...")

    if pipeline == "training":
        from src.pipelines.training import training_pipeline

        # Set stack based on environment (or use explicit override)
        set_stack_for_environment(environment, stack_override=stack)

        # Build kwargs from CLI args (only include if explicitly set)
        kwargs = {"environment": environment}  # Always pass environment for tracking
        if test_size is not None:
            kwargs["test_size"] = test_size
        if n_estimators is not None:
            kwargs["n_estimators"] = n_estimators
        if max_depth is not None:
            kwargs["max_depth"] = max_depth
        if min_accuracy is not None:
            kwargs["min_accuracy"] = min_accuracy

        # Local: fast iteration without governance
        # Staging: full governance enforcement
        if environment == "local":
            logger.info("Using local mode (no governance, simpler DAG)")
            kwargs["enable_governance"] = False
            training_pipeline(**kwargs)
        else:
            logger.info("Using staging mode (full governance)")
            kwargs["enable_governance"] = True
            # Run with config file, CLI args override config
            if config_path.exists():
                training_pipeline.with_options(config_path=str(config_path))(**kwargs)
            else:
                training_pipeline(**kwargs)


    elif pipeline == "batch_inference":
        from src.pipelines.batch_inference import batch_inference_pipeline

        batch_inference_pipeline()

    elif pipeline == "champion_challenger":
        from src.pipelines.champion_challenger import champion_challenger_pipeline

        champion_challenger_pipeline()


if __name__ == "__main__":
    main()
