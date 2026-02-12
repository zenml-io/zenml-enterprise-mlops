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

"""Simulate data drift for testing drift detection and alerting.

Use simulate_drift: true in staging config to verify the drift pipeline.
"""

from typing import Annotated

import numpy as np
import pandas as pd
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def introduce_simulated_drift(
    data: pd.DataFrame,
    simulate_drift: bool = False,
    drift_strength: float = 0.6,
    seed: int = 42,
) -> Annotated[pd.DataFrame, "data"]:
    """Introduce simulated drift for testing drift detection.

    When enabled, shifts numerical column means and adds noise to simulate
    distribution changes. Use with batch inference staging to test alerts.

    Args:
        data: Input DataFrame (e.g. X_test)
        simulate_drift: When True, apply artificial drift
        drift_strength: Magnitude of shift (0.6 default for reliable Evidently
            detection; 0.3 = subtle, 0.8 = strong)
        seed: Random seed for reproducibility

    Returns:
        DataFrame (modified if simulate_drift else unchanged)
    """
    if not simulate_drift:
        logger.info("Simulated drift disabled - returning data unchanged")
        return data

    rng = np.random.default_rng(seed)
    drifted = data.copy()

    for col in drifted.select_dtypes(include=[np.number]).columns:
        mean_val = drifted[col].mean()
        std_val = drifted[col].std()
        if std_val > 0 and pd.notna(mean_val):
            # Shift mean and add extra noise
            shift = mean_val * drift_strength * (rng.random() - 0.5) * 2
            noise = rng.normal(0, std_val * drift_strength, size=len(drifted))
            drifted[col] = drifted[col] + shift + noise

    logger.info(
        f"Simulated drift applied (strength={drift_strength}) - "
        f"{len(drifted.columns)} numerical columns modified"
    )
    return drifted
