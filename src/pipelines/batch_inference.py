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

"""Batch inference pipeline using production model.

This pipeline demonstrates how to:
- Load the current production model by stage
- Run batch predictions
- Track predictions for monitoring
"""

from typing import Annotated

import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.preprocessing import StandardScaler
from zenml import Model, pipeline, step
from zenml.enums import ModelStages
from zenml.logger import get_logger

from governance.hooks import pipeline_failure_hook, pipeline_success_hook
from src.steps import load_data, predict_batch

logger = get_logger(__name__)


@step
def load_production_artifacts() -> tuple[
    Annotated[ClassifierMixin, "model"],
    Annotated[StandardScaler, "scaler"],
]:
    """Load model and scaler from the Model Control Plane.

    Returns:
        Tuple of (model, scaler) from the production model version
    """
    from zenml import get_step_context

    context = get_step_context()
    model = context.model.load_artifact("model")
    scaler = context.model.load_artifact("scaler")

    logger.info(f"Loaded production model version: {context.model.number}")

    return model, scaler


@step
def apply_scaler(
    X: pd.DataFrame,
    scaler: StandardScaler,
) -> Annotated[pd.DataFrame, "X_scaled"]:
    """Apply saved scaler to features.

    Args:
        X: Raw features
        scaler: Fitted StandardScaler from training

    Returns:
        Scaled features
    """
    X_scaled = pd.DataFrame(
        scaler.transform(X),
        columns=X.columns,
        index=X.index,
    )
    logger.info(f"Applied scaler to {len(X)} samples")
    return X_scaled


@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        version=ModelStages.PRODUCTION,  # Always use production model
    ),
    on_success=pipeline_success_hook,
    on_failure=pipeline_failure_hook,
)
def batch_inference_pipeline():
    """Run batch inference using the production model.

    This pipeline:
    1. Loads new patient data
    2. Loads the current production model and scaler (by stage)
    3. Engineers features using the saved scaler
    4. Generates predictions
    5. Logs predictions for monitoring

    The model is referenced by stage ("production") so this pipeline
    always uses the current production model without code changes.
    """
    # Load new data to predict on
    _X_train, X_test, _, _ = load_data()

    # Use test set as new data for demo purposes
    # In production, this would load from your data warehouse
    logger.info("Loading new data for predictions")

    # Load production model and scaler from Model Control Plane
    model, scaler = load_production_artifacts()

    # Apply scaler transformation
    X_scaled = apply_scaler(X_test, scaler)

    # Generate predictions
    predictions = predict_batch(model, X_scaled)

    # In production, predictions would be:
    # 1. Saved to database
    # 2. Sent to monitoring system (Arize)
    # 3. Delivered to downstream applications

    return predictions
