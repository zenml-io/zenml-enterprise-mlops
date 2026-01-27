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

from typing import Annotated, Optional

import joblib
from sklearn.base import ClassifierMixin, TransformerMixin
from zenml import ArtifactConfig, Model, get_step_context, log_metadata, pipeline, step
from zenml.enums import ArtifactType, ModelStages
from zenml.logger import get_logger

logger = get_logger(__name__)


@step
def download_and_register_model(
    export_path: str,
    import_metadata: dict,
) -> Annotated[
    ClassifierMixin,
    ArtifactConfig(name="sklearn_classifier", artifact_type=ArtifactType.MODEL),
]:
    """Download and register imported model artifact from GCS.

    Args:
        export_path: GCS path to the export directory
        import_metadata: Metadata from the export manifest

    Returns:
        The registered model artifact
    """
    import tempfile
    from pathlib import Path

    from google.cloud import storage

    source = import_metadata.get("source", {})
    logger.info(
        f"Registering model from {source.get('workspace')} v{source.get('model_version')}"
    )

    # Download model from GCS
    bucket_name = export_path.replace("gs://", "").split("/")[0]
    blob_path = "/".join(export_path.replace("gs://", "").split("/")[1:]) + "/model.joblib"

    gcs_client = storage.Client()
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "model.joblib"
        blob.download_to_filename(str(local_path))
        model = joblib.load(local_path)

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

    Args:
        export_path: GCS path to the export directory
        has_scaler: Whether a scaler artifact exists

    Returns:
        The registered scaler artifact or None
    """
    if not has_scaler:
        logger.info("No scaler to import")
        return None

    import tempfile
    from pathlib import Path

    from google.cloud import storage

    bucket_name = export_path.replace("gs://", "").split("/")[0]
    blob_path = "/".join(export_path.replace("gs://", "").split("/")[1:]) + "/scaler.joblib"

    gcs_client = storage.Client()
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "scaler.joblib"
        blob.download_to_filename(str(local_path))
        scaler = joblib.load(local_path)

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

    # Log source lineage information
    lineage_metadata = {
        "source": {
            "workspace": source.get("workspace"),
            "model_version": source.get("model_version"),
            "model_version_id": source.get("model_version_id"),
            "pipeline_run_url": source.get("pipeline_run_url"),
            "created_at": source.get("created_at"),
        },
        "git_commit": metrics.get("git_commit"),
        "promotion_chain": import_metadata.get("promotion_chain", []),
        "imported_at": import_metadata.get("export_timestamp"),
    }

    log_metadata(metadata={"cross_workspace_lineage": lineage_metadata}, infer_model=True)
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
    - Source lineage links (workspace, version, pipeline run URL)
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
