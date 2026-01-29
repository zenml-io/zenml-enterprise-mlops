#!/bin/bash
# =============================================================================
# ZenML Stack Deployment Script
# =============================================================================
# Usage: ./deploy.sh <action> [stack]
#
# Actions:
#   deploy-all    - Deploy all GCP stacks (shared → dev → staging → prod)
#   destroy-all   - Destroy all stacks in reverse order
#   deploy        - Deploy a specific stack
#   destroy       - Destroy a specific stack
#   status        - Show deployment status
#
# Available Stacks:
#   shared              - Shared GCS artifact store bucket
#   development         - Dev stack (local orchestrator, GCP)
#   staging             - Staging stack (Vertex AI, GCP)
#   staging-aws         - Staging stack (EKS, AWS) - NEW
#   production          - Production stack (Vertex AI, GCP)
#   production-airflow  - Production stack (Cloud Composer, GCP) - NEW
#
# Examples:
#   ./deploy.sh deploy-all              # Deploy all GCP stacks
#   ./deploy.sh deploy staging-aws      # Deploy AWS staging
#   ./deploy.sh deploy production-airflow  # Deploy Cloud Composer stack
#   ./deploy.sh status
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# =============================================================================
# Auto-source .env if it exists
# =============================================================================
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${CYAN}==== $1 ====${NC}"; }

# =============================================================================
# Stack directory mapping
# =============================================================================

get_stack_dir() {
    case "$1" in
        shared)
            echo "$SCRIPT_DIR/shared/gcp"
            ;;
        development|dev)
            echo "$SCRIPT_DIR/environments/development/gcp"
            ;;
        staging)
            echo "$SCRIPT_DIR/environments/staging/gcp"
            ;;
        staging-aws)
            echo "$SCRIPT_DIR/environments/staging/aws"
            ;;
        production|prod)
            echo "$SCRIPT_DIR/environments/production/gcp"
            ;;
        production-airflow|prod-airflow)
            echo "$SCRIPT_DIR/environments/production/gcp-airflow"
            ;;
        *)
            log_error "Unknown stack: $1"
            log_info "Available stacks: shared, development, staging, staging-aws, production, production-airflow"
            exit 1
            ;;
    esac
}

get_cloud_provider() {
    case "$1" in
        staging-aws)
            echo "aws"
            ;;
        *)
            echo "gcp"
            ;;
    esac
}

get_workspace() {
    case "$1" in
        shared)
            echo "none"
            ;;
        development|dev|staging|staging-aws)
            echo "dev-staging"
            ;;
        production|prod|production-airflow|prod-airflow)
            echo "production"
            ;;
    esac
}

# =============================================================================
# Auth checks
# =============================================================================

check_gcp() {
    if ! gcloud auth application-default print-access-token &>/dev/null; then
        log_error "GCP not authenticated. Run: gcloud auth application-default login"
        exit 1
    fi
}

check_aws() {
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS not authenticated. Run: aws configure"
        exit 1
    fi
}

setup_workspace_env() {
    local workspace="$1"

    case "$workspace" in
        dev-staging)
            if [ -n "$ZENML_DEV_STAGING_URL" ]; then
                export ZENML_SERVER_URL="$ZENML_DEV_STAGING_URL"
                export ZENML_API_KEY="$ZENML_DEV_STAGING_API_KEY"
                export TF_VAR_zenml_server_url="$ZENML_DEV_STAGING_URL"
                export TF_VAR_zenml_api_key="$ZENML_DEV_STAGING_API_KEY"
                export CURRENT_WORKSPACE="enterprise-dev-staging"
                log_info "Using dev-staging workspace"
                return 0
            fi
            ;;
        production)
            if [ -n "$ZENML_PRODUCTION_URL" ]; then
                export ZENML_SERVER_URL="$ZENML_PRODUCTION_URL"
                export ZENML_API_KEY="$ZENML_PRODUCTION_API_KEY"
                export TF_VAR_zenml_server_url="$ZENML_PRODUCTION_URL"
                export TF_VAR_zenml_api_key="$ZENML_PRODUCTION_API_KEY"
                export CURRENT_WORKSPACE="enterprise-production"
                log_info "Using production workspace"
                return 0
            fi
            ;;
    esac

    # Fall back to checking if already set
    if [ -z "$ZENML_SERVER_URL" ]; then
        log_error "ZenML credentials not found in .env"
        log_info "Ensure .env has ZENML_DEV_STAGING_URL or ZENML_PRODUCTION_URL"
        exit 1
    fi
}

# =============================================================================
# Deploy a single stack
# =============================================================================

deploy_stack() {
    local stack="$1"
    local dir=$(get_stack_dir "$stack")
    local cloud=$(get_cloud_provider "$stack")
    local workspace=$(get_workspace "$stack")

    log_header "Deploying: $stack"
    log_info "Directory: $dir"
    log_info "Cloud: $cloud"

    # Check cloud auth
    if [ "$cloud" = "gcp" ]; then
        check_gcp
    else
        check_aws
    fi

    # Setup workspace environment
    if [ "$workspace" != "none" ]; then
        setup_workspace_env "$workspace"
    fi

    cd "$dir"

    # Check for tfvars
    if [ ! -f "terraform.tfvars" ]; then
        if [ -f "terraform.tfvars.example" ]; then
            log_warn "terraform.tfvars not found."
            log_info "Create it with: cp terraform.tfvars.example terraform.tfvars"
            log_info "Then edit with your values."
            exit 1
        fi
    fi

    # Init if needed
    if [ ! -d ".terraform" ]; then
        log_info "Initializing Terraform..."
        terraform init
    fi

    # Plan and apply
    log_info "Planning..."
    terraform plan -out=tfplan

    log_info "Applying..."
    terraform apply tfplan
    rm -f tfplan

    log_success "$stack deployed!"

    # Show post-deployment instructions
    echo ""
    terraform output post_deployment_instructions 2>/dev/null || true
}

