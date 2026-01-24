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

"""Platform-managed shared steps.

These steps enforce governance policies and are required
by the platform team to be included in all pipelines.
"""

from governance.steps.data_validation import validate_data_quality
from governance.steps.model_validation import validate_model_performance

__all__ = [
    "validate_data_quality",
    "validate_model_performance",
]
