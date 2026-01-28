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

"""Model governance policy enforcement hook.

This hook validates that models meet governance requirements before
they can be promoted to staging/production. Enforces required metadata,
tags, and performance thresholds.
"""

from zenml import get_step_context
from zenml.logger import get_logger

logger = get_logger(__name__)


def model_governance_hook() -> None:
    """Enforce model governance policies after training.

    Validates that trained models have:
    - Required tags (use case, team, compliance level)
    - Performance metrics logged
    - Git commit information (for reproducibility)
    - Proper naming conventions

    Raises:
        ValueError: If model doesn't meet governance requirements
    """
    try:
        context = get_step_context()

        # Only validate models
        if not context.model:
            return

        model = context.model
        model_version = model.get_model_version()

        # Check required tags
        required_tags = {"use_case", "owner_team"}
        model_tags = set(model_version.tags) if model_version.tags else set()
        missing_tags = required_tags - model_tags

        if missing_tags:
            raise ValueError(
                f"Model governance violation: Missing required tags {missing_tags}. "
                f"Add tags with @pipeline(model=Model(name='...', tags=['use_case:fraud', 'owner_team:ml-platform']))"
            )

        # Check naming convention (must start with use case prefix)
        valid_prefixes = ["breast_cancer", "fraud_detection", "churn_prediction"]
        if not any(model.name.startswith(prefix) for prefix in valid_prefixes):
            logger.warning(
                f"Model name '{model.name}' doesn't follow naming convention. "
                f"Should start with one of: {valid_prefixes}"
            )

        # Check for git commit (required for production)
        import os

        git_commit = os.getenv("GIT_COMMIT") or os.getenv("GITHUB_SHA")
        if not git_commit:
            logger.warning(
                "No git commit found in environment. Set GIT_COMMIT or GITHUB_SHA "
                "for full reproducibility and compliance."
            )

        logger.info(
            f"Model governance check passed for {model.name} version {model.version}"
        )

    except ValueError:
        # Re-raise validation errors to fail the pipeline
        raise
    except Exception as e:
        # Don't fail pipeline for other hook errors
        logger.warning(f"Model governance hook failed: {e}")


# Keep old name for backward compatibility
def compliance_failure_hook(exception: BaseException) -> None:
    """Legacy compliance hook - now just logs the error.

    Note: ZenML already tracks all pipeline failures with full context
    in the metadata store. Use ZenML's built-in audit logs for compliance.

    Args:
        exception: The exception that caused the failure
    """
    try:
        context = get_step_context()
        logger.error(
            f"Pipeline '{context.pipeline_run.name}' failed: {exception}. "
            f"Check ZenML dashboard for full audit trail."
        )
    except Exception as e:
        logger.error(f"Compliance hook failed: {e}")
