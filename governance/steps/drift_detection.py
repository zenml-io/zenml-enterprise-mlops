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
# WITHOUT WARRANTIES OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# restrictions under the License.

"""Platform-governed drift detection using ZenML Evidently steps."""

from typing import Any

import pandas as pd
from zenml.integrations.evidently.metrics import EvidentlyMetricConfig
from zenml.integrations.evidently.steps import evidently_report_step

# ZenML Evidently report step configured for data drift detection
drift_report_step = evidently_report_step.with_options(
    parameters=dict(
        metrics=[
            EvidentlyMetricConfig.metric("DataDriftPreset", drift_share=0.5),
        ],
    ),
)
