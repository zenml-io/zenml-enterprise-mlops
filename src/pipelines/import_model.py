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

"""Import model pipeline for cross-workspace promotion.

This pipeline runs in the destination workspace (enterprise-production) to:
1. Download and register imported model artifacts from GCS
2. Preserve lineage metadata from source workspace
3. Set the appropriate model stage

The pipeline creates proper lineage in the destination workspace while
maintaining audit trail links back to the source workspace.
"""

import os
import tempfile
from pathlib import Path
from typing import Annotated, Optional

import joblib
from google.cloud import storage
from sklearn.base import ClassifierMixin, TransformerMixin
from zenml import ArtifactConfig, Model, get_step_context, log_metadata, pipeline, step
from zenml.enums import ArtifactType, ModelStages
from zenml.logger import get_logger

logger = get_logger(__name__)

# Default GCP project for model exchange bucket
DEFAULT_GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "zenml-core")
DEFAULT_EXCHANGE_BUCKET = os.getenv(
    "MODEL_EXCHANGE_BUCKET", "zenml-core-model-exchange"
)

# Shared Artifact Store Mode
# When True, both workspaces use the same artifact store bucket, so ZenML's fileio works.
USE_SHARED_ARTIFACT_STORE = (
    os.getenv("USE_SHARED_ARTIFACT_STORE", "false").lower() == "true"
)


def _download_from_gcs(gcs_uri: str, local_path: str) -> None:
    """Download a file from GCS.

    Uses ZenML's fileio when using shared artifact store (recommended),
    otherwise uses direct GCS client for separate bucket architecture.

    Args:
        gcs_uri: Full GCS URI (gs://bucket/path)
        local_path: Path to save locally
    """
    if USE_SHARED_ARTIFACT_STORE:
        # Shared artifact store: fileio works because bucket is within bounds
        from zenml.io import fileio

        fileio.copy(gcs_uri, local_path, overwrite=True)
    else:
        # Separate buckets: use direct GCS client to bypass bounds validation
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        parts = gcs_uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

        client = storage.Client(project=DEFAULT_GCP_PROJECT)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(local_path)


@step
def download_and_register_model(
    export_path: str,
    import_metadata: dict,
) -> Annotated[
    ClassifierMixin,
    ArtifactConfig(name="sklearn_classifier", artifact_type=ArtifactType.MODEL),
]:
    """Download and register imported model artifact from GCS.

    Uses direct GCS client to download from the model exchange bucket,
    which is intentionally outside the artifact store bounds.

    Args:
        export_path: GCS path to the export directory
        import_metadata: Metadata from the export manifest

    Returns:
        The registered model artifact
    """
    source = import_metadata.get("source", {})
    logger.info(
        f"Registering model from {source.get('workspace')} v{source.get('model_version')}"
    )

    # Download model directly from GCS (bypasses artifact store bounds)
    model_uri = f"{export_path}/model.joblib"

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _download_from_gcs(model_uri, tmp_path)
        model = joblib.load(tmp_path)
    finally:
        tmp_file = Path(tmp_path)
        if tmp_file.exists():
            tmp_file.unlink()

    logger.info("Downloaded and registered model artifact")
    return model


@step
def download_and_register_scaler(
    export_path: str,
    has_scaler: bool,
) -> Annotated[
    Optional[TransformerMixin],
    ArtifactConfig(name="scaler", artifact_type=ArtifactType.MODEL),
]:
    """Download and register imported scaler artifact if present.

    Uses direct GCS client to download from the model exchange bucket,
    which is intentionally outside the artifact store bounds.

    Args:
        export_path: GCS path to the export directory
        has_scaler: Whether a scaler artifact exists

    Returns:
        The registered scaler artifact or None
    """
    if not has_scaler:
        logger.info("No scaler to import")
        return None

    # Download scaler directly from GCS (bypasses artifact store bounds)
    scaler_uri = f"{export_path}/scaler.joblib"

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _download_from_gcs(scaler_uri, tmp_path)
        scaler = joblib.load(tmp_path)
    finally:
        tmp_file = Path(tmp_path)
        if tmp_file.exists():
            tmp_file.unlink()

    logger.info("Downloaded and registered scaler artifact")
    return scaler


