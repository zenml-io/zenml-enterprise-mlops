"""Workspace switching utilities for the 2-workspace demo.

Provides helpers to switch between enterprise-dev-staging and
enterprise-production workspaces during the interactive demo.
"""

import os
from typing import Optional

# Workspace names
DEV_STAGING = "enterprise-dev-staging"
PRODUCTION = "enterprise-production"

# Environment variable mappings
WORKSPACE_ENV = {
    DEV_STAGING: {
        "url_env": "ZENML_DEV_STAGING_URL",
        "api_key_env": "ZENML_DEV_STAGING_API_KEY",
    },
    PRODUCTION: {
        "url_env": "ZENML_PRODUCTION_URL",
        "api_key_env": "ZENML_PRODUCTION_API_KEY",
    },
}


def verify_workspace_credentials() -> dict[str, bool]:
    """Check which workspace credentials are available.

    Returns:
        Dict mapping workspace name to whether credentials are configured.
    """
    result = {}
    for name, env in WORKSPACE_ENV.items():
        url = os.getenv(env["url_env"])
        api_key = os.getenv(env["api_key_env"])
        result[name] = bool(url and api_key)
    return result


def is_two_workspace_mode() -> bool:
    """Return True if both workspace credentials are available."""
    creds = verify_workspace_credentials()
    return all(creds.values())


def switch_workspace(workspace: str) -> bool:
    """Switch active ZenML workspace via environment variables.

    Sets ZENML_STORE_URL and ZENML_STORE_API_KEY from the workspace-specific
    env vars (e.g. ZENML_DEV_STAGING_URL → ZENML_STORE_URL).

    Args:
        workspace: One of DEV_STAGING or PRODUCTION.

    Returns:
        True if switch succeeded, False if credentials missing.
    """
    if workspace not in WORKSPACE_ENV:
        print(f"  Unknown workspace: {workspace}")
        return False

    env = WORKSPACE_ENV[workspace]
    url = os.getenv(env["url_env"])
    api_key = os.getenv(env["api_key_env"])

    if not url or not api_key:
        print(f"  Missing credentials for {workspace}.")
        print(f"  Set {env['url_env']} and {env['api_key_env']} in .env")
        return False

    os.environ["ZENML_STORE_URL"] = url
    os.environ["ZENML_STORE_API_KEY"] = api_key

    # Reset the Client singleton so it picks up the new env vars
    try:
        from zenml.client import Client
        from zenml.config.global_config import GlobalConfiguration

        Client._reset_instance()
        gc = GlobalConfiguration()
        gc._zen_store = None
    except Exception:
        pass

    return True


def get_current_workspace() -> Optional[str]:
    """Return which workspace is currently active based on ZENML_STORE_URL."""
    current_url = os.getenv("ZENML_STORE_URL", "")
    for name, env in WORKSPACE_ENV.items():
        workspace_url = os.getenv(env["url_env"], "")
        if workspace_url and current_url == workspace_url:
            return name
    return None


def print_workspace_context(workspace: str):
    """Print a workspace context banner."""
    if workspace == DEV_STAGING:
        label = "enterprise-dev-staging"
        icon = "🔧"
    else:
        label = "enterprise-production"
        icon = "🏭"
    print(f"  {icon} Workspace: {label}")
    print()
