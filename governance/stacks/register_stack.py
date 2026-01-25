#!/usr/bin/env python
"""
Register ZenML Stack Components via Python SDK

Alternative to Terraform for those who prefer code-based registration.
This script registers stack components using the ZenML Python SDK.

Usage:
    python register_stack.py --environment staging --cloud gcp
    python register_stack.py --environment production --cloud aws
"""

import click
from zenml.client import Client
from zenml.enums import StackComponentType
from zenml.logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.option(
    "--environment",
    type=click.Choice(["staging", "production"]),
    required=True,
    help="Environment to register stack for",
)
@click.option(
    "--cloud",
    type=click.Choice(["gcp", "aws", "azure", "local"]),
    required=True,
    help="Cloud provider",
)
@click.option(
    "--project-id",
    type=str,
    help="Cloud project/account ID (required for cloud providers)",
)
@click.option(
    "--region",
    type=str,
    default="us-central1",
    help="Cloud region",
)
@click.option(
    "--artifact-store-path",
    type=str,
    help="Path to artifact store (e.g., gs://bucket, s3://bucket)",
)
@click.option(
    "--container-registry-uri",
    type=str,
    help="Container registry URI",
)
def register_stack(
    environment: str,
    cloud: str,
    project_id: str,
    region: str,
    artifact_store_path: str,
    container_registry_uri: str,
):
    """Register ZenML stack components programmatically."""

    client = Client()
    stack_name = f"{cloud}-{environment}"

    logger.info(f"Registering stack: {stack_name}")

    # Register orchestrator
    if cloud == "local":
        orchestrator_flavor = "local"
        orchestrator_config = {}
        orchestrator_name = "local-orchestrator"
    elif cloud == "gcp":
        orchestrator_flavor = "vertex"
        orchestrator_config = {
            "project": project_id,
            "location": region,
        }
        orchestrator_name = f"vertex-{environment}"
    elif cloud == "aws":
        orchestrator_flavor = "sagemaker"
        orchestrator_config = {
            "execution_role": f"arn:aws:iam::{project_id}:role/zenml-{environment}",
            "region": region,
        }
        orchestrator_name = f"sagemaker-{environment}"
    elif cloud == "azure":
        orchestrator_flavor = "azureml"
        orchestrator_config = {
            "subscription_id": project_id,
            "resource_group": f"zenml-{environment}",
            "workspace_name": f"zenml-{environment}",
        }
        orchestrator_name = f"azureml-{environment}"

    try:
        client.create_stack_component(
            name=orchestrator_name,
            flavor=orchestrator_flavor,
            component_type=StackComponentType.ORCHESTRATOR,
            configuration=orchestrator_config,
        )
        logger.info(f"✅ Registered orchestrator: {orchestrator_name}")
    except Exception as e:
        logger.warning(f"Orchestrator already exists or error: {e}")

    # Register artifact store
    if cloud == "local":
        artifact_flavor = "local"
        artifact_config = {"path": "./.zenml/local_store"}
        artifact_name = "local-artifact-store"
    elif cloud == "gcp":
        artifact_flavor = "gcp"
        artifact_config = {
            "path": artifact_store_path
            or f"gs://{project_id}-zenml-artifacts-{environment}"
        }
        artifact_name = f"gcs-{environment}"
    elif cloud == "aws":
        artifact_flavor = "s3"
        artifact_config = {
            "path": artifact_store_path
            or f"s3://{project_id}-zenml-artifacts-{environment}"
        }
        artifact_name = f"s3-{environment}"
    elif cloud == "azure":
        artifact_flavor = "azure"
        artifact_config = {
            "path": artifact_store_path
            or f"az://{project_id}-zenml-artifacts-{environment}"
        }
        artifact_name = f"azure-{environment}"

    try:
        client.create_stack_component(
            name=artifact_name,
            flavor=artifact_flavor,
            component_type=StackComponentType.ARTIFACT_STORE,
            configuration=artifact_config,
        )
        logger.info(f"✅ Registered artifact store: {artifact_name}")
    except Exception as e:
        logger.warning(f"Artifact store already exists or error: {e}")

    # Register container registry (skip for local)
    if cloud != "local":
        if cloud == "gcp":
            registry_flavor = "gcp"
            registry_config = {
                "uri": container_registry_uri
                or f"{region}-docker.pkg.dev/{project_id}/zenml-{environment}"
            }
            registry_name = f"gcr-{environment}"
        elif cloud == "aws":
            registry_flavor = "aws"
            registry_config = {
                "uri": container_registry_uri
                or f"{project_id}.dkr.ecr.{region}.amazonaws.com/zenml-{environment}"
            }
            registry_name = f"ecr-{environment}"
        elif cloud == "azure":
            registry_flavor = "azure"
            registry_config = {
                "uri": container_registry_uri
                or f"{project_id}.azurecr.io/zenml-{environment}"
            }
            registry_name = f"acr-{environment}"

        try:
            client.create_stack_component(
                name=registry_name,
                flavor=registry_flavor,
                component_type=StackComponentType.CONTAINER_REGISTRY,
                configuration=registry_config,
            )
            logger.info(f"✅ Registered container registry: {registry_name}")
        except Exception as e:
            logger.warning(f"Container registry already exists or error: {e}")

    # Register MLflow experiment tracker
    mlflow_name = f"mlflow-{environment}"
    if environment == "local":
        mlflow_uri = "http://localhost:5000"
    else:
        mlflow_uri = f"https://mlflow-{environment}.your-company.com"

    try:
        client.create_stack_component(
            name=mlflow_name,
            flavor="mlflow",
            component_type=StackComponentType.EXPERIMENT_TRACKER,
            configuration={"tracking_uri": mlflow_uri},
        )
        logger.info(f"✅ Registered experiment tracker: {mlflow_name}")
    except Exception as e:
        logger.warning(f"Experiment tracker already exists or error: {e}")

    # Create the stack
    stack_components = {
        "orchestrator": orchestrator_name,
        "artifact_store": artifact_name,
        "experiment_tracker": mlflow_name,
    }

    if cloud != "local":
        stack_components["container_registry"] = registry_name

    try:
        client.create_stack(
            name=stack_name,
            components=stack_components,
        )
        logger.info(f"✅ Created stack: {stack_name}")
    except Exception as e:
        logger.warning(f"Stack already exists or error: {e}")

    logger.info("")
    logger.info("Stack registration complete!")
    logger.info(f"Set as active: zenml stack set {stack_name}")
    logger.info("")
    logger.info("View stack details:")
    logger.info(f"  zenml stack describe {stack_name}")


if __name__ == "__main__":
    register_stack()
