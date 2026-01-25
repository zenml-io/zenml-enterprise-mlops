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
from zenml import Model, get_step_context, pipeline, step
from zenml.enums import ModelStages
from zenml.logger import get_logger

from governance.hooks import pipeline_failure_hook, pipeline_success_hook
from src.steps import load_data

logger = get_logger(__name__)


@step(enable_cache=False)  # Always run fresh to use current production model
def scale_and_predict(
    X: pd.DataFrame,
) -> Annotated[pd.DataFrame, "predictions"]:
    """Load production model and generate predictions.

    Loads the model and scaler directly from Model Control Plane,
    then generates predictions with probabilities.

    Args:
        X: Raw features to predict on

    Returns:
        DataFrame with predictions and probabilities
    """
    context = get_step_context()

    # Load artifacts directly from Model Control Plane
    model = context.model.load_artifact("sklearn_classifier")
    scaler = context.model.load_artifact("scaler")

    logger.info(f"Loaded production model version: {context.model.number}")

    # Scale features
    X_scaled = pd.DataFrame(
        scaler.transform(X),
        columns=X.columns,
        index=X.index,
    )

    # Generate predictions
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)[:, 1]

    results = pd.DataFrame(
        {
            "prediction": predictions,
            "probability": probabilities,
        },
        index=X.index,
    )

    high_risk_count = (predictions == 1).sum()
    logger.info(
        f"Predictions complete: {high_risk_count} high-risk identified "
        f"({high_risk_count / len(predictions) * 100:.1f}%)"
    )

    return results


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
    1. Loads new data
    2. Loads the production model and scaler (by stage)
    3. Scales features and generates predictions

    The model is referenced by stage ("production") so this pipeline
    always uses the current production model without code changes.
    """
    # Load new data to predict on (using test set as demo data)
    _X_train, X_test, _, _ = load_data()

    # Scale and predict in a single step
    predictions = scale_and_predict(X_test)

    return predictions