# =============================================================================
# Destroy a single stack
# =============================================================================

destroy_stack() {
    local stack="$1"
    local dir=$(get_stack_dir "$stack")
    local cloud=$(get_cloud_provider "$stack")
    local workspace=$(get_workspace "$stack")

    log_header "Destroying: $stack"

    # Check cloud auth
    if [ "$cloud" = "gcp" ]; then
        check_gcp
    else
        check_aws
    fi

    # Setup workspace environment
    if [ "$workspace" != "none" ]; then
        setup_workspace_env "$workspace" 2>/dev/null || true
    fi

    cd "$dir"

    # Check state exists
    if [ ! -f "terraform.tfstate" ]; then
        log_warn "$stack: No state file found, skipping"
        return 0
    fi

    if [ "$(grep -c '"type":' terraform.tfstate 2>/dev/null || echo 0)" -eq 0 ]; then
        log_warn "$stack: Empty state, skipping"
        return 0
    fi

    # Init if needed
    if [ ! -d ".terraform" ]; then
        terraform init
    fi

    # Destroy
    if ! terraform destroy -auto-approve 2>&1; then
        log_warn "Destroy may have failed, check manually"
    fi

    log_success "$stack destroyed!"
}

# =============================================================================
# Status
# =============================================================================

show_status() {
    echo ""
    log_header "ZenML Stack Deployment Status"
    echo ""

    echo -e "${CYAN}GCP Stacks:${NC}"
    for stack in shared development staging production production-airflow; do
        local dir=$(get_stack_dir "$stack" 2>/dev/null)
        if [ ! -d "$dir" ]; then
            continue
        fi

        local state_file="$dir/terraform.tfstate"
        if [ -f "$state_file" ]; then
            local count=$(grep -c '"type":' "$state_file" 2>/dev/null || echo 0)
            if [ "$count" -gt 0 ]; then
                echo -e "  ${GREEN}✓${NC} $stack: $count resources"
            else
                echo -e "  ${YELLOW}○${NC} $stack: initialized, empty"
            fi
        else
            echo -e "  ${RED}✗${NC} $stack: not deployed"
        fi
    done

    echo ""
    echo -e "${CYAN}AWS Stacks:${NC}"
    for stack in staging-aws; do
        local dir=$(get_stack_dir "$stack" 2>/dev/null)
        if [ ! -d "$dir" ]; then
            continue
        fi

        local state_file="$dir/terraform.tfstate"
        if [ -f "$state_file" ]; then
            local count=$(grep -c '"type":' "$state_file" 2>/dev/null || echo 0)
            if [ "$count" -gt 0 ]; then
                echo -e "  ${GREEN}✓${NC} $stack: $count resources"
            else
                echo -e "  ${YELLOW}○${NC} $stack: initialized, empty"
            fi
        else
            echo -e "  ${RED}✗${NC} $stack: not deployed"
        fi
    done
    echo ""
}

# =============================================================================
# Deploy all (GCP only)
# =============================================================================

deploy_all() {
    log_header "Deploying all GCP stacks"
    echo ""

    check_gcp

    # Setup environment
    setup_workspace_env "dev-staging"
    echo ""

    for stack in shared development staging production; do
        deploy_stack "$stack"
        echo ""
    done

    log_success "All GCP stacks deployed!"
    show_status
}

# =============================================================================
# Destroy all
# =============================================================================

destroy_all() {
    log_header "Destroying all stacks"
    echo ""

    for stack in production-airflow production staging staging-aws development shared; do
        local dir=$(get_stack_dir "$stack" 2>/dev/null || true)
        if [ -n "$dir" ] && [ -f "$dir/terraform.tfstate" ]; then
            destroy_stack "$stack" || true
            echo ""
        fi
    done

    log_success "All stacks destroyed!"
    show_status
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    echo "Usage: $0 <action> [stack]"
    echo ""
    echo "Actions:"
    echo "  deploy-all    Deploy all GCP stacks (shared → dev → staging → prod)"
    echo "  destroy-all   Destroy all stacks"
    echo "  deploy        Deploy a specific stack"
    echo "  destroy       Destroy a specific stack"
    echo "  status        Show deployment status"
    echo ""
    echo "Available Stacks:"
    echo "  shared              Shared GCS artifact store"
    echo "  development         Dev stack (local, GCP)"
    echo "  staging             Staging stack (Vertex AI, GCP)"
    echo "  staging-aws         Staging stack (EKS, AWS)"
    echo "  production          Production stack (Vertex AI, GCP)"
    echo "  production-airflow  Production stack (Cloud Composer, GCP)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy-all"
    echo "  $0 deploy staging-aws"
    echo "  $0 deploy production-airflow"
    echo "  $0 status"
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    deploy-all)
        deploy_all
        ;;
    destroy-all)
        destroy_all
        ;;
    deploy)
        if [ -z "$2" ]; then
            log_error "Specify a stack. Run: $0 --help"
            exit 1
        fi
        deploy_stack "$2"
        ;;
    destroy)
        if [ -z "$2" ]; then
            log_error "Specify a stack. Run: $0 --help"
            exit 1
        fi
        destroy_stack "$2"
        ;;
    status)
        show_status
        ;;
    --help|-h|help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
