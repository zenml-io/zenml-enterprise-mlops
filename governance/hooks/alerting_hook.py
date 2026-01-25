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

"""Alerting hooks for pipeline notifications.

These hooks send notifications to Slack (or other alerters) when pipeline
steps succeed or fail. They use ZenML's built-in alerter stack component.

Setup:
    1. Register a Slack alerter:
       zenml alerter register slack_alerter \\
           --flavor=slack \\
           --slack_token=<your-token> \\
           --default_slack_channel_id=<channel-id>

    2. Add to your stack:
       zenml stack update <stack-name> --alerter slack_alerter

Usage:
    from governance.hooks import alerter_success_hook, alerter_failure_hook

    @pipeline(on_failure=alerter_failure_hook)
    def training_pipeline():
        ...

    # Or use ZenML's built-in hooks directly:
    from zenml.hooks import alerter_success_hook, alerter_failure_hook
"""

from zenml import get_step_context
from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)


def alerter_success_hook() -> None:
    """Send success notification via configured alerter.

    This hook sends a formatted success message to Slack (or other alerter)
    when a pipeline step completes successfully.

    If no alerter is configured, it logs a message instead.
    """
    try:
        context = get_step_context()
        step_name = context.step_run.name
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        message = (
            f"✅ *Step Succeeded*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Step: `{step_name}`\n"
            f"• Run: `{run_name}`"
        )

        # Try to use the alerter from the active stack
        client = Client()
        alerter = client.active_stack.alerter

        if alerter:
            alerter.post(message=message)
            logger.info(f"Success notification sent for step '{step_name}'")
        else:
            logger.info(
                f"No alerter configured. Step '{step_name}' succeeded in '{pipeline_name}'"
            )

    except Exception as e:
        # Don't fail the pipeline if alerting fails
        logger.warning(f"Could not send success alert: {e}")


def alerter_failure_hook(exception: BaseException) -> None:
    """Send failure notification via configured alerter.

    This hook sends a formatted failure message to Slack (or other alerter)
    when a pipeline step fails. Includes exception details for debugging.

    Args:
        exception: The exception that caused the step to fail.
    """
    try:
        context = get_step_context()
        step_name = context.step_run.name
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        message = (
            f"❌ *Step Failed*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Step: `{step_name}`\n"
            f"• Run: `{run_name}`\n"
            f"• Error: `{type(exception).__name__}: {exception!s}`"
        )

        # Try to use the alerter from the active stack
        client = Client()
        alerter = client.active_stack.alerter

        if alerter:
            alerter.post(message=message)
            logger.info(f"Failure notification sent for step '{step_name}'")
        else:
            logger.warning(
                f"No alerter configured. Step '{step_name}' failed: {exception}"
            )

    except Exception as e:
        # Don't fail the pipeline if alerting fails
        logger.warning(f"Could not send failure alert: {e}")


def pipeline_success_hook() -> None:
    """Send notification when entire pipeline succeeds.

    Use this at the pipeline level for end-of-pipeline notifications.
    """
    try:
        context = get_step_context()
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        # Get model info if available
        model_info = ""
        if context.model:
            model_info = f"\n• Model: `{context.model.name}` v{context.model.version}"

        message = (
            f"🎉 *Pipeline Completed Successfully*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Run: `{run_name}`"
            f"{model_info}"
        )

        client = Client()
        alerter = client.active_stack.alerter

        if alerter:
            alerter.post(message=message)
            logger.info(f"Pipeline success notification sent for '{pipeline_name}'")
        else:
            logger.info(f"Pipeline '{pipeline_name}' completed successfully")

    except Exception as e:
        logger.warning(f"Could not send pipeline success alert: {e}")


def pipeline_failure_hook(exception: BaseException) -> None:
    """Send notification when pipeline fails.

    Use this at the pipeline level for critical failure alerts.

    Args:
        exception: The exception that caused the pipeline to fail.
    """
    try:
        context = get_step_context()
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        message = (
            f"🚨 *Pipeline Failed*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Run: `{run_name}`\n"
            f"• Error: `{type(exception).__name__}: {exception!s}`\n"
            f"• Action Required: Please investigate immediately"
        )

        client = Client()
        alerter = client.active_stack.alerter

        if alerter:
            alerter.post(message=message)
            logger.info(f"Pipeline failure notification sent for '{pipeline_name}'")
        else:
            logger.error(f"Pipeline '{pipeline_name}' failed: {exception}")

    except Exception as e:
        logger.warning(f"Could not send pipeline failure alert: {e}")
