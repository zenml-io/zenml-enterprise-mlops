"""Shared test fixtures for the ZenML Enterprise MLOps template."""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


@pytest.fixture
def sample_features() -> pd.DataFrame:
    """Generate sample feature data for testing."""
    np.random.seed(42)
    n_samples = 100

    return pd.DataFrame(
        {
            "age": np.random.randint(18, 90, n_samples),
            "num_procedures": np.random.randint(0, 10, n_samples),
            "num_medications": np.random.randint(0, 20, n_samples),
            "num_outpatient": np.random.randint(0, 5, n_samples),
            "num_inpatient": np.random.randint(0, 5, n_samples),
            "num_emergency": np.random.randint(0, 3, n_samples),
            "num_diagnoses": np.random.randint(1, 10, n_samples),
            "time_in_hospital": np.random.randint(1, 14, n_samples),
        }
    )


@pytest.fixture
def sample_target() -> pd.Series:
    """Generate sample target variable for testing."""
    np.random.seed(42)
    return pd.Series(np.random.randint(0, 2, 100), name="readmitted")


@pytest.fixture
def trained_model(sample_features: pd.DataFrame, sample_target: pd.Series):
    """Create a trained model for testing."""
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(sample_features, sample_target)
    return model


@pytest.fixture
def fitted_scaler(sample_features: pd.DataFrame):
    """Create a fitted scaler for testing."""
    scaler = StandardScaler()
    scaler.fit(sample_features)
    return scaler


@pytest.fixture
def sample_metrics() -> dict:
    """Sample model metrics for testing promotion logic."""
    return {
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85,
        "roc_auc": 0.90,
    }


@pytest.fixture
def poor_metrics() -> dict:
    """Poor model metrics that should fail validation."""
    return {
        "accuracy": 0.55,
        "precision": 0.50,
        "recall": 0.60,
        "f1_score": 0.54,
        "roc_auc": 0.58,
    }
