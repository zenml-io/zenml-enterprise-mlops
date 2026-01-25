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
"""

from governance.hooks.compliance_hook import compliance_failure_hook
from governance.hooks.mlflow_hook import mlflow_success_hook
from governance.hooks.monitoring_hook import monitoring_success_hook

__all__ = [
    "compliance_failure_hook",
    "mlflow_success_hook",
    "monitoring_success_hook",
]
