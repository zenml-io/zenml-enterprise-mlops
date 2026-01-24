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

"""Model evaluation step with comprehensive metrics."""

import mlflow
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from typing import Dict
from typing_extensions import Annotated

from zenml import get_step_context, log_metadata, step
from zenml.client import Client
from zenml.integrations.mlflow.experiment_trackers import (
    MLFlowExperimentTracker,
)
from zenml.logger import get_logger

logger = get_logger(__name__)

# Get experiment tracker
experiment_tracker = Client().active_stack.experiment_tracker
EXPERIMENT_TRACKER_NAME = (
    experiment_tracker.name
    if experiment_tracker
    and isinstance(experiment_tracker, MLFlowExperimentTracker)
    else None
)


@step(experiment_tracker=EXPERIMENT_TRACKER_NAME)
def evaluate_model(
    model: ClassifierMixin,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Annotated[Dict[str, float], "metrics"]:
    """Evaluate model performance on test set.

    This step computes comprehensive classification metrics and logs them
    to both ZenML Model Control Plane and MLflow for tracking.

    Args:
        model: Trained model to evaluate
        X_test: Test features
        y_test: Test labels

    Returns:
        Dictionary of evaluation metrics
    """
    logger.info("Evaluating model performance")

    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
    }

    # Log metrics to console
    logger.info("Model Performance:")
    for metric_name, metric_value in metrics.items():
        logger.info(f"  {metric_name}: {metric_value:.4f}")

    # Log to MLflow
    if EXPERIMENT_TRACKER_NAME:
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)

    # Log to ZenML Model Control Plane
    log_metadata(
        metadata=metrics,
        infer_model=True,  # Automatically attach to pipeline's model
    )

    return metrics