@step
def log_cross_workspace_metadata(
    import_metadata: dict,
    dest_stage: str,
) -> Annotated[dict, "import_record"]:
    """Log comprehensive metadata for audit trail.

    This step preserves all lineage information from the source workspace
    as metadata on the model version in the destination workspace.

    This addresses the enterprise requirement:
    "Can we trace a production prediction back to training data, code commit, and pipeline run?"

    Args:
        import_metadata: Metadata from the export manifest
        dest_stage: Target stage in destination workspace

    Returns:
        Import record summary
    """
    source = import_metadata.get("source", {})
    metrics = import_metadata.get("metrics", {})

    # Log original metrics (for dashboard visibility)
    if metrics:
        log_metadata(metadata=metrics, infer_model=True)
        logger.info(f"Logged {len(metrics)} metrics to model version")

    # Get current pipeline run context for import_run_url
    context = get_step_context()
    pipeline_run = context.pipeline_run

    # Get workspace and project from the promotion_chain (added during import)
    promotion_chain = import_metadata.get("promotion_chain", [])
    workspace_name = None
    if promotion_chain and promotion_chain[-1].get("action") == "imported":
        workspace_name = promotion_chain[-1].get("to_workspace")

    # Get project name from client
    from zenml.client import Client

    client = Client()
    project_name = client.active_project.name

    # Build import pipeline run URL
    # Format: https://cloud.zenml.io/workspaces/{workspace}/projects/{project}/runs/{run_id}?tab=overview
    import_run_url = None
    if workspace_name and project_name:
        import_run_url = (
            f"https://cloud.zenml.io/workspaces/{workspace_name}/"
            f"projects/{project_name}/runs/{pipeline_run.id}?tab=overview"
        )

    # Update the last promotion_chain entry (the import action) with the run URL
    if (
        promotion_chain
        and promotion_chain[-1].get("action") == "imported"
        and import_run_url
    ):
        promotion_chain[-1]["import_run_url"] = import_run_url

    # Log source lineage information
    lineage_metadata = {
        "source": {
            "workspace": source.get("workspace"),
            "model_version": source.get("model_version"),
            "model_version_id": source.get("model_version_id"),
            "model_version_url": source.get("model_version_url"),
            "training_run_url": source.get("training_run_url"),
            "created_at": source.get("created_at"),
        },
        "git_commit": metrics.get("git_commit"),
        "promotion_chain": promotion_chain,
        "imported_at": import_metadata.get("export_timestamp"),
    }

    log_metadata(metadata=lineage_metadata, infer_model=True)
    logger.info("Logged cross-workspace lineage metadata")

    return {
        "status": "imported",
        "source_workspace": source.get("workspace"),
        "source_version": source.get("model_version"),
        "dest_stage": dest_stage,
    }


@step
def set_model_stage(
    import_record: dict,
    dest_stage: str,
) -> Annotated[str, "stage_result"]:
    """Set the model stage in destination workspace.

    Args:
        import_record: Record from metadata logging step
        dest_stage: Target stage to set

    Returns:
        Confirmation message
    """
    context = get_step_context()

    stage_map = {
        "staging": ModelStages.STAGING,
        "production": ModelStages.PRODUCTION,
    }

    if dest_stage in stage_map:
        context.model.set_stage(stage_map[dest_stage], force=True)
        logger.info(f"Model stage set to: {dest_stage}")

    return f"Stage set to {dest_stage}"


@pipeline(
    model=Model(
        name="breast_cancer_classifier",
        description="Imported from cross-workspace promotion",
        tags=["imported", "cross-workspace"],
    ),
    enable_cache=False,  # Always run fresh for imports
)
def import_model_pipeline(
    export_path: str,
    import_metadata: dict,
    has_scaler: bool = True,
    dest_stage: str = "production",
):
    """Import a model from another workspace.

    This pipeline creates a new model version in the destination workspace
    while preserving all lineage and audit trail information from the source.

    The imported model version contains:
    - Registered model and scaler artifacts (downloaded from GCS)
    - Original metrics (accuracy, precision, recall, etc.)
    - Source lineage links (workspace, version, model version URL)
    - Complete promotion chain history

    This addresses enterprise requirements:
    - "How does ZenML maintain audit trails for model training, promotion, and deployment?"
    - "Can we trace a production prediction back to training data, code commit, and pipeline run?"

    Args:
        export_path: GCS path to the export directory
        import_metadata: Metadata from the export manifest
        has_scaler: Whether a scaler artifact exists in the export
        dest_stage: Target stage in destination workspace
    """
    # Download and register artifacts from GCS
    registered_model = download_and_register_model(
        export_path=export_path,
        import_metadata=import_metadata,
    )

    download_and_register_scaler(
        export_path=export_path,
        has_scaler=has_scaler,
    )

    # Log metadata for audit trail
    import_record = log_cross_workspace_metadata(
        import_metadata=import_metadata,
        dest_stage=dest_stage,
    )

    # Set stage (after metadata is logged)
    set_model_stage(
        import_record=import_record,
        dest_stage=dest_stage,
    )

    return registered_model
