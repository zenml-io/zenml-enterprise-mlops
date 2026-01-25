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

"""Feature engineering step for patient data."""

from typing import Annotated

import pandas as pd
from sklearn.preprocessing import StandardScaler
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def engineer_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[
    Annotated[pd.DataFrame, "X_train_scaled"],
    Annotated[pd.DataFrame, "X_test_scaled"],
    Annotated[StandardScaler, "scaler"],
]:
    """Engineer and scale features for model training.

    This step applies feature scaling to ensure all features are on
    similar scales. The scaler is fit on training data only to prevent
    data leakage.

    Args:
        X_train: Training features
        X_test: Test features

    Returns:
        Tuple of (X_train_scaled, X_test_scaled, scaler)
    """
    logger.info("Engineering features")

    # Fit scaler on training data only
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index,
    )

    # Transform test data using fitted scaler
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index,
    )

    logger.info(f"Features scaled: {X_train_scaled.shape[1]} features")

    return X_train_scaled, X_test_scaled, scaler
