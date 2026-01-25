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

"""Main script to run ZenML pipelines.

Usage:
    python run.py --pipeline training
    python run.py --pipeline training --n-estimators 200
    python run.py --pipeline batch_inference
    python run.py --pipeline champion_challenger

For real-time inference (Pipeline Deployments):
    zenml pipeline deploy src.pipelines.realtime_inference.inference_service \\
        --name readmission-api
"""

import click
from zenml.logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.option(
    "--pipeline",
    type=click.Choice(["training", "batch_inference", "champion_challenger"]),
    default="training",
    help="Which pipeline to run",
)
@click.option(
    "--test-size",
    type=float,
    default=0.2,
    help="Fraction of data for testing",
)
@click.option(
    "--n-estimators",
    type=int,
    default=100,
    help="Number of trees in Random Forest",
)
@click.option(
    "--max-depth",
    type=int,
    default=10,
    help="Maximum depth of trees",
)
@click.option(
    "--min-accuracy",
    type=float,
    default=0.7,
    help="Minimum accuracy required for validation",
)
def main(
    pipeline: str,
    test_size: float,
    n_estimators: int,
    max_depth: int,
    min_accuracy: float,
):
    """Run ZenML pipelines for patient readmission prediction.

    This script provides a simple CLI interface to run different pipelines.
    """
    logger.info(f"Running {pipeline} pipeline...")

    if pipeline == "training":
        from src.pipelines.training import training_pipeline

        training_pipeline(
            test_size=test_size,
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_accuracy=min_accuracy,
        )
        logger.info("Training pipeline completed successfully!")

    elif pipeline == "batch_inference":
        from src.pipelines.batch_inference import batch_inference_pipeline

        batch_inference_pipeline()
        logger.info("Batch inference pipeline completed successfully!")

    elif pipeline == "champion_challenger":
        from src.pipelines.champion_challenger import champion_challenger_pipeline

        champion_challenger_pipeline()
        logger.info("Champion/Challenger comparison completed successfully!")

    logger.info(
        "\nCheck the ZenML dashboard for detailed results: http://localhost:8237"
    )


if __name__ == "__main__":
    main()
