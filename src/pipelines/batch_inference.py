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

from zenml import Model, pipeline
from zenml.enums import ModelStages
from zenml.logger import get_logger

from platform.hooks import mlflow_success_hook, compliance_failure_hook
from src.steps import load_data, engineer_features, predict_batch

logger = get_logger(__name__)


@pipeline(
    model=Model(
        name="patient_readmission_predictor",
        version=ModelStages.PRODUCTION,  # Always use production model
    ),
    on_success=mlflow_success_hook,
    on_failure=compliance_failure_hook,
)
def batch_inference_pipeline():
    """Run batch inference using the production model.

    This pipeline:
    1. Loads new patient data
    2. Loads the current production model (by stage)
    3. Engineers features using the saved scaler
    4. Generates predictions
    5. Logs predictions for monitoring

    The model is referenced by stage ("production") so this pipeline
    always uses the current production model without code changes.
    """
    # Load new data to predict on
    X_train, X_test, _, _ = load_data()

    # Use test set as new data for demo purposes
    # In production, this would load from your data warehouse
    logger.info("Loading new patient data for predictions")

    # Load production model and scaler from Model Control Plane
    # The model is automatically available via the pipeline context
    from zenml import get_pipeline_context

    context = get_pipeline_context()
    model = context.model.load_artifact("model")
    scaler = context.model.load_artifact("scaler")

    logger.info(f"Loaded production model: {context.model.version}")

    # Engineer features using saved scaler
    import pandas as pd

    X_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index,
    )

    # Generate predictions
    predictions = predict_batch(model, X_scaled)

    # In production, predictions would be:
    # 1. Saved to database
    # 2. Sent to monitoring system (Arize)
    # 3. Delivered to downstream applications

    return predictions
