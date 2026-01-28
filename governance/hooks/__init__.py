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

"""Platform hooks for governance enforcement.

Hooks are automatically executed at pipeline lifecycle events
to enforce platform policies without modifying user code.

Available Hooks:
    Alerting (External Notifications):
        - alerter_failure_hook: Send Slack alert on step failure
        - alerter_success_hook: Send Slack notification on step success
        - pipeline_failure_hook: Send alert on pipeline failure
        - pipeline_success_hook: Send notification on pipeline completion

    Policy Enforcement:
        - model_governance_hook: Enforce required tags and naming conventions

    External Monitoring:
        - monitoring_success_hook: Send metrics to Datadog/Prometheus

    Legacy:
        - compliance_failure_hook: Deprecated, kept for backward compatibility
"""

from governance.hooks.alerting_hook import (
    alerter_failure_hook,
    alerter_success_hook,
    pipeline_failure_hook,
    pipeline_success_hook,
)
from governance.hooks.compliance_hook import (
    compliance_failure_hook,
    model_governance_hook,
)
from governance.hooks.monitoring_hook import monitoring_success_hook

__all__ = [
    "alerter_failure_hook",
    "alerter_success_hook",
    "compliance_failure_hook",
    "model_governance_hook",
    "monitoring_success_hook",
    "pipeline_failure_hook",
    "pipeline_success_hook",
]
