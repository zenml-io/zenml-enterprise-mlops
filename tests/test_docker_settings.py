"""Tests for platform-managed Docker settings.

These tests verify that DockerSettings configurations are valid and
the factory function works correctly.
"""

import pytest
from zenml.config import DockerSettings


class TestDockerSettingsImports:
    """Test that all docker settings can be imported."""

    def test_import_standard_settings(self):
        """Standard docker settings should import."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert STANDARD_DOCKER_SETTINGS is not None
        assert isinstance(STANDARD_DOCKER_SETTINGS, DockerSettings)

    def test_import_gpu_settings(self):
        """GPU docker settings should import."""
        from governance.docker import GPU_DOCKER_SETTINGS

        assert GPU_DOCKER_SETTINGS is not None
        assert isinstance(GPU_DOCKER_SETTINGS, DockerSettings)

    def test_import_lightweight_settings(self):
        """Lightweight docker settings should import."""
        from governance.docker import LIGHTWEIGHT_DOCKER_SETTINGS

        assert LIGHTWEIGHT_DOCKER_SETTINGS is not None
        assert isinstance(LIGHTWEIGHT_DOCKER_SETTINGS, DockerSettings)

    def test_import_base_settings(self):
        """Base docker settings should import."""
        from governance.docker import BASE_DOCKER_SETTINGS

        assert BASE_DOCKER_SETTINGS is not None
        assert isinstance(BASE_DOCKER_SETTINGS, DockerSettings)

    def test_import_factory_function(self):
        """Factory function should import."""
        from governance.docker import get_docker_settings

        assert get_docker_settings is not None
        assert callable(get_docker_settings)


class TestStandardDockerSettings:
    """Test standard docker settings configuration."""

    def test_parent_image(self):
        """Standard settings should use Python 3.11 slim image."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert STANDARD_DOCKER_SETTINGS.parent_image == "python:3.11-slim"

    def test_package_installer(self):
        """Standard settings should use uv installer."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert STANDARD_DOCKER_SETTINGS.python_package_installer.value == "uv"

    def test_required_integrations(self):
        """Standard settings should include mlflow and sklearn."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert "mlflow" in STANDARD_DOCKER_SETTINGS.required_integrations
        assert "sklearn" in STANDARD_DOCKER_SETTINGS.required_integrations

    def test_apt_packages(self):
        """Standard settings should include git and curl."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert "git" in STANDARD_DOCKER_SETTINGS.apt_packages
        assert "curl" in STANDARD_DOCKER_SETTINGS.apt_packages

    def test_environment_variables(self):
        """Standard settings should set Python environment variables."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        assert STANDARD_DOCKER_SETTINGS.environment.get("PYTHONUNBUFFERED") == "1"
        assert STANDARD_DOCKER_SETTINGS.environment.get("PIP_NO_CACHE_DIR") == "1"


class TestGPUDockerSettings:
    """Test GPU docker settings configuration."""

    def test_parent_image(self):
        """GPU settings should use PyTorch CUDA image."""
        from governance.docker import GPU_DOCKER_SETTINGS

        assert "pytorch" in GPU_DOCKER_SETTINGS.parent_image
        assert "cuda" in GPU_DOCKER_SETTINGS.parent_image

    def test_required_integrations(self):
        """GPU settings should include pytorch and mlflow."""
        from governance.docker import GPU_DOCKER_SETTINGS

        assert "pytorch" in GPU_DOCKER_SETTINGS.required_integrations
        assert "mlflow" in GPU_DOCKER_SETTINGS.required_integrations

    def test_cuda_environment(self):
        """GPU settings should set CUDA environment variables."""
        from governance.docker import GPU_DOCKER_SETTINGS

        assert "CUDA_VISIBLE_DEVICES" in GPU_DOCKER_SETTINGS.environment

    def test_opencv_dependencies(self):
        """GPU settings should include OpenCV system dependencies."""
        from governance.docker import GPU_DOCKER_SETTINGS

        assert "libsm6" in GPU_DOCKER_SETTINGS.apt_packages
        assert "libxext6" in GPU_DOCKER_SETTINGS.apt_packages


