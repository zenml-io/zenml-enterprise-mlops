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

from governance.hooks import (
    batch_inference_success_hook,
    pipeline_failure_hook,
)
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
    total_predictions = len(predictions)
    high_risk_pct = (
        (high_risk_count / total_predictions * 100) if total_predictions > 0 else 0.0
    )
    logger.info(
        f"Predictions complete: {high_risk_count} high-risk identified "
        f"({high_risk_pct:.1f}%)"
    )

    return results


@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        version=ModelStages.PRODUCTION,  # Always use production model
    ),
    on_failure=pipeline_failure_hook,
    enable_cache=False,
)
def batch_inference_pipeline(
    enable_drift_detection: bool = False,
    simulate_drift: bool = False,
):
    """Run batch inference using the production model.

    This pipeline:
    1. Loads new data (and reference data when drift detection enabled)
    2. Optionally simulates drift (staging: set simulate_drift in config)
    3. Optionally runs drift detection and Slack alert (staging/production)
    4. Loads the production model and scaler (by stage)
    5. Scales features and generates predictions

    The model is referenced by stage ("production") so this pipeline
    always uses the current production model without code changes.

    Args:
        enable_drift_detection: When True, compares inference input against
            training baseline to detect data drift. Use in staging/production.
        simulate_drift: When True (and drift detection enabled), artificially
            shifts data to trigger drift. Use in staging to test alerting.
    """
    # Load data (X_train = reference for drift; X_test = inference input)
    X_train, X_test, _, _ = load_data()

    # Step success hooks: attach in staging/production only (when drift enabled)
    predict_step = (
        scale_and_predict.with_options(on_success=batch_inference_success_hook)
        if enable_drift_detection
        else scale_and_predict
    )

    # Platform governance: drift detection (staging/production only)
    if enable_drift_detection:
        from governance.steps import (
            drift_alert_slack,
            drift_report_step,
            introduce_simulated_drift,
        )

        # Simulate drift when testing (e.g. simulate_drift: true in staging yaml)
        X_test_for_drift = introduce_simulated_drift(
            data=X_test, simulate_drift=simulate_drift
        )
        report_json, _ = drift_report_step(
            reference_dataset=X_train,
            comparison_dataset=X_test_for_drift,
        )
        drift_alert_slack(
            report_json=report_json,
            reference_data=X_train,
            current_data=X_test_for_drift,
            simulate_drift=simulate_drift,
        )
        predictions = predict_step(X_test_for_drift)
    else:
        predictions = predict_step(X_test)

    return predictions
