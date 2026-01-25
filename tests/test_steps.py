"""Unit tests for step logic.

These tests verify the core data transformations and calculations
used in pipeline steps, without requiring ZenML execution.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler


class TestDataTransformations:
    """Test data transformation logic."""

    def test_scaler_preserves_shape(self, sample_features):
        """Scaling should preserve the shape of data."""
        scaler = StandardScaler()
        scaled = scaler.fit_transform(sample_features)

        assert scaled.shape == sample_features.shape

    def test_scaler_normalizes_values(self, sample_features):
        """Scaled data should have mean ~0 and std ~1."""
        scaler = StandardScaler()
        scaled = scaler.fit_transform(sample_features)

        # Check mean is approximately 0 for each column
        means = np.mean(scaled, axis=0)
        assert np.allclose(means, 0, atol=1e-10)

        # Check std is approximately 1 for each column
        stds = np.std(scaled, axis=0)
        assert np.allclose(stds, 1, atol=1e-10)

    def test_scaler_handles_single_value_columns(self):
        """Scaler should handle columns with constant values."""
        df = pd.DataFrame(
            {
                "constant": [5] * 100,
                "variable": np.random.randn(100),
            }
        )
        scaler = StandardScaler()
        scaled = scaler.fit_transform(df)

        # Constant column becomes 0 (no variance)
        assert np.allclose(scaled[:, 0], 0)


class TestModelTraining:
    """Test model training logic."""

    def test_model_can_fit(self, sample_features, sample_target):
        """Model should be able to fit on sample data."""
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(sample_features, sample_target)

        assert hasattr(model, "classes_")
        assert len(model.classes_) == 2  # Binary classification

    def test_model_predictions_are_binary(
        self, sample_features, sample_target, trained_model
    ):
        """Model predictions should be 0 or 1."""
        predictions = trained_model.predict(sample_features)

        assert set(predictions).issubset({0, 1})

    def test_model_probabilities_sum_to_one(
        self, sample_features, sample_target, trained_model
    ):
        """Prediction probabilities should sum to 1."""
        probabilities = trained_model.predict_proba(sample_features)

        row_sums = probabilities.sum(axis=1)
        assert np.allclose(row_sums, 1.0)

    def test_model_probabilities_in_range(
        self, sample_features, sample_target, trained_model
    ):
        """Prediction probabilities should be between 0 and 1."""
        probabilities = trained_model.predict_proba(sample_features)

        assert probabilities.min() >= 0
        assert probabilities.max() <= 1


class TestMetricsCalculation:
    """Test metrics calculation logic."""

    def test_metrics_are_calculated_correctly(self):
        """Verify metrics calculation matches expected values."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 1, 1, 0, 0, 1, 0])

        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)

        # Manual calculations
        # TP=3, TN=3, FP=1, FN=1
        assert accuracy == 6 / 8  # (TP + TN) / total
        assert precision == 3 / 4  # TP / (TP + FP)
        assert recall == 3 / 4  # TP / (TP + FN)
        assert np.isclose(f1, 2 * (0.75 * 0.75) / (0.75 + 0.75))

    def test_metrics_range(self, sample_features, sample_target, trained_model):
        """All metrics should be between 0 and 1."""
        predictions = trained_model.predict(sample_features)

        metrics = {
            "accuracy": accuracy_score(sample_target, predictions),
            "precision": precision_score(sample_target, predictions, zero_division=0),
            "recall": recall_score(sample_target, predictions, zero_division=0),
            "f1": f1_score(sample_target, predictions, zero_division=0),
        }

        for name, value in metrics.items():
            assert 0 <= value <= 1, f"{name} = {value} is out of range"

    def test_perfect_predictions_give_perfect_metrics(self):
        """Perfect predictions should yield metrics of 1.0."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])

        assert accuracy_score(y_true, y_pred) == 1.0
        assert precision_score(y_true, y_pred) == 1.0
        assert recall_score(y_true, y_pred) == 1.0
        assert f1_score(y_true, y_pred) == 1.0


class TestPredictionOutput:
    """Test prediction output formatting."""

    def test_prediction_dataframe_structure(self, sample_features, trained_model):
        """Prediction output should have expected columns."""
        predictions = trained_model.predict(sample_features)
        probabilities = trained_model.predict_proba(sample_features)[:, 1]

        results = pd.DataFrame(
            {
                "prediction": predictions,
                "probability": probabilities,
            }
        )

        assert "prediction" in results.columns
        assert "probability" in results.columns
        assert len(results) == len(sample_features)

    def test_high_probability_correlates_with_positive_prediction(
        self, sample_features, trained_model
    ):
        """High probabilities should generally correspond to positive predictions."""
        predictions = trained_model.predict(sample_features)
        probabilities = trained_model.predict_proba(sample_features)[:, 1]

        # Where probability > 0.5, prediction should be 1
        high_prob_mask = probabilities > 0.5
        assert np.all(predictions[high_prob_mask] == 1)

        # Where probability <= 0.5, prediction should be 0
        low_prob_mask = probabilities <= 0.5
        assert np.all(predictions[low_prob_mask] == 0)


class TestChampionChallengerLogic:
    """Test champion/challenger comparison logic."""

    def test_agreement_rate_calculation(self):
        """Agreement rate should be correctly calculated."""
        champion_preds = np.array([0, 1, 1, 0, 1])
        challenger_preds = np.array([0, 1, 0, 0, 1])

        agreement_rate = (champion_preds == challenger_preds).mean()
        assert agreement_rate == 0.8  # 4 out of 5 agree

    def test_probability_difference_calculation(self):
        """Probability differences should be correctly calculated."""
        champion_probs = np.array([0.2, 0.8, 0.6, 0.3, 0.9])
        challenger_probs = np.array([0.25, 0.75, 0.7, 0.35, 0.85])

        avg_diff = np.abs(champion_probs - challenger_probs).mean()
        max_diff = np.abs(champion_probs - challenger_probs).max()

        assert np.isclose(avg_diff, 0.06)
        assert np.isclose(max_diff, 0.1)

    def test_identical_models_have_perfect_agreement(self):
        """Identical predictions should have 100% agreement."""
        predictions = np.array([0, 1, 1, 0, 1])

        agreement_rate = (predictions == predictions).mean()
        prob_diff = np.abs(predictions - predictions).mean()

        assert agreement_rate == 1.0
        assert prob_diff == 0.0
