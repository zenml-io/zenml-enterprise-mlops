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

"""Training pipeline for binary classification model.

This pipeline demonstrates:
- Clean developer experience (no wrapper code)
- Platform governance enforcement via hooks
- Model Control Plane integration
- MLflow experiment tracking
- Dynamic preprocessing (optional SMOTE, PCA)

Uses breast cancer dataset for demo; replace with your data in production.
"""

from typing import Annotated, Optional

import pandas as pd
from sklearn.decomposition import PCA
from zenml import Model, pipeline, step
from zenml.logger import get_logger

# Import platform governance
from governance.hooks import (
    pipeline_failure_hook,
    pipeline_success_hook,
)
from governance.steps import validate_data_quality, validate_model_performance

# Import ML steps
from src.steps import (
    engineer_features,
    evaluate_model,
    load_data,
    train_model,
)

logger = get_logger(__name__)


@step
def check_and_apply_smote(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    enable_resampling: bool = False,
    imbalance_threshold: float = 0.3,
    random_state: int = 42,
) -> tuple[
    Annotated[pd.DataFrame, "X_train"],
    Annotated[pd.Series, "y_train"],
]:
    """Check for class imbalance and apply SMOTE if needed.

    This step combines the check and apply logic to avoid conditional
    branching at the pipeline level, which doesn't work in ZenML.

    Args:
        X_train: Training features
        y_train: Training labels
        enable_resampling: Whether to enable SMOTE resampling
        imbalance_threshold: Minimum ratio of minority class (0.3 = 30%)
        random_state: Random seed for reproducibility

    Returns:
        Training features and labels (resampled if needed)
    """
    if not enable_resampling:
        logger.info("SMOTE resampling disabled")
        return X_train, y_train

    # Check class distribution
    class_counts = y_train.value_counts()
    minority_ratio = class_counts.min() / class_counts.sum()

    logger.info(
        f"Class distribution: {class_counts.to_dict()}. "
        f"Minority class ratio: {minority_ratio:.2%}"
    )

    if minority_ratio >= imbalance_threshold:
        logger.info("No resampling needed - class distribution acceptable")
        return X_train, y_train

    # Apply SMOTE
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        logger.warning(
            "imbalanced-learn not installed. Skipping SMOTE resampling. "
            "Install with: pip install imbalanced-learn"
        )
        return X_train, y_train

    smote = SMOTE(random_state=random_state)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    logger.info(
        f"SMOTE resampling applied: {len(X_train)} → {len(X_resampled)} samples"
    )
    return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled)


@step
def check_and_apply_pca(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    enable_pca: bool = False,
    max_features: int = 50,
    n_components: int = 30,
    random_state: int = 42,
) -> tuple[
    Annotated[pd.DataFrame, "X_train"],
    Annotated[pd.DataFrame, "X_test"],
    Annotated[Optional[PCA], "pca_transformer"],
]:
    """Check feature count and apply PCA if needed.

    This step combines the check and apply logic to avoid conditional
    branching at the pipeline level, which doesn't work in ZenML.

    Args:
        X_train: Training features
        X_test: Test features
        enable_pca: Whether to enable PCA
        max_features: Maximum features before triggering reduction
        n_components: Number of principal components to keep
        random_state: Random seed for reproducibility

    Returns:
        Training and test features (PCA-transformed if needed) and PCA transformer (or None)
    """
    if not enable_pca:
        logger.info("PCA disabled")
        return X_train, X_test, None

    # Check feature count
    feature_count = X_train.shape[1]
    logger.info(f"Feature count: {feature_count}")

    if feature_count <= max_features:
        logger.info(f"No PCA needed - feature count within limit ({max_features})")
        return X_train, X_test, None

    # Apply PCA
    pca = PCA(n_components=min(n_components, feature_count), random_state=random_state)
    X_train_pca = pca.fit_transform(X_train)
    X_test_pca = pca.transform(X_test)

    explained_variance = pca.explained_variance_ratio_.sum()
    logger.info(
        f"PCA applied: {feature_count} → {pca.n_components_} features. "
        f"Explained variance: {explained_variance:.2%}"
    )

    return (
        pd.DataFrame(
            X_train_pca, columns=[f"PC{i + 1}" for i in range(pca.n_components_)]
        ),
        pd.DataFrame(
            X_test_pca, columns=[f"PC{i + 1}" for i in range(pca.n_components_)]
        ),
        pca,
    )


@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        description="Binary classification model for risk prediction",
        tags=["classification", "sklearn", "production"],
    ),
    on_success=pipeline_success_hook,
    on_failure=pipeline_failure_hook,
)
def training_pipeline(
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: int = 10,
    min_accuracy: float = 0.7,
    enable_resampling: bool = False,
    imbalance_threshold: float = 0.3,
    enable_pca: bool = False,
    max_features_for_pca: int = 50,
    pca_components: int = 30,
):
    """Train and validate a binary classification model.

    This pipeline demonstrates:
    1. Clean Python code (no framework wrappers)
    2. Platform governance (automatic via hooks)
    3. Dynamic preprocessing (conditional SMOTE, PCA)
    4. Complete lineage and metadata tracking

    Platform governance is automatically enforced:
    - Data quality validation (platform step)
    - Model performance validation (platform step)
    - MLflow auto-logging (platform hook)
    - Compliance audit trail (platform hook)

    Dynamic features adapt at runtime:
    - SMOTE resampling if class imbalance detected
    - PCA if feature count is high

    Args:
        test_size: Fraction of data for testing
        n_estimators: Number of trees in Random Forest
        max_depth: Maximum depth of trees
        min_accuracy: Minimum accuracy required for validation
        enable_resampling: Enable dynamic SMOTE resampling for class imbalance
        imbalance_threshold: Minimum minority class ratio before triggering SMOTE (0.3 = 30%)
        enable_pca: Enable dynamic PCA for high-dimensional data
        max_features_for_pca: Max features before triggering PCA (default 50)
        pca_components: Number of principal components to keep (default 30)
    """
    # Load data
    X_train, X_test, y_train, y_test = load_data(test_size=test_size)

    # Platform governance: Validate data quality
    X_train = validate_data_quality(X_train, min_rows=100)

    # Dynamic: Check for class imbalance and apply SMOTE if needed
    # Logic is handled inside the step to avoid pipeline-level conditional branching
    X_train, y_train = check_and_apply_smote(
        X_train,
        y_train,
        enable_resampling=enable_resampling,
        imbalance_threshold=imbalance_threshold,
    )

    # Engineer features (scaling, transformations)
    X_train_scaled, X_test_scaled, _scaler = engineer_features(X_train, X_test)

    # Dynamic: Check feature count and apply PCA if needed
    # Logic is handled inside the step to avoid pipeline-level conditional branching
    X_train_final, X_test_final, _pca_transformer = check_and_apply_pca(
        X_train_scaled,
        X_test_scaled,
        enable_pca=enable_pca,
        max_features=max_features_for_pca,
        n_components=pca_components,
    )

    # Train model (MLflow autologging enabled automatically via hook)
    model = train_model(
        X_train_final,
        y_train,
        n_estimators=n_estimators,
        max_depth=max_depth,
    )

    # Evaluate model
    metrics = evaluate_model(model, X_test_final, y_test)

    # Platform governance: Validate model performance
    validate_model_performance(
        metrics,
        min_accuracy=min_accuracy,
        min_precision=0.7,
        min_recall=0.7,
    )

    return model, metrics


if __name__ == "__main__":
    # Run the training pipeline
    training_pipeline()
