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

"""Cross-workspace model promotion for 2-workspace architecture.

This script handles model promotion between enterprise-dev-staging and
enterprise-production workspaces. It exports model artifacts and metadata
from the source workspace, stores them in a shared GCS bucket, and imports
them into the destination workspace with full audit trail preservation.

This addresses the enterprise pain point: "Promotion is manual and error-prone"

Usage:
    # Full promotion (export + import)
    python scripts/promote_cross_workspace.py \
        --model breast_cancer_classifier \
        --source-workspace enterprise-dev-staging \
        --dest-workspace enterprise-production \
        --source-stage staging \
        --dest-stage production

    # Export only (for manual review before import)
    python scripts/promote_cross_workspace.py \
        --model breast_cancer_classifier \
        --source-workspace enterprise-dev-staging \
        --source-stage staging \
        --export-only

    # Import only (after manual approval)
    python scripts/promote_cross_workspace.py \
        --model breast_cancer_classifier \
        --dest-workspace enterprise-production \
        --dest-stage production \
        --import-from gs://zenml-core-model-exchange/exports/...

Environment Variables (can also be set in .env file):
    ZENML_DEV_STAGING_URL: URL for dev-staging workspace
    ZENML_DEV_STAGING_API_KEY: API key for dev-staging workspace
    ZENML_PRODUCTION_URL: URL for production workspace
    ZENML_PRODUCTION_API_KEY: API key for production workspace
    MODEL_EXCHANGE_BUCKET: GCS bucket for model exchange (default: zenml-core-model-exchange)
    GCP_PROJECT_ID: GCP project ID (default: zenml-core)
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import joblib
from dotenv import load_dotenv
from google.cloud import storage
from zenml.client import Client
from zenml.enums import ModelStages
from zenml.logger import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)

# Configuration (with env var overrides)
DEFAULT_EXCHANGE_BUCKET = os.getenv("MODEL_EXCHANGE_BUCKET", "zenml-core-model-exchange")
DEFAULT_GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "zenml-core")

WORKSPACE_CONFIG = {
    "enterprise-dev-staging": {
        "url_env": "ZENML_DEV_STAGING_URL",
        "api_key_env": "ZENML_DEV_STAGING_API_KEY",
        "project": os.getenv("ZENML_PROJECT", "cancer-detection"),
    },
    "enterprise-production": {
        "url_env": "ZENML_PRODUCTION_URL",
        "api_key_env": "ZENML_PRODUCTION_API_KEY",
        "project": os.getenv("ZENML_PROJECT", "cancer-detection"),
    },
}


def connect_to_workspace(workspace_name: str) -> Client:
    """Connect to a ZenML workspace by setting environment variables.

    ZenML automatically uses ZENML_STORE_URL and ZENML_STORE_API_KEY
    when creating a Client.

    Args:
        workspace_name: Name of the workspace to connect to

    Returns:
        ZenML Client connected to the workspace
    """
    config = WORKSPACE_CONFIG.get(workspace_name)
    if not config:
        raise ValueError(f"Unknown workspace: {workspace_name}")

    url = os.environ.get(config["url_env"])
    api_key = os.environ.get(config["api_key_env"])

    if not url:
        raise ValueError(
            f"Store URL not found. Set {config['url_env']} environment variable."
        )
    if not api_key:
        raise ValueError(
            f"API key not found. Set {config['api_key_env']} environment variable."
        )

    logger.info(f"Connecting to workspace: {workspace_name}")

    # Set ZenML environment variables for auto-connection
    os.environ["ZENML_STORE_URL"] = url
    os.environ["ZENML_STORE_API_KEY"] = api_key

    # Set project
    result = subprocess.run(
        ["zenml", "project", "set", config["project"]],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to set project: {result.stderr}")

    return Client()


def export_model(
    client: Client,
    model_name: str,
    source_stage: str,
    source_workspace: str,
    exchange_bucket: str,
) -> dict:
    """Export model artifacts and metadata to shared bucket.

    Args:
        client: ZenML client connected to source workspace
        model_name: Name of the model to export
        source_stage: Stage to export (staging/production/latest)
        source_workspace: Name of source workspace
        exchange_bucket: GCS bucket for model exchange

    Returns:
        Export manifest with metadata and paths
    """
    logger.info(f"Exporting {model_name} ({source_stage}) from {source_workspace}")

    # Map stage string to enum
    stage_map = {
        "staging": ModelStages.STAGING,
        "production": ModelStages.PRODUCTION,
        "latest": ModelStages.LATEST,
    }

    # Get model version
    model_version = client.get_model_version(
        model_name_or_id=model_name,
        model_version_name_or_number_or_id=stage_map.get(source_stage, source_stage),
    )

    logger.info(f"Found model version: {model_version.number}")

    # Load artifacts
    model_artifact = model_version.get_artifact("sklearn_classifier")
    scaler_artifact = model_version.get_artifact("scaler")

    if model_artifact is None:
        raise ValueError(f"No model artifact found for {model_name}")

    model = model_artifact.load()
    scaler = scaler_artifact.load() if scaler_artifact else None

    # Extract metrics from metadata
    metrics = {}
    for key, value in (model_version.run_metadata or {}).items():
        if hasattr(value, "value"):
            metrics[key] = value.value
        elif isinstance(value, (int, float, str, bool)):
            metrics[key] = value

    # Get pipeline run info
    pipeline_run_ids = list(model_version.pipeline_run_ids or [])
    pipeline_run_url = None
    if pipeline_run_ids:
        pipeline_run_url = (
            f"https://cloud.zenml.io/workspaces/{source_workspace}/"
            f"pipelines/runs/{pipeline_run_ids[0]}"
        )

    # Create export manifest
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    export_path = f"exports/{model_name}/{source_workspace}_to_production/{timestamp}"

    manifest = {
        "model_name": model_name,
        "export_timestamp": datetime.utcnow().isoformat(),
        "export_path": f"gs://{exchange_bucket}/{export_path}",
        # Source information
        "source": {
            "workspace": source_workspace,
            "model_version": model_version.number,
            "model_version_id": str(model_version.id),
            "stage": source_stage,
            "pipeline_run_ids": [str(pid) for pid in pipeline_run_ids],
            "pipeline_run_url": pipeline_run_url,
            "created_at": str(model_version.created),
        },
        # Metrics for validation
        "metrics": metrics,
        # Artifacts
        "artifacts": {
            "model": f"gs://{exchange_bucket}/{export_path}/model.joblib",
            "scaler": f"gs://{exchange_bucket}/{export_path}/scaler.joblib"
            if scaler
            else None,
        },
        # Lineage chain (will be extended on each promotion)
        "promotion_chain": [
            {
                "action": "exported",
                "from_workspace": source_workspace,
                "from_version": model_version.number,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    }

    # Upload to GCS
    gcs_client = storage.Client(project=DEFAULT_GCP_PROJECT)
    bucket = gcs_client.bucket(exchange_bucket)

    # Upload model artifact
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
        joblib.dump(model, f.name)
        blob = bucket.blob(f"{export_path}/model.joblib")
        blob.upload_from_filename(f.name)
        os.unlink(f.name)
        logger.info(f"Uploaded model to gs://{exchange_bucket}/{export_path}/model.joblib")

    # Upload scaler if exists
    if scaler is not None:
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            joblib.dump(scaler, f.name)
            blob = bucket.blob(f"{export_path}/scaler.joblib")
            blob.upload_from_filename(f.name)
            os.unlink(f.name)
            logger.info(f"Uploaded scaler to gs://{exchange_bucket}/{export_path}/scaler.joblib")

    # Upload manifest
    manifest_blob = bucket.blob(f"{export_path}/manifest.json")
    manifest_blob.upload_from_string(
        json.dumps(manifest, indent=2, default=str),
        content_type="application/json",
    )
    logger.info(f"Uploaded manifest to gs://{exchange_bucket}/{export_path}/manifest.json")

    # Write export path to file for GitHub Actions
    with open("export_path.txt", "w") as f:
        f.write(f"gs://{exchange_bucket}/{export_path}")

    return manifest


def validate_for_promotion(manifest: dict, dest_workspace: str) -> bool:
    """Validate model meets requirements for destination workspace.

    Args:
        manifest: Export manifest with metrics
        dest_workspace: Destination workspace name

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    metrics = manifest.get("metrics", {})

    # Define requirements per destination
    requirements = {
        "enterprise-staging": {
            "accuracy": 0.70,
            "precision": 0.70,
            "recall": 0.70,
        },
        "enterprise-production": {
            "accuracy": 0.80,
            "precision": 0.80,
            "recall": 0.80,
        },
    }

    workspace_requirements = requirements.get(dest_workspace, {})

    failures = []
    for metric, min_value in workspace_requirements.items():
        actual = metrics.get(metric)
        if actual is None:
            failures.append(f"{metric}: missing (required >= {min_value})")
        elif float(actual) < min_value:
            failures.append(f"{metric}: {float(actual):.3f} < {min_value:.3f}")

    if failures:
        error_msg = f"Model does not meet {dest_workspace} requirements:\n"
        error_msg += "\n".join(f"  - {f}" for f in failures)
        raise ValueError(error_msg)

    logger.info(f"✅ Validation passed for {dest_workspace}")
    return True


