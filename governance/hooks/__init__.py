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
    - alerter_success_hook: Send Slack notification on step success
    - alerter_failure_hook: Send Slack notification on step failure
    - pipeline_success_hook: Send notification on pipeline completion
    - pipeline_failure_hook: Send notification on pipeline failure
    - compliance_failure_hook: Log compliance events on failures
    - monitoring_success_hook: Log monitoring metrics on success

Note:
    MLflow experiment tracking is handled automatically by ZenML's
    experiment tracker stack component - no hook needed!
"""

from governance.hooks.alerting_hook import (
    alerter_failure_hook,
    alerter_success_hook,
    pipeline_failure_hook,
    pipeline_success_hook,
)
from governance.hooks.compliance_hook import compliance_failure_hook
from governance.hooks.monitoring_hook import monitoring_success_hook

__all__ = [
    # Alerting hooks (Slack, etc.)
    "alerter_success_hook",
    "alerter_failure_hook",
    "pipeline_success_hook",
    "pipeline_failure_hook",
    # Compliance hooks
    "compliance_failure_hook",
    # Monitoring hooks
    "monitoring_success_hook",
]
