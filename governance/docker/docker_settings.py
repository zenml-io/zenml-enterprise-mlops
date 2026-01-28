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

"""Platform-managed Docker settings for enterprise ML pipelines.

This module provides pre-configured DockerSettings maintained by the platform
team. Data scientists use these settings without modification - the platform
team controls dependencies, security patches, and compliance requirements.

Design Principles:
- Platform team owns Docker configuration
- Data scientists import pre-built settings
- Consistent environments across teams
- Security and compliance baked in

Example:
    from governance.docker import STANDARD_DOCKER_SETTINGS

    @pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
    def training_pipeline():
        ...

    # Or per-step for specialized needs
    @step(settings={"docker": GPU_DOCKER_SETTINGS})
    def train_with_gpu():
        ...
"""

from zenml.config import DockerSettings

# =============================================================================
# Base Configuration
# =============================================================================

# Environment variables for consistent Python behavior
_BASE_ENVIRONMENT = {
    "PYTHONUNBUFFERED": "1",  # Disable output buffering for logging
    "PYTHONDONTWRITEBYTECODE": "1",  # Don't create .pyc files
    "PIP_NO_CACHE_DIR": "1",  # Don't cache pip packages (smaller images)
    "PIP_DISABLE_PIP_VERSION_CHECK": "1",  # Skip pip update check
}


# =============================================================================
# Pre-configured Docker Settings
# =============================================================================

# Minimal base settings - use as foundation for custom configurations
# No parent_image = use default ZenML image (has ZenML pre-installed)
BASE_DOCKER_SETTINGS = DockerSettings(
    python_package_installer="uv",
    environment=_BASE_ENVIRONMENT,
    install_stack_requirements=True,
)


# Standard settings for most ML training pipelines
# No parent_image = use default ZenML image (has ZenML pre-installed)
STANDARD_DOCKER_SETTINGS = DockerSettings(
    python_package_installer="uv",
    environment=_BASE_ENVIRONMENT,
    required_integrations=["sklearn"],
    install_stack_requirements=True,
)


# GPU-enabled settings for deep learning workloads
# Includes: PyTorch with CUDA 11.8, cuDNN, OpenCV dependencies
GPU_DOCKER_SETTINGS = DockerSettings(
    parent_image="pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime",
    python_package_installer="uv",
    python_package_installer_args={
        "system": None
    },  # None = flag without value (--system)
    apt_packages=[
        "libsm6",  # OpenCV dependencies
        "libxext6",
        "libgl1-mesa-glx",
    ],
    environment={
        **_BASE_ENVIRONMENT,
        "CUDA_VISIBLE_DEVICES": "0",  # Default to first GPU
        "TORCH_CUDA_ARCH_LIST": "7.0 7.5 8.0 8.6",  # Common GPU architectures
    },
    required_integrations=["pytorch"],
    install_stack_requirements=True,
)


# Minimal settings for quick iteration and testing
# Use for: data preprocessing, feature engineering, lightweight inference
# No parent_image = use default ZenML image (has ZenML pre-installed)
LIGHTWEIGHT_DOCKER_SETTINGS = DockerSettings(
    python_package_installer="uv",
    environment=_BASE_ENVIRONMENT,
    # No required_integrations - install only what's needed
    install_stack_requirements=True,
)


# =============================================================================
# Factory Function for Custom Settings
# =============================================================================


def get_docker_settings(
    base: str = "standard",
    extra_apt_packages: list[str] | None = None,
    extra_integrations: list[str] | None = None,
    extra_requirements: list[str] | None = None,
    extra_environment: dict | None = None,
    parent_image: str | None = None,
) -> DockerSettings:
    """Create customized Docker settings based on a platform-approved base.

    This function allows data scientists to extend platform settings
    without modifying the base configurations.

    Args:
        base: Base configuration to extend ("standard", "gpu", "lightweight")
        extra_apt_packages: Additional system packages to install
        extra_integrations: Additional ZenML integrations to include
        extra_requirements: Additional Python packages to install
        extra_environment: Additional environment variables
        parent_image: Override the parent image (use with caution)

    Returns:
        Customized DockerSettings

    Example:
        # Add HuggingFace support to standard settings
        settings = get_docker_settings(
            base="standard",
            extra_integrations=["huggingface"],
            extra_requirements=["transformers>=4.30.0"],
        )

        @pipeline(settings={"docker": settings})
        def nlp_pipeline():
            ...
    """
    # Select base configuration
    base_configs = {
        "standard": STANDARD_DOCKER_SETTINGS,
        "gpu": GPU_DOCKER_SETTINGS,
        "lightweight": LIGHTWEIGHT_DOCKER_SETTINGS,
        "base": BASE_DOCKER_SETTINGS,
    }

    if base not in base_configs:
        raise ValueError(
            f"Unknown base configuration: {base}. "
            f"Choose from: {list(base_configs.keys())}"
        )

    base_settings = base_configs[base]

    # Build merged configurations
    apt_packages = list(base_settings.apt_packages or [])
    if extra_apt_packages:
        apt_packages.extend(extra_apt_packages)

    integrations = list(base_settings.required_integrations or [])
    if extra_integrations:
        integrations.extend(extra_integrations)

    requirements = base_settings.requirements
    if extra_requirements:
        if isinstance(requirements, list):
            requirements = requirements + extra_requirements
        elif requirements is None:
            requirements = extra_requirements
        else:
            # requirements is a file path, can't easily merge
            # Create a new list with file + extra packages
            requirements = extra_requirements

    environment = dict(base_settings.environment)
    if extra_environment:
        environment.update(extra_environment)

    # Build kwargs for DockerSettings
    kwargs = {
        "python_package_installer": "uv",
        "environment": environment,
        "install_stack_requirements": base_settings.install_stack_requirements,
    }

    # Only set parent_image if explicitly provided or base has one
    if parent_image:
        kwargs["parent_image"] = parent_image
        # Custom images without venv need --system flag
        kwargs["python_package_installer_args"] = {"system": None}
    elif base_settings.parent_image:
        kwargs["parent_image"] = base_settings.parent_image
        kwargs["python_package_installer_args"] = {"system": None}

    # Only include apt_packages if there are any
    if apt_packages:
        kwargs["apt_packages"] = apt_packages

    # Only include required_integrations if there are any
    if integrations:
        kwargs["required_integrations"] = integrations

    # Only include requirements if there are any
    if requirements:
        kwargs["requirements"] = requirements

    return DockerSettings(**kwargs)