def import_model(
    client: Client,
    manifest_path: str,
    dest_workspace: str,
    dest_stage: str,
    exchange_bucket: str,
) -> str:
    """Import model artifacts into destination workspace.

    Args:
        client: ZenML client connected to destination workspace
        manifest_path: GCS path to export manifest
        dest_workspace: Name of destination workspace
        dest_stage: Target stage in destination workspace
        exchange_bucket: GCS bucket name

    Returns:
        New model version ID in destination workspace
    """
    logger.info(f"Importing model into {dest_workspace}")

    # Load manifest from GCS
    gcs_client = storage.Client(project=DEFAULT_GCP_PROJECT)
    bucket = gcs_client.bucket(exchange_bucket)

    # Parse manifest path
    if manifest_path.startswith("gs://"):
        manifest_path = manifest_path.replace(f"gs://{exchange_bucket}/", "")
    if not manifest_path.endswith("/manifest.json"):
        manifest_path = f"{manifest_path}/manifest.json"

    manifest_blob = bucket.blob(manifest_path)
    manifest = json.loads(manifest_blob.download_as_string())

    logger.info(f"Loaded manifest for {manifest['model_name']}")
    logger.info(f"Source: {manifest['source']['workspace']} v{manifest['source']['model_version']}")

    # Download model artifacts to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download model
        model_path = manifest["artifacts"]["model"].replace(f"gs://{exchange_bucket}/", "")
        model_blob = bucket.blob(model_path)
        local_model_path = Path(tmpdir) / "model.joblib"
        model_blob.download_to_filename(str(local_model_path))
        model = joblib.load(local_model_path)
        logger.info("Downloaded model artifact")

        # Download scaler if exists
        scaler = None
        if manifest["artifacts"].get("scaler"):
            scaler_path = manifest["artifacts"]["scaler"].replace(f"gs://{exchange_bucket}/", "")
            scaler_blob = bucket.blob(scaler_path)
            local_scaler_path = Path(tmpdir) / "scaler.joblib"
            scaler_blob.download_to_filename(str(local_scaler_path))
            scaler = joblib.load(local_scaler_path)
            logger.info("Downloaded scaler artifact")

        # Add import entry to promotion chain
        manifest["promotion_chain"].append({
            "action": "imported",
            "to_workspace": dest_workspace,
            "to_stage": dest_stage,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Run import pipeline
        logger.info("Running import pipeline...")

        from src.pipelines.import_model import import_model_pipeline

        # Run the import pipeline
        import_model_pipeline(
            model_artifact=model,
            scaler_artifact=scaler,
            import_metadata=manifest,
            dest_stage=dest_stage,
        )

        logger.info(f"✅ Model imported to {dest_workspace}")

        # Get the newly created model version
        model_version = client.get_model_version(
            manifest["model_name"],
            ModelStages.PRODUCTION if dest_stage == "production" else ModelStages.STAGING,
        )

        return str(model_version.id)


@click.command()
@click.option(
    "--model",
    type=str,
    required=True,
    help="Name of the model to promote",
)
@click.option(
    "--source-workspace",
    type=click.Choice(list(WORKSPACE_CONFIG.keys())),
    help="Source workspace to export from",
)
@click.option(
    "--dest-workspace",
    type=click.Choice(list(WORKSPACE_CONFIG.keys())),
    help="Destination workspace to import into",
)
@click.option(
    "--source-stage",
    type=click.Choice(["staging", "production", "latest"]),
    default="staging",
    help="Stage to export from source workspace",
)
@click.option(
    "--dest-stage",
    type=click.Choice(["staging", "production"]),
    default="production",
    help="Stage to set in destination workspace",
)
@click.option(
    "--export-only",
    is_flag=True,
    default=False,
    help="Only export, don't import (for manual approval workflows)",
)
@click.option(
    "--import-from",
    type=str,
    default=None,
    help="Import from this GCS path (skips export)",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    default=False,
    help="Skip validation checks (use with caution!)",
)
@click.option(
    "--exchange-bucket",
    type=str,
    default=None,
    help=f"GCS bucket for model exchange (default: {DEFAULT_EXCHANGE_BUCKET})",
)
def promote_cross_workspace(
    model: str,
    source_workspace: Optional[str],
    dest_workspace: Optional[str],
    source_stage: str,
    dest_stage: str,
    export_only: bool,
    import_from: Optional[str],
    skip_validation: bool,
    exchange_bucket: Optional[str],
):
    """Promote model across ZenML workspaces.

    This script handles the export/import workflow for promoting models
    from enterprise-dev-staging to enterprise-production.

    The promotion preserves:
    - Model artifacts (sklearn_classifier, scaler)
    - All metrics (accuracy, precision, recall, etc.)
    - Source lineage links (workspace, version, pipeline run)
    - Promotion history chain

    Examples:

    Full promotion:
        python scripts/promote_cross_workspace.py \\
            --model breast_cancer_classifier \\
            --source-workspace enterprise-dev-staging \\
            --dest-workspace enterprise-production

    Export only (for approval workflows):
        python scripts/promote_cross_workspace.py \\
            --model breast_cancer_classifier \\
            --source-workspace enterprise-dev-staging \\
            --export-only

    Import after approval:
        python scripts/promote_cross_workspace.py \\
            --model breast_cancer_classifier \\
            --dest-workspace enterprise-production \\
            --import-from gs://zenml-core-model-exchange/exports/...
    """
    bucket = exchange_bucket or os.environ.get("MODEL_EXCHANGE_BUCKET", DEFAULT_EXCHANGE_BUCKET)

    logger.info("=" * 60)
    logger.info("Cross-Workspace Model Promotion")
    logger.info("=" * 60)
    logger.info(f"Model: {model}")

    manifest = None

    # Export phase
    if import_from is None:
        if source_workspace is None:
            raise click.UsageError("--source-workspace is required for export")

        logger.info(f"Source: {source_workspace} ({source_stage} stage)")

        # Connect to source workspace
        source_client = connect_to_workspace(source_workspace)

        # Export model
        manifest = export_model(
            client=source_client,
            model_name=model,
            source_stage=source_stage,
            source_workspace=source_workspace,
            exchange_bucket=bucket,
        )

        logger.info(f"Exported to: {manifest['export_path']}")

        if export_only:
            logger.info("\n✅ Export complete. Model ready for import.")
            logger.info(f"Export path: {manifest['export_path']}")
            logger.info("\nTo import, run:")
            logger.info("  python scripts/promote_cross_workspace.py \\")
            logger.info(f"    --model {model} \\")
            logger.info("    --dest-workspace enterprise-production \\")
            logger.info(f"    --import-from {manifest['export_path']}")
            return
    else:
        # Load manifest for import-only workflow
        logger.info(f"Import from: {import_from}")
        gcs_client = storage.Client(project=DEFAULT_GCP_PROJECT)
        gcs_bucket = gcs_client.bucket(bucket)

        manifest_path = import_from.replace(f"gs://{bucket}/", "")
        if not manifest_path.endswith("/manifest.json"):
            manifest_path = f"{manifest_path}/manifest.json"

        manifest_blob = gcs_bucket.blob(manifest_path)
        manifest = json.loads(manifest_blob.download_as_string())

    # Validation phase
    if dest_workspace and not skip_validation:
        logger.info(f"\nValidating for {dest_workspace}...")
        validate_for_promotion(manifest, dest_workspace)
    elif skip_validation:
        logger.warning("⚠️  Skipping validation (--skip-validation)")

    # Import phase
    if dest_workspace:
        logger.info(f"\nDestination: {dest_workspace} ({dest_stage} stage)")

        # Connect to destination workspace
        dest_client = connect_to_workspace(dest_workspace)

        # Import model
        import_path = import_from or manifest["export_path"]
        new_version_id = import_model(
            client=dest_client,
            manifest_path=import_path,
            dest_workspace=dest_workspace,
            dest_stage=dest_stage,
            exchange_bucket=bucket,
        )

        logger.info("\n" + "=" * 60)
        logger.info("✅ PROMOTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Model: {model}")
        logger.info(f"Source: {manifest['source']['workspace']} v{manifest['source']['model_version']}")
        logger.info(f"Destination: {dest_workspace} ({dest_stage} stage)")
        logger.info(f"New Version ID: {new_version_id}")

        # Print audit trail
        logger.info("\n📋 Audit Trail (stored in model metadata):")
        logger.info(f"  - Source workspace: {manifest['source']['workspace']}")
        logger.info(f"  - Source version: {manifest['source']['model_version']}")
        logger.info(f"  - Source pipeline run: {manifest['source'].get('pipeline_run_url', 'N/A')}")
        logger.info(f"  - Metrics preserved: {list(manifest['metrics'].keys())}")


if __name__ == "__main__":
    promote_cross_workspace()
