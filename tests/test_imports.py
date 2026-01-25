"""Smoke tests to verify all pipelines and steps can be imported.

These tests catch import errors, missing dependencies, and syntax issues
without requiring a ZenML server or full pipeline execution.
"""



class TestPipelineImports:
    """Test that all pipelines can be imported."""

    def test_import_training_pipeline(self):
        """Training pipeline should import without errors."""
        from src.pipelines.training import training_pipeline

        assert training_pipeline is not None
        assert callable(training_pipeline)

    def test_import_batch_inference_pipeline(self):
        """Batch inference pipeline should import without errors."""
        from src.pipelines.batch_inference import batch_inference_pipeline

        assert batch_inference_pipeline is not None
        assert callable(batch_inference_pipeline)

    def test_import_champion_challenger_pipeline(self):
        """Champion/challenger pipeline should import without errors."""
        from src.pipelines.champion_challenger import champion_challenger_pipeline

        assert champion_challenger_pipeline is not None
        assert callable(champion_challenger_pipeline)

    def test_import_inference_service(self):
        """Real-time inference service should import without errors."""
        from src.pipelines.realtime_inference import inference_service

        assert inference_service is not None
        assert callable(inference_service)

    def test_pipelines_module_exports(self):
        """All pipelines should be exported from the module."""
        from src.pipelines import (
            batch_inference_pipeline,
            champion_challenger_pipeline,
            inference_service,
            training_pipeline,
        )

        assert all(
            [
                training_pipeline,
                batch_inference_pipeline,
                champion_challenger_pipeline,
                inference_service,
            ]
        )


class TestStepImports:
    """Test that all steps can be imported."""

    def test_import_data_loader(self):
        """Data loader step should import."""
        from src.steps.data_loader import load_data

        assert load_data is not None

    def test_import_feature_engineering(self):
        """Feature engineering step should import."""
        from src.steps.feature_engineering import engineer_features

        assert engineer_features is not None

    def test_import_model_trainer(self):
        """Model trainer step should import."""
        from src.steps.model_trainer import train_model

        assert train_model is not None

    def test_import_model_evaluator(self):
        """Model evaluator step should import."""
        from src.steps.model_evaluator import evaluate_model

        assert evaluate_model is not None

    def test_import_predictor(self):
        """Predictor step should import."""
        from src.steps.predictor import predict_batch

        assert predict_batch is not None


class TestGovernanceImports:
    """Test that governance components can be imported."""

    def test_import_hooks(self):
        """Governance hooks should import."""
        from governance.hooks import (
            compliance_failure_hook,
            mlflow_success_hook,
            monitoring_success_hook,
        )

        assert mlflow_success_hook is not None
        assert monitoring_success_hook is not None
        assert compliance_failure_hook is not None

    def test_import_validation_steps(self):
        """Governance validation steps should import."""
        from governance.steps.data_validation import validate_data_quality
        from governance.steps.model_validation import validate_model_performance

        assert validate_data_quality is not None
        assert validate_model_performance is not None

    def test_import_docker_settings(self):
        """Governance docker settings should import."""
        from governance.docker import (
            BASE_DOCKER_SETTINGS,
            GPU_DOCKER_SETTINGS,
            LIGHTWEIGHT_DOCKER_SETTINGS,
            STANDARD_DOCKER_SETTINGS,
            get_docker_settings,
        )

        assert STANDARD_DOCKER_SETTINGS is not None
        assert GPU_DOCKER_SETTINGS is not None
        assert LIGHTWEIGHT_DOCKER_SETTINGS is not None
        assert BASE_DOCKER_SETTINGS is not None
        assert get_docker_settings is not None
