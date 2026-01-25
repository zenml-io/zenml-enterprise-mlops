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

"""Data loading step for patient readmission prediction."""

from typing import Annotated

import pandas as pd
from sklearn.datasets import load_diabetes
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
    """Load and split the diabetes dataset for readmission prediction.

    This step uses the diabetes dataset as a proxy for patient readmission
    risk prediction. In production, this would load from your data warehouse.

    Args:
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.info("Loading diabetes dataset as proxy for patient data")

    # Load dataset
    data = load_diabetes(as_frame=True)
    X = data.data  # Use .data to get only features (excludes target)

    # Convert regression target to binary classification (high/low risk)
    # Threshold at median for balanced classes
    y = (data.target > data.target.median()).astype(int)
    y = pd.Series(y, name="readmission_risk")

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
