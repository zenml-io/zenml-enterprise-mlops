#!/bin/bash
# =============================================================================
# Workspace Switcher for ZenML Enterprise MLOps
# =============================================================================
# Usage: source scripts/use-workspace.sh <workspace>
#
# Workspaces:
#   dev-staging  - For dev-stack and staging-stack (enterprise-dev-staging)
#   production   - For gcp-stack (enterprise-production)
#
# This script loads credentials from .env and exports them for:
#   - Terraform (TF_VAR_* variables)
#   - ZenML CLI (ZENML_* variables)
#   - Python scripts
# =============================================================================

set -e

# Get the repo root - works in both bash and zsh
# Try git first, then fall back to script path detection
if git rev-parse --show-toplevel &>/dev/null; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
else
    # Fallback: try BASH_SOURCE, then $0
    if [ -n "${BASH_SOURCE[0]}" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    else
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    fi
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"
fi

# Check for workspace argument
if [ -z "$1" ]; then
    echo "Usage: source scripts/use-workspace.sh <workspace>"
    echo ""
    echo "Available workspaces:"
    echo "  dev-staging  - For dev-stack and staging-stack"
    echo "  production   - For gcp-stack"
    return 1 2>/dev/null || exit 1
fi

WORKSPACE="$1"

# Load .env file if it exists
ENV_FILE="$REPO_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Looking in: $REPO_ROOT"
    echo "Copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    return 1 2>/dev/null || exit 1
fi

# Source the .env file (handles comments and empty lines)
set -a
source "$ENV_FILE"
set +a

# Set workspace-specific variables
# Supports both naming conventions:
#   ZENML_DEV_STAGING_URL or DEV_STAGING_ZENML_SERVER_URL
#   ZENML_PRODUCTION_URL or PRODUCTION_ZENML_SERVER_URL
case "$WORKSPACE" in
    dev-staging|dev|staging)
        _url="${ZENML_DEV_STAGING_URL:-$DEV_STAGING_ZENML_SERVER_URL}"
        _key="${ZENML_DEV_STAGING_API_KEY:-$DEV_STAGING_ZENML_API_KEY}"
        export ZENML_SERVER_URL="$_url"
        export ZENML_API_KEY="$_key"
        export TF_VAR_zenml_server_url="$_url"
        export TF_VAR_zenml_api_key="$_key"
        export CURRENT_WORKSPACE="enterprise-dev-staging"
        echo "✓ Switched to dev-staging workspace (enterprise-dev-staging)"
        echo "  Stacks: dev-stack, staging-stack"
        ;;
    production|prod)
        _url="${ZENML_PRODUCTION_URL:-$PRODUCTION_ZENML_SERVER_URL}"
        _key="${ZENML_PRODUCTION_API_KEY:-$PRODUCTION_ZENML_API_KEY}"
        export ZENML_SERVER_URL="$_url"
        export ZENML_API_KEY="$_key"
        export TF_VAR_zenml_server_url="$_url"
        export TF_VAR_zenml_api_key="$_key"
        export CURRENT_WORKSPACE="enterprise-production"
        echo "✓ Switched to production workspace (enterprise-production)"
        echo "  Stacks: gcp-stack"
        ;;
    *)
        echo "Error: Unknown workspace '$WORKSPACE'"
        echo "Available: dev-staging, production"
        return 1 2>/dev/null || exit 1
        ;;
esac

# Export GCP variables for Terraform
export TF_VAR_project_id="${GCP_PROJECT_ID:-zenml-core}"
export TF_VAR_region="${GCP_REGION:-us-central1}"

# Export ZenML project and stack names
export ZENML_PROJECT="${ZENML_PROJECT:-cancer-detection}"
export ZENML_DEV_STACK="${ZENML_DEV_STACK:-dev-stack}"
export ZENML_STAGING_STACK="${ZENML_STAGING_STACK:-staging-stack}"
export ZENML_PRODUCTION_STACK="${ZENML_PRODUCTION_STACK:-gcp-stack}"

# Export shared bucket if set
if [ -n "$SHARED_ARTIFACT_BUCKET" ]; then
    export TF_VAR_shared_artifact_bucket="$SHARED_ARTIFACT_BUCKET"
    echo "  Shared bucket: $SHARED_ARTIFACT_BUCKET"
fi

# Export model exchange bucket for shared terraform
if [ -n "$MODEL_EXCHANGE_BUCKET" ]; then
    export TF_VAR_bucket_name="$MODEL_EXCHANGE_BUCKET"
fi

echo ""
echo "Environment variables exported:"
echo "  ZENML_SERVER_URL=$ZENML_SERVER_URL"
echo "  ZENML_PROJECT=$ZENML_PROJECT"
echo "  TF_VAR_project_id=$TF_VAR_project_id"
echo "  TF_VAR_region=$TF_VAR_region"
