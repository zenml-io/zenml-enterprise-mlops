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

"""Platform-managed Docker settings for ML pipelines.

This module provides pre-configured DockerSettings that enforce
organizational standards for containerized pipeline execution.

Usage:
    from governance.docker import STANDARD_DOCKER_SETTINGS, GPU_DOCKER_SETTINGS

    @pipeline(settings={"docker": STANDARD_DOCKER_SETTINGS})
    def my_pipeline():
        ...
"""

from governance.docker.docker_settings import (
    BASE_DOCKER_SETTINGS,
    GPU_DOCKER_SETTINGS,
    LIGHTWEIGHT_DOCKER_SETTINGS,
    STANDARD_DOCKER_SETTINGS,
    get_docker_settings,
)

__all__ = [
    "BASE_DOCKER_SETTINGS",
    "GPU_DOCKER_SETTINGS",
    "LIGHTWEIGHT_DOCKER_SETTINGS",
    "STANDARD_DOCKER_SETTINGS",
    "get_docker_settings",
]
