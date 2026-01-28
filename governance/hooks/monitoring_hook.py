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

"""Performance monitoring hook for external systems integration.

This hook integrates with external monitoring systems (Datadog, Prometheus, etc.)
to track pipeline performance outside of ZenML.

Note: ZenML already tracks execution time, artifacts, and metadata internally.
Use this hook only if you need to send metrics to external systems.
"""

from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)


def monitoring_success_hook() -> None:
    """Send performance metrics to external monitoring systems.

    ZenML already tracks execution time, artifacts, and metadata.
    This hook is for integrating with external systems like Datadog,
    Prometheus, or Arize for unified observability.

    Example integrations:
    - Datadog: Track step duration as custom metrics
    - Prometheus: Export pipeline execution stats
    - Arize: Monitor model performance over time
    """
    try:
        context = get_step_context()
        step_run = context.step_run

        # Calculate execution time
        if step_run.start_time and step_run.end_time:
            execution_time = (step_run.end_time - step_run.start_time).total_seconds()
        else:
            execution_time = 0.0

        # TODO: Send to your monitoring system
        # Example for Datadog:
        # from datadog import statsd
        # statsd.gauge(
        #     'zenml.step.duration',
        #     execution_time,
        #     tags=[
        #         f'pipeline:{context.pipeline_run.name}',
        #         f'step:{step_run.name}',
        #         f'workspace:{Client().active_workspace.name}'
        #     ]
        # )

        # Example for Prometheus:
        # from prometheus_client import Gauge
        # step_duration = Gauge('zenml_step_duration_seconds', 'Step execution time')
        # step_duration.set(execution_time)

        logger.info(
            f"Step '{step_run.name}' completed in {execution_time:.2f}s. "
            f"Add monitoring integration here."
        )

    except Exception as e:
        # Never fail pipeline due to monitoring
        logger.warning(f"Monitoring hook failed: {e}")
