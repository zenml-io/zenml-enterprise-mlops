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

"""Platform-governed model validation step.

This step enforces minimum performance requirements for models
before they can be promoted to production.
"""

from typing import Dict
from typing_extensions import Annotated

from zenml import step
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def validate_model_performance(
    metrics: Dict[str, float],
    min_accuracy: float = 0.7,
    min_precision: float = 0.7,
    min_recall: float = 0.7,
) -> Annotated[bool, "validation_passed"]:
    """Validate model performance against platform requirements.

    This is a platform-maintained step that enforces minimum performance
    standards. Models failing these checks cannot be promoted to production.

    Args:
        metrics: Dictionary of model performance metrics
        min_accuracy: Minimum accuracy required
        min_precision: Minimum precision required
        min_recall: Minimum recall required

    Returns:
        True if validation passes

    Raises:
        ValueError: If model does not meet minimum requirements
    """
    logger.info("Platform governance: Validating model performance")

    failures = []

    # Check accuracy
    if metrics.get("accuracy", 0) < min_accuracy:
        failures.append(
            f"Accuracy {metrics.get('accuracy', 0):.3f} < {min_accuracy:.3f}"
        )

    # Check precision
    if metrics.get("precision", 0) < min_precision:
        failures.append(
            f"Precision {metrics.get('precision', 0):.3f} < {min_precision:.3f}"
        )

    # Check recall
    if metrics.get("recall", 0) < min_recall:
        failures.append(
            f"Recall {metrics.get('recall', 0):.3f} < {min_recall:.3f}"
        )

    if failures:
        failure_msg = "Model validation failed:\n" + "\n".join(
            f"  - {f}" for f in failures
        )
        logger.error(failure_msg)
        raise ValueError(failure_msg)

    logger.info(
        f"Model validation passed - Accuracy: {metrics['accuracy']:.3f}, "
        f"Precision: {metrics['precision']:.3f}, "
        f"Recall: {metrics['recall']:.3f}"
    )

    return True
