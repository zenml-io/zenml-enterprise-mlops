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

"""Platform-governed data quality validation step.

This step is maintained by the platform team and required in all pipelines
to ensure data quality standards are met.
"""

from typing import Annotated

import pandas as pd
from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def validate_data_quality(
    dataset: pd.DataFrame,
    min_rows: int = 100,
    max_missing_fraction: float = 0.1,
) -> Annotated[pd.DataFrame, "validated_data"]:
    """Validate data quality according to platform standards.

    This is a platform-maintained step that enforces data quality gates.
    All pipelines must include this step to ensure compliance with
    data governance policies.

    Args:
        dataset: Input dataset to validate
        min_rows: Minimum number of rows required
        max_missing_fraction: Maximum fraction of missing values allowed

    Returns:
        Validated dataset (same as input if validation passes)

    Raises:
        ValueError: If data quality checks fail
    """
    logger.info("Platform governance: Running data quality validation")

    # Check minimum row count
    if len(dataset) < min_rows:
        raise ValueError(
            f"Data quality gate failed: Dataset has {len(dataset)} rows, "
            f"minimum required is {min_rows}"
        )

    # Check missing values
    missing_fraction = dataset.isnull().sum().sum() / (
        dataset.shape[0] * dataset.shape[1]
    )
    if missing_fraction > max_missing_fraction:
        raise ValueError(
            f"Data quality gate failed: {missing_fraction:.2%} missing values, "
            f"maximum allowed is {max_missing_fraction:.2%}"
        )

    # Check for duplicate rows
    duplicates = dataset.duplicated().sum()
    if duplicates > 0:
        logger.warning(
            f"Data quality warning: Found {duplicates} duplicate rows. "
            "Consider deduplication."
        )

    logger.info(
        f"Data quality validation passed: {len(dataset)} rows, "
        f"{missing_fraction:.2%} missing values"
    )

    return dataset
