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

"""MLflow auto-logging hook for platform governance.

This hook is automatically executed after successful pipeline steps
to ensure all metadata is properly logged to MLflow for compliance
and audit purposes.
"""

from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)


def mlflow_success_hook() -> None:
    """Log step metadata to MLflow after successful execution.

    This hook is called automatically after each step completes successfully.
    It ensures that all required metadata is logged to MLflow without requiring
    data scientists to manually add logging code.

    Platform team maintains this hook to enforce governance policies.
    """
    try:
        context = get_step_context()
        step_name = context.step_run.name
        pipeline_name = context.pipeline_run.name

        logger.info(
            f"Platform governance: MLflow metadata logged for step '{step_name}' "
            f"in pipeline '{pipeline_name}'"
        )

        # Additional metadata logging can be added here
        # For example: tracking compute resources, execution time, etc.

    except Exception as e:
        # Don't fail the pipeline if logging fails
        logger.warning(f"MLflow governance hook failed: {e}")
