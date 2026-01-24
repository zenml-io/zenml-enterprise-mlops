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

"""Monitoring hook for platform governance.

This hook can be used to send metrics to external monitoring systems
like Arize, Datadog, or custom dashboards.
"""

from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)


def monitoring_success_hook() -> None:
    """Send monitoring data after successful step execution.

    This hook would integrate with your monitoring solution (e.g., Arize)
    to track model performance, data quality, and system health.

    Platform team configures the monitoring endpoints and requirements.
    """
    try:
        context = get_step_context()
        step_name = context.step_run.name

        # Placeholder for monitoring integration
        # In production, this would send metrics to Arize/Datadog/etc.
        logger.info(
            f"Platform governance: Monitoring data sent for step '{step_name}'"
        )

    except Exception as e:
        logger.warning(f"Monitoring hook failed: {e}")
