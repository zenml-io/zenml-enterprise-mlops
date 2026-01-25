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

"""Data loading step for risk prediction model."""

from typing import Annotated

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def load_data(
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[
    Annotated[pd.DataFrame, "X_train"],
    Annotated[pd.DataFrame, "X_test"],
    Annotated[pd.Series, "y_train"],
    Annotated[pd.Series, "y_test"],
]:
    """Load and split the breast cancer dataset for binary classification.

    This step uses sklearn's breast cancer dataset for the demo.
    In production, this would load from your data warehouse.

    Args:
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.info("Loading breast cancer dataset as proxy for patient risk data")

    # Load dataset - this is a proper binary classification dataset
    data = load_breast_cancer(as_frame=True)
    X = data.data
    y = data.target
    y = pd.Series(y, name="risk_prediction")

    logger.info(f"Dataset loaded: {X.shape[0]} patients, {X.shape[1]} features")
    logger.info(f"Target distribution: {y.value_counts().to_dict()}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    logger.info(
        f"Data split: {len(X_train)} training samples, {len(X_test)} test samples"
    )

    return X_train, X_test, y_train, y_test
