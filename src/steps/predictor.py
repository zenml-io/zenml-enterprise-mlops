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

"""Prediction step for batch inference."""

from typing import Annotated

import pandas as pd
from sklearn.base import ClassifierMixin
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def predict_batch(
    model: ClassifierMixin,
    X: pd.DataFrame,
) -> Annotated[pd.DataFrame, "predictions"]:
    """Generate predictions for a batch of patients.

    Args:
        model: Trained model
        X: Features to predict on

    Returns:
        DataFrame with predictions and probabilities
    """
    logger.info(f"Generating predictions for {len(X)} patients")

    # Get predictions and probabilities
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    # Create results dataframe
    results = pd.DataFrame(
        {
            "patient_id": X.index,
            "readmission_risk": predictions,
            "risk_probability": probabilities,
        }
    )

    logger.info(
        f"Predictions complete: {(predictions == 1).sum()} high-risk patients "
        f"identified ({(predictions == 1).sum() / len(predictions):.1%})"
    )

    return results