class TestLightweightDockerSettings:
    """Test lightweight docker settings configuration."""

    def test_parent_image(self):
        """Lightweight settings should use Python slim image."""
        from governance.docker import LIGHTWEIGHT_DOCKER_SETTINGS

        assert LIGHTWEIGHT_DOCKER_SETTINGS.parent_image == "python:3.11-slim"

    def test_no_heavy_integrations(self):
        """Lightweight settings should not include heavy integrations."""
        from governance.docker import LIGHTWEIGHT_DOCKER_SETTINGS

        # Should have minimal or no integrations
        assert len(LIGHTWEIGHT_DOCKER_SETTINGS.required_integrations) == 0


class TestGetDockerSettings:
    """Test the factory function for creating custom docker settings."""

    def test_standard_base(self):
        """Factory should return settings based on standard config."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(base="standard")
        assert settings.parent_image == "python:3.11-slim"
        assert "mlflow" in settings.required_integrations

    def test_gpu_base(self):
        """Factory should return settings based on GPU config."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(base="gpu")
        assert "pytorch" in settings.parent_image
        assert "pytorch" in settings.required_integrations

    def test_lightweight_base(self):
        """Factory should return settings based on lightweight config."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(base="lightweight")
        assert len(settings.required_integrations) == 0

    def test_extra_apt_packages(self):
        """Factory should add extra apt packages."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            extra_apt_packages=["ffmpeg", "libsndfile1"],
        )
        assert "ffmpeg" in settings.apt_packages
        assert "libsndfile1" in settings.apt_packages
        # Original packages should still be there
        assert "git" in settings.apt_packages

    def test_extra_integrations(self):
        """Factory should add extra integrations."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            extra_integrations=["huggingface", "wandb"],
        )
        assert "huggingface" in settings.required_integrations
        assert "wandb" in settings.required_integrations
        # Original integrations should still be there
        assert "mlflow" in settings.required_integrations

    def test_extra_requirements(self):
        """Factory should add extra requirements."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            extra_requirements=["transformers>=4.30.0", "datasets"],
        )
        assert "transformers>=4.30.0" in settings.requirements
        assert "datasets" in settings.requirements

    def test_extra_environment(self):
        """Factory should add extra environment variables."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            extra_environment={"MY_CUSTOM_VAR": "value"},
        )
        assert settings.environment.get("MY_CUSTOM_VAR") == "value"
        # Original env vars should still be there
        assert settings.environment.get("PYTHONUNBUFFERED") == "1"

    def test_override_parent_image(self):
        """Factory should allow overriding parent image."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            parent_image="custom/image:latest",
        )
        assert settings.parent_image == "custom/image:latest"

    def test_invalid_base_raises_error(self):
        """Factory should raise error for invalid base."""
        from governance.docker import get_docker_settings

        with pytest.raises(ValueError, match="Unknown base configuration"):
            get_docker_settings(base="invalid")

    def test_combined_customizations(self):
        """Factory should handle multiple customizations together."""
        from governance.docker import get_docker_settings

        settings = get_docker_settings(
            base="standard",
            extra_apt_packages=["ffmpeg"],
            extra_integrations=["huggingface"],
            extra_requirements=["transformers"],
            extra_environment={"HF_HOME": "/cache"},
        )

        assert "ffmpeg" in settings.apt_packages
        assert "huggingface" in settings.required_integrations
        assert "transformers" in settings.requirements
        assert settings.environment.get("HF_HOME") == "/cache"


class TestDockerSettingsWithPipeline:
    """Test that docker settings can be applied to pipelines/steps."""

    def test_settings_dict_format(self):
        """Docker settings should work in settings dict format."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        settings_dict = {"docker": STANDARD_DOCKER_SETTINGS}
        assert "docker" in settings_dict
        assert isinstance(settings_dict["docker"], DockerSettings)

    def test_settings_immutable(self):
        """Docker settings should be immutable (frozen)."""
        from governance.docker import STANDARD_DOCKER_SETTINGS

        # DockerSettings is frozen, so this should raise an error
        with pytest.raises(Exception):  # ValidationError or TypeError
            STANDARD_DOCKER_SETTINGS.parent_image = "new-image"
