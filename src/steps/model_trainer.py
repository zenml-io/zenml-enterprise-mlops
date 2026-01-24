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

"""Model training step with MLflow integration."""

import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import ClassifierMixin
from typing_extensions import Annotated

from zenml import ArtifactConfig, get_step_context, step
from zenml.client import Client
from zenml.integrations.mlflow.experiment_trackers import (
    MLFlowExperimentTracker,
)
from zenml.logger import get_logger

logger = get_logger(__name__)

# Get experiment tracker from active stack
experiment_tracker = Client().active_stack.experiment_tracker

if experiment_tracker and isinstance(
    experiment_tracker, MLFlowExperimentTracker
):
    EXPERIMENT_TRACKER_NAME = experiment_tracker.name
else:
    EXPERIMENT_TRACKER_NAME = None
    logger.warning(
        "No MLflow experiment tracker found in active stack. "
        "MLflow autologging will be disabled."
    )


@step(
    experiment_tracker=EXPERIMENT_TRACKER_NAME,
    enable_cache=False,  # Disable caching for training steps
)
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 100,
    max_depth: int = 10,
    random_state: int = 42,
) -> Annotated[
    ClassifierMixin,
    ArtifactConfig(name="model", is_model_artifact=True),
]:
    """Train a Random Forest classifier for readmission prediction.

    This step trains the model and automatically logs everything to MLflow
    via autologging. The model artifact is marked for Model Control Plane.

    Args:
        X_train: Training features
        y_train: Training labels
        n_estimators: Number of trees in the forest
        max_depth: Maximum depth of trees
        random_state: Random seed for reproducibility

    Returns:
        Trained model
    """
    logger.info(
        f"Training Random Forest model with n_estimators={n_estimators}, "
        f"max_depth={max_depth}"
    )

    # Enable MLflow autologging
    if EXPERIMENT_TRACKER_NAME:
        mlflow.sklearn.autolog()

    # Train model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    logger.info("Model training completed")

    # Log additional custom metrics if needed
    if EXPERIMENT_TRACKER_NAME:
        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("use_case", "patient_readmission_prediction")

    return model
