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

"""ML pipelines for the patient readmission prediction use case."""

from src.pipelines.batch_inference import batch_inference_pipeline
from src.pipelines.champion_challenger import champion_challenger_pipeline
from src.pipelines.realtime_inference import inference_service
from src.pipelines.training import training_pipeline

__all__ = [
    "batch_inference_pipeline",
    "champion_challenger_pipeline",
    "inference_service",
    "training_pipeline",
]
