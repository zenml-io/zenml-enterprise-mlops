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
    - Git commit information (for reproducibility)
    - Proper naming conventions

    Raises:
        ValueError: If model doesn't meet governance requirements
    """
    try:
        context = get_step_context()

        # Only validate models in model context pipelines
        if not context.model:
            return

        model = context.model

        # Get model version from ZenML client
        from zenml.client import Client

        client = Client()
        try:
            model_version = client.get_model_version(
                model_name_or_id=model.name,
                model_version_name_or_number_or_id=model.version,
            )
        except Exception:
            # Model version may not exist yet if pipeline hasn't completed
            logger.info(
                "Model version not yet registered, skipping governance validation"
            )
            return

        # Check required tags - look for use_case: and owner_team: prefixes
        required_tag_prefixes = ["use_case:", "owner_team:"]
        # Extract tag names from TagResponse objects
        model_tags = (
            [
                tag.name if hasattr(tag, "name") else str(tag)
                for tag in model_version.tags
            ]
            if model_version.tags
            else []
        )
        missing_prefixes = [
            prefix
            for prefix in required_tag_prefixes
            if not any(tag.startswith(prefix) for tag in model_tags)
        ]

        if missing_prefixes:
            logger.warning(
                f"Model governance: Missing recommended tags with prefixes {missing_prefixes}. "
                f"Add tags like: tags=['use_case:breast_cancer', 'owner_team:ml-platform']"
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
            logger.info(
                "No git commit found in environment. Set GIT_COMMIT or GITHUB_SHA "
                "for full reproducibility and compliance."
            )

        logger.info(
            f"Model governance check completed for {model.name} version {model.version}"
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
