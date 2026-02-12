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

"""Slack alert when data drift is detected in batch inference."""

import json
from typing import Any

import pandas as pd
from zenml import get_step_context, step
from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)


def _parse_evidently_report(
    report: Any,
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
) -> dict:
    """Parse Evidently report into drift summary dict."""
    dataset_drift = False
    number_of_drifted_columns = 0
    share_of_drifted_columns = 0.0
    drifted_columns: list[str] = []
    columns = list(reference_data.columns)

    report_dict: dict = {}
    if isinstance(report, dict):
        report_dict = report
    elif isinstance(report, str):
        try:
            report_dict = json.loads(report)
        except Exception:
            pass
    else:
        for attr in ("as_dict", "dict", "to_dict", "model_dump"):
            fn = getattr(report, attr, None)
            if callable(fn):
                try:
                    report_dict = fn() or {}
                    break
                except Exception:
                    pass
        if not report_dict and hasattr(report, "json"):
            try:
                report_dict = json.loads(report.json())
            except Exception:
                pass

    if not report_dict:
        logger.warning(
            "Could not parse Evidently report (type=%s). "
            "Tried as_dict, dict, to_dict, model_dump, json.",
            type(report).__name__,
        )

    for metric in report_dict.get("metrics", []):
        result = metric.get("result", metric.get("value", {}))
        if not isinstance(result, dict):
            continue
        if "dataset_drift" in result:
            dataset_drift = result["dataset_drift"]
        if "number_of_drifted_columns" in result:
            number_of_drifted_columns = result["number_of_drifted_columns"]
        if "share_of_drifted_columns" in result:
            share_of_drifted_columns = result["share_of_drifted_columns"]
        if "count" in result and "share" in result:
            number_of_drifted_columns = result["count"]
            share_of_drifted_columns = result["share"]
            dataset_drift = share_of_drifted_columns >= 0.5
        if "drifted_columns" in result:
            drifted_columns = result.get("drifted_columns", [])
        elif "drift_by_columns" in result:
            for col_name, col_info in result.get("drift_by_columns", {}).items():
                if isinstance(col_info, dict) and col_info.get("drift_detected"):
                    drifted_columns.append(col_info.get("column_name", col_name))
        elif "columns" in result:
            for col_info in result.get("columns", []):
                if isinstance(col_info, dict) and col_info.get("drift_detected"):
                    drifted_columns.append(col_info.get("column_name", ""))

    if not drifted_columns and number_of_drifted_columns > 0:
        drifted_columns = list(columns[:number_of_drifted_columns])

    return {
        "dataset_drift_detected": bool(dataset_drift),
        "number_of_drifted_columns": number_of_drifted_columns,
        "share_of_drifted_columns": float(share_of_drifted_columns),
        "reference_rows": len(reference_data),
        "current_rows": len(current_data),
        "drifted_columns": drifted_columns,
    }


@step
def drift_alert_slack(
    report_json: Any,
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    simulate_drift: bool = False,
) -> str:
    """Send Slack alert when drift is detected.

    Parses Evidently report (report_json) and sends alert when drift detected.
    No-ops if no alerter or if drift was not detected.

    Args:
        report_json: Evidently report (dict or Report object) from drift_report_step.
        reference_data: Reference DataFrame (for row count).
        current_data: Current DataFrame (for row count).
        simulate_drift: When True, message indicates drift was simulated for testing.

    Returns:
        Status message (sent/skipped)
    """
    drift_report = _parse_evidently_report(
        report_json, reference_data, current_data
    )

    # Skip alert only when no drift at all
    if not drift_report.get("dataset_drift_detected") and drift_report.get(
        "number_of_drifted_columns", 0
    ) == 0:
        logger.info("No drift detected - skipping Slack notification")
        return "No drift detected - alert skipped"

    client = Client()
    alerter = client.active_stack.alerter

    if alerter is None:
        logger.info("No alerter configured - skipping Slack notification")
        return "No alerter configured"

    context = get_step_context()
    pipeline_name = context.pipeline_run.pipeline.name
    run_id = str(context.pipeline_run.id)
    run_name = context.pipeline_run.name

    drifted_cols = drift_report.get("number_of_drifted_columns", 0)
    share_drifted = drift_report.get("share_of_drifted_columns", 0)
    if not isinstance(share_drifted, (int, float)):
        share_drifted = 0
    ref_rows = drift_report.get("reference_rows", 0)
    cur_rows = drift_report.get("current_rows", 0)
    drifted_columns = drift_report.get("drifted_columns", [])
    cols_preview = (
        ", ".join(drifted_columns[:5])
        + ("..." if len(drifted_columns) > 5 else "")
        if drifted_columns
        else "—"
    )

    message = (
        "⚠️ *Data Drift Detected in Batch Inference*\n\n"
        f"• Pipeline: `{pipeline_name}`\n"
        f"• Run: `{run_name}`\n"
        f"• Drifted columns: {drifted_cols} ({share_drifted:.1%} of features)\n"
        f"• Affected: `{cols_preview}`\n"
        f"• Reference samples: {ref_rows}\n"
        f"• Current samples: {cur_rows}\n\n"
        "_Consider retraining or investigating the cause._"
    )

    alerter.post(message=message)
    logger.info(f"Slack drift alert sent for pipeline run {run_id}")

    return f"Drift alert sent (run_id={run_id})"
