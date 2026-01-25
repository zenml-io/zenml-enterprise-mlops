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

"""Utilities for MLflow experiment tracking integration."""

from typing import Optional

from zenml.logger import get_logger

logger = get_logger(__name__)

__all__ = ["get_experiment_tracker_name"]


def get_experiment_tracker_name() -> Optional[str]:
    """Get the MLflow experiment tracker name from the active stack.

    This function safely attempts to detect an MLflow experiment tracker
    in the active ZenML stack. It includes proper error handling to ensure
    graceful degradation if ZenML Client cannot be initialized or if no
    MLflow tracker is configured.

    Returns:
        Name of the MLflow experiment tracker if available, None otherwise
    """
    try:
        from zenml.client import Client
        from zenml.integrations.mlflow.experiment_trackers import (
            MLFlowExperimentTracker,
        )

        client = Client()
        experiment_tracker = client.active_stack.experiment_tracker

        if experiment_tracker and isinstance(
            experiment_tracker, MLFlowExperimentTracker
        ):
            logger.info(
                f"MLflow experiment tracker detected: {experiment_tracker.name}"
            )
            return experiment_tracker.name
        else:
            logger.info(
                "No MLflow experiment tracker found in active stack. "
                "MLflow tracking will be disabled."
            )
            return None

    except Exception as e:
        logger.warning(
            f"Could not determine experiment tracker: {e}. "
            "MLflow tracking will be disabled."
        )
        return None
