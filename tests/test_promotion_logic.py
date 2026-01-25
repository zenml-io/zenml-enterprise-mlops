"""Tests for model promotion validation logic.

These tests verify the promotion thresholds and validation rules
without requiring a ZenML server connection.
"""



# Extract promotion thresholds for testing (mirrors promote_model.py)
PROMOTION_REQUIREMENTS = {
    "staging": {
        "accuracy": 0.7,
        "precision": 0.7,
        "recall": 0.7,
    },
    "production": {
        "accuracy": 0.8,
        "precision": 0.8,
        "recall": 0.8,
    },
}

REQUIRED_METRICS = ["accuracy", "precision", "recall"]


def check_metrics_meet_requirements(
    metrics: dict, stage: str
) -> tuple[bool, list[str]]:
    """Check if metrics meet the requirements for a given stage.

    Args:
        metrics: Dictionary of metric name -> value
        stage: Target stage ("staging" or "production")

    Returns:
        Tuple of (passes, list of failure messages)
    """
    requirements = PROMOTION_REQUIREMENTS.get(stage, {})
    failures = []

    for metric, min_value in requirements.items():
        actual = metrics.get(metric, 0)
        if actual < min_value:
            failures.append(f"{metric}: {actual:.3f} < {min_value:.3f}")

    return len(failures) == 0, failures


def check_required_metrics_present(metrics: dict) -> list[str]:
    """Check if all required metrics are present.

    Returns:
        List of missing metric names
    """
    return [m for m in REQUIRED_METRICS if m not in metrics]


class TestPromotionThresholds:
    """Test promotion threshold definitions."""

    def test_staging_thresholds_are_lower_than_production(self):
        """Staging thresholds should be less strict than production."""
        for metric in REQUIRED_METRICS:
            staging_req = PROMOTION_REQUIREMENTS["staging"][metric]
            prod_req = PROMOTION_REQUIREMENTS["production"][metric]
            assert staging_req <= prod_req, (
                f"{metric}: staging ({staging_req}) should be <= production ({prod_req})"
            )

    def test_all_thresholds_are_reasonable(self):
        """All thresholds should be between 0 and 1."""
        for stage, requirements in PROMOTION_REQUIREMENTS.items():
            for metric, value in requirements.items():
                assert 0 <= value <= 1, f"{stage}.{metric} = {value} is out of range"

    def test_production_requires_80_percent_minimum(self):
        """Production should require at least 80% on all metrics."""
        for metric, value in PROMOTION_REQUIREMENTS["production"].items():
            assert value >= 0.8, f"Production {metric} threshold too low: {value}"


class TestMetricsValidation:
    """Test metrics validation logic."""

    def test_good_metrics_pass_staging(self, sample_metrics):
        """Good metrics should pass staging validation."""
        passes, failures = check_metrics_meet_requirements(sample_metrics, "staging")
        assert passes, f"Should pass staging but got failures: {failures}"

    def test_good_metrics_pass_production(self, sample_metrics):
        """Good metrics should pass production validation."""
        passes, failures = check_metrics_meet_requirements(sample_metrics, "production")
        assert passes, f"Should pass production but got failures: {failures}"

    def test_poor_metrics_fail_staging(self, poor_metrics):
        """Poor metrics should fail staging validation."""
        passes, failures = check_metrics_meet_requirements(poor_metrics, "staging")
        assert not passes, "Should fail staging validation"
        assert len(failures) > 0

    def test_poor_metrics_fail_production(self, poor_metrics):
        """Poor metrics should fail production validation."""
        passes, failures = check_metrics_meet_requirements(poor_metrics, "production")
        assert not passes, "Should fail production validation"
        assert len(failures) > 0

    def test_borderline_staging_metrics(self):
        """Metrics exactly at threshold should pass."""
        borderline = {"accuracy": 0.7, "precision": 0.7, "recall": 0.7}
        passes, failures = check_metrics_meet_requirements(borderline, "staging")
        assert passes, f"Borderline metrics should pass: {failures}"

    def test_just_below_threshold_fails(self):
        """Metrics just below threshold should fail."""
        just_below = {"accuracy": 0.699, "precision": 0.7, "recall": 0.7}
        passes, failures = check_metrics_meet_requirements(just_below, "staging")
        assert not passes, "Just below threshold should fail"
        assert "accuracy" in failures[0]

    def test_missing_metrics_detected(self):
        """Missing required metrics should be detected."""
        incomplete = {"accuracy": 0.9}  # Missing precision and recall
        missing = check_required_metrics_present(incomplete)
        assert "precision" in missing
        assert "recall" in missing
        assert "accuracy" not in missing

    def test_complete_metrics_pass_check(self, sample_metrics):
        """Complete metrics should have no missing values."""
        missing = check_required_metrics_present(sample_metrics)
        assert len(missing) == 0


class TestPromotionPaths:
    """Test valid promotion paths."""

    def test_staging_metrics_may_not_meet_production(self):
        """Metrics that pass staging may not pass production."""
        staging_only = {"accuracy": 0.75, "precision": 0.72, "recall": 0.78}

        staging_passes, _ = check_metrics_meet_requirements(staging_only, "staging")
        prod_passes, _ = check_metrics_meet_requirements(staging_only, "production")

        assert staging_passes, "Should pass staging"
        assert not prod_passes, "Should fail production"

    def test_production_metrics_always_pass_staging(self):
        """Metrics that pass production should always pass staging."""
        production_ready = {"accuracy": 0.85, "precision": 0.82, "recall": 0.88}

        staging_passes, _ = check_metrics_meet_requirements(production_ready, "staging")
        prod_passes, _ = check_metrics_meet_requirements(production_ready, "production")

        assert staging_passes, "Should pass staging"
        assert prod_passes, "Should pass production"
