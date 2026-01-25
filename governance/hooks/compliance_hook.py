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

"""Compliance hook for platform governance.

This hook is executed when pipelines fail to ensure proper
incident tracking and audit logging for compliance purposes.
"""

from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)


def compliance_failure_hook(exception: Exception) -> None:
    """Log compliance information when a step fails.

    This hook ensures that failures are properly documented for
    audit trails and regulatory compliance (e.g., HIPAA, GDPR).

    Args:
        exception: The exception that caused the failure

    Platform team maintains this hook to meet compliance requirements.
    """
    try:
        context = get_step_context()
        step_name = context.step_run.name
        pipeline_name = context.pipeline_run.name

        # Log failure for audit trail
        logger.error(
            f"Compliance audit: Pipeline '{pipeline_name}' step '{step_name}' "
            f"failed with error: {exception!s}"
        )

        # In production, this would:
        # 1. Log to compliance database
        # 2. Send alerts to platform team
        # 3. Create incident ticket
        # 4. Record in audit trail for regulatory review

    except Exception as e:
        logger.error(f"Compliance hook failed: {e}")
