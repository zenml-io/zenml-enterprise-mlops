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

"""Training pipeline for patient readmission prediction model.

This pipeline demonstrates:
- Clean developer experience (no wrapper code)
- Platform governance enforcement via hooks
- Model Control Plane integration
- MLflow experiment tracking
"""

from zenml import Model, pipeline
from zenml.logger import get_logger

# Import platform governance
from platform.hooks import (
    mlflow_success_hook,
    compliance_failure_hook,
)
from platform.steps import validate_data_quality, validate_model_performance

# Import ML steps
from src.steps import (
    load_data,
    engineer_features,
    train_model,
    evaluate_model,
)

logger = get_logger(__name__)


@pipeline(
    model=Model(
        name="patient_readmission_predictor",
        description="Predicts 30-day hospital readmission risk for patients",
        tags=["healthcare", "classification", "production"],
    ),
    on_success=mlflow_success_hook,
    on_failure=compliance_failure_hook,
)
def training_pipeline(
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: int = 10,
    min_accuracy: float = 0.7,
):
    """Train and validate a patient readmission risk prediction model.

    This pipeline:
    1. Loads and validates patient data
    2. Engineers features
    3. Trains a Random Forest classifier
    4. Evaluates performance
    5. Validates against platform requirements

    Platform governance is automatically enforced via:
    - Data quality validation (platform step)
    - Model performance validation (platform step)
    - MLflow auto-logging (platform hook)
    - Compliance audit trail (platform hook)

    Data scientists only need to focus on the ML logic!

    Args:
        test_size: Fraction of data for testing
        n_estimators: Number of trees in Random Forest
        max_depth: Maximum depth of trees
        min_accuracy: Minimum accuracy required for validation
    """
    # Load data
    X_train, X_test, y_train, y_test = load_data(test_size=test_size)

    # Platform governance: Validate data quality
    X_train = validate_data_quality(X_train, min_rows=100)

    # Engineer features
    X_train_scaled, X_test_scaled, scaler = engineer_features(
        X_train, X_test
    )

    # Train model (MLflow autologging enabled automatically)
    model = train_model(
        X_train_scaled,
        y_train,
        n_estimators=n_estimators,
        max_depth=max_depth,
    )

    # Evaluate model
    metrics = evaluate_model(model, X_test_scaled, y_test)

    # Platform governance: Validate model performance
    validate_model_performance(
        metrics,
        min_accuracy=min_accuracy,
        min_precision=0.7,
        min_recall=0.7,
    )

    return model, metrics
