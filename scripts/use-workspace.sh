#!/bin/bash
# Switch to a workspace by setting the right environment variables
#
# Usage: source scripts/use-workspace.sh dev-staging
#        source scripts/use-workspace.sh production
#
# This sets all the env vars that ZenML Python client and Terraform need.

if [ -z "$1" ]; then
    echo "Usage: source scripts/use-workspace.sh <workspace>"
    echo "  Workspaces: dev-staging, production"
    return 1 2>/dev/null || exit 1
fi

# Load .env if not already loaded
if [ -z "$ZENML_DEV_STAGING_URL" ]; then
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    elif [ -f ../.env ]; then
        export $(grep -v '^#' ../.env | xargs)
    else
        echo "Error: .env file not found"
        return 1 2>/dev/null || exit 1
    fi
fi

case "$1" in
    dev-staging|dev|staging)
        # Python client
        export ZENML_STORE_URL="$ZENML_DEV_STAGING_URL"
        export ZENML_STORE_API_KEY="$ZENML_DEV_STAGING_API_KEY"
        # ZenML Terraform provider
        export ZENML_SERVER_URL="$ZENML_DEV_STAGING_URL"
        export ZENML_API_KEY="$ZENML_DEV_STAGING_API_KEY"
        # Terraform variables (for variable resolution)
        export TF_VAR_zenml_server_url="$ZENML_DEV_STAGING_URL"
        export TF_VAR_zenml_api_key="$ZENML_DEV_STAGING_API_KEY"
        echo "✓ Switched to DEV-STAGING workspace: $ZENML_STORE_URL"
        ;;
    production|prod)
        # Python client
        export ZENML_STORE_URL="$ZENML_PRODUCTION_URL"
        export ZENML_STORE_API_KEY="$ZENML_PRODUCTION_API_KEY"
        # ZenML Terraform provider
        export ZENML_SERVER_URL="$ZENML_PRODUCTION_URL"
        export ZENML_API_KEY="$ZENML_PRODUCTION_API_KEY"
        # Terraform variables (for variable resolution)
        export TF_VAR_zenml_server_url="$ZENML_PRODUCTION_URL"
        export TF_VAR_zenml_api_key="$ZENML_PRODUCTION_API_KEY"
        echo "✓ Switched to PRODUCTION workspace: $ZENML_STORE_URL"
        ;;
    *)
        echo "Unknown workspace: $1"
        echo "  Workspaces: dev-staging, production"
        return 1 2>/dev/null || exit 1
        ;;
esac

echo "  Python client:      ZENML_STORE_URL, ZENML_STORE_API_KEY"
echo "  ZenML TF provider:  ZENML_SERVER_URL, ZENML_API_KEY"
echo "  Terraform vars:     TF_VAR_zenml_server_url, TF_VAR_zenml_api_key"
