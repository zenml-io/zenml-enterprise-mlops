#!/usr/bin/env python
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

"""Generate training report from the latest pipeline run.

This script extracts results from the most recent training pipeline run
and generates a markdown report suitable for PR comments.

Usage:
    python scripts/generate_training_report.py
    python scripts/generate_training_report.py --output report.md
    python scripts/generate_training_report.py --pipeline training --model breast_cancer_classifier
"""

import os
import sys
from pathlib import Path

import click

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from zenml.client import Client
from zenml.logger import get_logger

logger = get_logger(__name__)


def get_latest_training_run(client: Client, pipeline_name: str = "training_pipeline"):
    """Get the most recent training pipeline run.

    Args:
        client: ZenML client
        pipeline_name: Name of the training pipeline

    Returns:
        The latest pipeline run or None
    """
    try:
        runs = client.list_pipeline_runs(
            pipeline_name=pipeline_name,
            sort_by="desc:created",
            size=1,
        )
        if runs:
            return runs[0]
    except Exception as e:
        logger.warning(f"Could not find pipeline runs for '{pipeline_name}': {e}")

    return None


def extract_metrics_from_run(run) -> dict:
    """Extract metrics from a pipeline run.

    Args:
        run: Pipeline run object

    Returns:
        Dictionary of metrics
    """
    metrics = {}

    # Try to get metrics from the evaluate_model step
    try:
        for step_name, step_run in run.steps.items():
            if "evaluate" in step_name.lower() or "metrics" in step_name.lower():
                for output_name, artifact in step_run.outputs.items():
                    if "metrics" in output_name.lower():
                        metrics = artifact.load()
                        break
    except Exception as e:
        logger.warning(f"Could not extract metrics: {e}")

    # Fallback: try model version metadata
    if not metrics:
        try:
            # Get model version from run
            model = run.model
            if model:
                run_metadata = model.run_metadata or {}
                for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
                    if key in run_metadata:
                        value = run_metadata[key]
                        metrics[key] = value.value if hasattr(value, "value") else value
        except Exception as e:
            logger.warning(f"Could not extract metrics from model version: {e}")

    return metrics


def generate_report(
    run,
    metrics: dict,
    min_accuracy: float = 0.7,
    min_precision: float = 0.7,
    min_recall: float = 0.7,
) -> tuple[str, bool]:
    """Generate a markdown report from pipeline run results.

    Args:
        run: Pipeline run object
        metrics: Model metrics dictionary
        min_accuracy: Minimum accuracy threshold
        min_precision: Minimum precision threshold
        min_recall: Minimum recall threshold

    Returns:
        Tuple of (markdown_report, passed)
    """
    # Extract run info
    run_id = str(run.id)[:8]
    pipeline_name = run.pipeline.name if run.pipeline else "unknown"
    status = run.status.value if run.status else "unknown"
    created = run.created.strftime("%Y-%m-%d %H:%M UTC") if run.created else "unknown"

    # Get model info
    model_name = "unknown"
    model_version = "unknown"
    if run.model:
        model_name = run.model.name
        model_version = run.model.version

    # Get git info from environment
    git_sha = os.environ.get("ZENML_GITHUB_SHA", os.environ.get("GITHUB_SHA", "unknown"))[:7]
    pr_url = os.environ.get("ZENML_GITHUB_PR_URL", os.environ.get("GITHUB_PR_URL", ""))

    # Calculate pass/fail
    accuracy = metrics.get("accuracy", 0)
    precision = metrics.get("precision", 0)
    recall = metrics.get("recall", 0)
    f1 = metrics.get("f1_score", 0)
    roc_auc = metrics.get("roc_auc", 0)

    acc_pass = accuracy >= min_accuracy
    prec_pass = precision >= min_precision
    rec_pass = recall >= min_recall
    run_success = status == "completed"

    overall_passed = acc_pass and prec_pass and rec_pass and run_success
    decision = "✅ **PASSED**" if overall_passed else "❌ **FAILED**"

    # Build report
    report = f"""# Training Report

**Model**: `{model_name}` (v{model_version})
**Pipeline**: `{pipeline_name}` (run: `{run_id}`)
**Status**: {status}
**Commit**: `{git_sha}`
**Generated**: {created}

---

## Overall Decision: {decision}

| Category | Status |
|----------|--------|
| Pipeline Execution | {'✅ PASS' if run_success else '❌ FAIL'} |
| Model Performance | {'✅ PASS' if (acc_pass and prec_pass and rec_pass) else '❌ FAIL'} |

---

## Model Performance

| Metric | Threshold | Actual | Result |
|--------|-----------|--------|--------|
| Accuracy | ≥{min_accuracy:.1%} | {accuracy:.2%} | {'✅ PASS' if acc_pass else '❌ FAIL'} |
| Precision | ≥{min_precision:.1%} | {precision:.2%} | {'✅ PASS' if prec_pass else '❌ FAIL'} |
| Recall | ≥{min_recall:.1%} | {recall:.2%} | {'✅ PASS' if rec_pass else '❌ FAIL'} |
| F1 Score | - | {f1:.2%} | ℹ️ INFO |
| ROC AUC | - | {roc_auc:.2%} | ℹ️ INFO |

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

    report += f"""
---

## Links

- [ZenML Dashboard](https://cloud.zenml.io)
"""
    if pr_url:
        report += f"- [Pull Request]({pr_url})\n"

    return report, overall_passed


@click.command()
@click.option(
    "--pipeline",
    default="training_pipeline",
    help="Pipeline name to get results from",
)
@click.option(
    "--output",
    default="training_report.md",
    help="Output file path for the report",
)
@click.option(
    "--min-accuracy",
    default=0.7,
    help="Minimum accuracy threshold",
)
@click.option(
    "--min-precision",
    default=0.7,
    help="Minimum precision threshold",
)
@click.option(
    "--min-recall",
    default=0.7,
    help="Minimum recall threshold",
)
def main(
    pipeline: str,
    output: str,
    min_accuracy: float,
    min_precision: float,
    min_recall: float,
):
    """Generate training report from the latest pipeline run."""
    logger.info("Generating training report...")

    client = Client()

    # Get latest run
    run = get_latest_training_run(client, pipeline)
    if not run:
        logger.error(f"No runs found for pipeline '{pipeline}'")
        # Generate a fallback report
        fallback_report = f"""# Training Report

## ❌ No Pipeline Run Found

Could not find any runs for pipeline `{pipeline}`.

Please ensure the training pipeline has completed before generating the report.
"""
        with open(output, "w") as f:
            f.write(fallback_report)
        sys.exit(1)

    logger.info(f"Found run: {run.id}")

    # Extract metrics
    metrics = extract_metrics_from_run(run)
    logger.info(f"Extracted metrics: {metrics}")

    # Generate report
    report, passed = generate_report(
        run,
        metrics,
        min_accuracy,
        min_precision,
        min_recall,
    )

    # Write report
    with open(output, "w") as f:
        f.write(report)

    logger.info(f"Report written to {output}")
    logger.info(f"Overall result: {'PASSED' if passed else 'FAILED'}")

    # Exit with appropriate code for CI
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
