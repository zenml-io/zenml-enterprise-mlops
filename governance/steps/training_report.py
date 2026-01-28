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

"""Training report generation for governance and PR comments.

This module generates human-readable training reports that can be:
- Posted as PR comments for visibility
- Stored as artifacts for audit trails
- Used for model approval decisions

Inspired by zenml-gitflow's model appraisal pattern.
"""

import os
from datetime import datetime, timezone
from typing import Annotated

import pandas as pd
from zenml import get_step_context, step
from zenml.logger import get_logger
from zenml.types import HTMLString

logger = get_logger(__name__)


def _generate_data_quality_section(
    dataset: pd.DataFrame,
    dataset_name: str,
    min_rows: int = 100,
    max_missing_fraction: float = 0.1,
) -> tuple[str, bool]:
    """Generate data quality section for report.

    Returns:
        Tuple of (markdown_section, passed)
    """
    n_rows, n_cols = dataset.shape
    missing_count = dataset.isnull().sum().sum()
    total_cells = n_rows * n_cols
    missing_fraction = missing_count / total_cells if total_cells > 0 else 0
    duplicates = dataset.duplicated().sum()

    row_check = n_rows >= min_rows
    missing_check = missing_fraction <= max_missing_fraction

    passed = row_check and missing_check

    section = f"""
### Data Quality: {dataset_name}

| Check | Threshold | Actual | Result |
|-------|-----------|--------|--------|
| Minimum rows | {min_rows} | {n_rows} | {'✅ PASS' if row_check else '❌ FAIL'} |
| Missing values | ≤{max_missing_fraction:.1%} | {missing_fraction:.2%} | {'✅ PASS' if missing_check else '❌ FAIL'} |
| Duplicate rows | - | {duplicates} | {'⚠️ WARNING' if duplicates > 0 else '✅ OK'} |

**Summary**: {n_rows:,} rows × {n_cols} columns, {missing_count:,} missing values
"""
    return section, passed


def _generate_model_performance_section(
    metrics: dict[str, float],
    min_accuracy: float = 0.7,
    min_precision: float = 0.7,
    min_recall: float = 0.7,
) -> tuple[str, bool]:
    """Generate model performance section for report.

    Returns:
        Tuple of (markdown_section, passed)
    """
    accuracy = metrics.get("accuracy", 0)
    precision = metrics.get("precision", 0)
    recall = metrics.get("recall", 0)
    f1 = metrics.get("f1_score", 0)
    roc_auc = metrics.get("roc_auc", 0)

    acc_check = accuracy >= min_accuracy
    prec_check = precision >= min_precision
    rec_check = recall >= min_recall

    passed = acc_check and prec_check and rec_check

    section = f"""
### Model Performance

| Metric | Threshold | Actual | Result |
|--------|-----------|--------|--------|
| Accuracy | ≥{min_accuracy:.1%} | {accuracy:.2%} | {'✅ PASS' if acc_check else '❌ FAIL'} |
| Precision | ≥{min_precision:.1%} | {precision:.2%} | {'✅ PASS' if prec_check else '❌ FAIL'} |
| Recall | ≥{min_recall:.1%} | {recall:.2%} | {'✅ PASS' if rec_check else '❌ FAIL'} |
| F1 Score | - | {f1:.2%} | ℹ️ INFO |
| ROC AUC | - | {roc_auc:.2%} | ℹ️ INFO |
"""
    return section, passed


@step
def generate_training_report(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    metrics: dict[str, float],
    min_accuracy: float = 0.7,
    min_precision: float = 0.7,
    min_recall: float = 0.7,
    min_rows: int = 100,
    max_missing_fraction: float = 0.1,
    write_to_file: bool = True,
    output_path: str = "training_report.md",
) -> Annotated[HTMLString, "training_report"]:
    """Generate a comprehensive training report for PR comments and audit trails.

    This step produces an HTML report summarizing:
    - Data quality checks (row count, missing values, duplicates)
    - Model performance metrics vs thresholds
    - Overall pass/fail decision

    The report can be used for:
    - ZenML dashboard visualization (HTMLString)
    - PR comments (immediate visibility)
    - Audit trails (compliance)
    - Model approval gates (governance)

    Args:
        X_train: Training dataset
        X_test: Test dataset
        metrics: Model performance metrics
        min_accuracy: Minimum accuracy threshold
        min_precision: Minimum precision threshold
        min_recall: Minimum recall threshold
        min_rows: Minimum rows required
        max_missing_fraction: Maximum missing value fraction
        write_to_file: Whether to write report to file (for CI)
        output_path: File path for report output

    Returns:
        HTMLString report for dashboard visualization
    """
    context = get_step_context()

    # Get model and pipeline info
    model_name = context.model.name if context.model else "unknown"
    model_version = context.model.version if context.model else "unknown"
    pipeline_name = context.pipeline_run.pipeline.name
    run_id = str(context.pipeline_run.id)[:8]

    # Get environment info from git
    git_sha = os.environ.get("ZENML_GITHUB_SHA", "unknown")[:7]
    pr_url = os.environ.get("ZENML_GITHUB_PR_URL", "")

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Generate sections
    train_section, train_passed = _generate_data_quality_section(
        X_train, "Training Data", min_rows, max_missing_fraction
    )
    test_section, test_passed = _generate_data_quality_section(
        X_test, "Test Data", min_rows // 5, max_missing_fraction  # Lower threshold for test
    )
    perf_section, perf_passed = _generate_model_performance_section(
        metrics, min_accuracy, min_precision, min_recall
    )

    overall_passed = train_passed and test_passed and perf_passed
    decision = "✅ **PASSED**" if overall_passed else "❌ **FAILED**"

    # Build full report
    report = f"""# Training Report

**Model**: `{model_name}` (v{model_version})
**Pipeline**: `{pipeline_name}` (run: `{run_id}`)
**Commit**: `{git_sha}`
**Generated**: {timestamp}

---

## Overall Decision: {decision}

| Category | Status |
|----------|--------|
| Training Data Quality | {'✅ PASS' if train_passed else '❌ FAIL'} |
| Test Data Quality | {'✅ PASS' if test_passed else '❌ FAIL'} |
| Model Performance | {'✅ PASS' if perf_passed else '❌ FAIL'} |

---

## Detailed Results

{train_section}

{test_section}

{perf_section}

---

## Next Steps

"""

    if overall_passed:
        report += """
- ✅ Model meets all quality gates
- 🔄 Merge PR to promote to staging
- 🚀 Create a release to promote to production
"""
    else:
        report += """
- ❌ Model did not meet quality gates
- 🔍 Review failed checks above
- 🔧 Fix issues and push new commit
"""

    # Add links section
    report += f"""
---

## Links

- [ZenML Dashboard](https://cloud.zenml.io)
"""
    if pr_url:
        report += f"- [Pull Request]({pr_url})\n"

    # Write to file for CI
    if write_to_file:
        with open(output_path, "w") as f:
            f.write(report)
        logger.info(f"Training report written to {output_path}")

    logger.info(f"Training report generated: {decision}")

    # Convert to HTML for dashboard visualization
    html_report = generate_html_report(report)
    return HTMLString(html_report)


def generate_html_report(markdown_report: str) -> str:
    """Convert markdown report to HTML with styling.

    Args:
        markdown_report: The markdown report string

    Returns:
        HTML report with embedded CSS styling
    """
    # Simple markdown to HTML conversion
    # In production, use a library like markdown2 or mistune
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Training Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
    </style>
</head>
<body>
<pre style="white-space: pre-wrap; font-family: inherit;">
{markdown_report}
</pre>
</body>
</html>
"""
    return html
