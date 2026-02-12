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


def batch_inference_success_hook() -> None:
    """Send notification when batch inference step completes successfully.

    Use as step-level on_success for scale_and_predict. Includes prediction stats.
    """
    try:
        context = get_step_context()
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        # Load predictions from step output to get stats
        high_risk_count = 0
        total = 0
        try:
            outputs = getattr(context.step_run, "outputs", None) or {}
            pred_artifact = outputs.get("predictions")
            if pred_artifact is not None:
                preds = pred_artifact.load() if hasattr(pred_artifact, "load") else None
                if preds is not None:
                    total = len(preds)
                    if hasattr(preds, "columns") and "prediction" in preds.columns:
                        high_risk_count = int((preds["prediction"] == 1).sum())
        except Exception:
            pass

        stats = ""
        if total > 0:
            pct = high_risk_count / total * 100
            stats = f"\n• Predictions: {total} total, {high_risk_count} high-risk ({pct:.1f}%)"

        model_info = ""
        if context.model:
            model_info = f"\n• Model: `{context.model.name}` v{context.model.version}"

        message = (
            f"✅ *Batch Inference Completed Successfully*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Run: `{run_name}`"
            f"{model_info}"
            f"{stats}"
        )

        client = Client()
        alerter = client.active_stack.alerter
        if alerter:
            alerter.post(message=message)
            logger.info(f"Inference success notification sent for '{pipeline_name}'")
        else:
            logger.info(f"No alerter configured. Inference completed for '{pipeline_name}'")
    except Exception as e:
        logger.warning(f"Could not send inference success alert: {e}")


def drift_detection_success_hook() -> None:
    """Send notification with drift detection results when run_drift_detection completes.

    Use as step-level on_success for run_drift_detection. Sends drift stats.
    """
    try:
        context = get_step_context()
        pipeline_name = context.pipeline_run.pipeline.name
        run_name = context.pipeline_run.name

        drift_report = {}
        try:
            outputs = getattr(context.step_run, "outputs", None) or {}
            drift_artifact = outputs.get("drift_report")
            if drift_artifact is not None:
                drift_report = drift_artifact.load() if hasattr(drift_artifact, "load") else {}
            if not isinstance(drift_report, dict):
                drift_report = {}
        except Exception:
            pass

        drifted = drift_report.get("number_of_drifted_columns", 0)
        share = drift_report.get("share_of_drifted_columns", 0.0)
        if not isinstance(share, (int, float)):
            share = 0.0
        ref_rows = drift_report.get("reference_rows", 0)
        cur_rows = drift_report.get("current_rows", 0)
        detected = drift_report.get("dataset_drift_detected", False)

        status = "⚠️ Drift detected" if detected or drifted > 0 else "✓ No drift"
        message = (
            f"📊 *Drift Detection Results*\n"
            f"• Pipeline: `{pipeline_name}`\n"
            f"• Run: `{run_name}`\n"
            f"• Status: {status}\n"
            f"• Drifted columns: {drifted} ({share:.1%} of features)\n"
            f"• Reference samples: {ref_rows}\n"
            f"• Current samples: {cur_rows}"
        )

        client = Client()
        alerter = client.active_stack.alerter
        if alerter:
            alerter.post(message=message)
            logger.info(f"Drift detection results notification sent for '{pipeline_name}'")
        else:
            logger.info(f"No alerter configured. Drift check completed for '{pipeline_name}'")
    except Exception as e:
        logger.warning(f"Could not send drift detection results alert: {e}")


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
            logger.info(
                f"No alerter configured. Pipeline '{pipeline_name}' completed successfully"
            )

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
