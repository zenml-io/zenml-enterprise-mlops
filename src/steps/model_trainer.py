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

from typing import Annotated

import mlflow
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from zenml import ArtifactConfig, ArtifactType, step
from zenml.logger import get_logger

from src.utils import get_experiment_tracker_name

logger = get_logger(__name__)


@step(enable_cache=False)
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 100,
    max_depth: int = 10,
    random_state: int = 42,
) -> Annotated[
    ClassifierMixin,
    ArtifactConfig(name="model", artifact_type=ArtifactType.MODEL),
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

    # Get experiment tracker name (evaluated at step runtime, not import time)
    experiment_tracker_name = get_experiment_tracker_name()

    # Enable MLflow autologging if tracker is available
    if experiment_tracker_name:
        mlflow.sklearn.autolog()
        logger.info(
            f"MLflow autologging enabled with tracker: {experiment_tracker_name}"
        )

    # Train model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    logger.info("Model training completed")

    # Log additional custom metrics if MLflow is available
    if experiment_tracker_name:
        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("use_case", "patient_readmission_prediction")

    return model
