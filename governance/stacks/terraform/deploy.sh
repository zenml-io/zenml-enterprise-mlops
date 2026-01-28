#!/bin/bash
# =============================================================================
# ZenML Stack Deployment Script
# =============================================================================
# Usage: ./deploy.sh <action> [stack]
#
# Actions:
#   deploy-all    - Deploy all stacks in order (shared → dev → staging → prod)
#   destroy-all   - Destroy all stacks in reverse order
#   deploy        - Deploy a specific stack
#   destroy       - Destroy a specific stack
#   status        - Show deployment status of all stacks
#
# Stacks:
#   shared        - Shared artifact store bucket
#   development   - Dev stack (local orchestrator)
#   staging       - Staging stack (Vertex AI)
#   production    - Production stack (Vertex AI)
#
# Examples:
#   ./deploy.sh deploy-all
#   ./deploy.sh deploy staging
#   ./deploy.sh destroy production
#   ./deploy.sh status
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Stack directories
SHARED_DIR="$SCRIPT_DIR/shared/gcp"
DEV_DIR="$SCRIPT_DIR/environments/development/gcp"
STAGING_DIR="$SCRIPT_DIR/environments/staging/gcp"
PROD_DIR="$SCRIPT_DIR/environments/production/gcp"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_env() {
    if [ -z "$ZENML_SERVER_URL" ] && [ "$1" != "shared" ]; then
        log_error "ZENML_SERVER_URL not set. Run: source scripts/use-workspace.sh <workspace>"
        exit 1
    fi
}

check_gcp() {
    if ! gcloud auth application-default print-access-token &>/dev/null; then
        log_error "GCP not authenticated. Run: gcloud auth application-default login"
        exit 1
    fi
}

get_stack_dir() {
    case "$1" in
        shared) echo "$SHARED_DIR" ;;
        development|dev) echo "$DEV_DIR" ;;
        staging) echo "$STAGING_DIR" ;;
        production|prod) echo "$PROD_DIR" ;;
        *) log_error "Unknown stack: $1"; exit 1 ;;
    esac
}

get_workspace_for_stack() {
    case "$1" in
        shared) echo "none" ;;
        development|dev|staging) echo "dev-staging" ;;
        production|prod) echo "production" ;;
    esac
}

deploy_stack() {
    local stack="$1"
    local dir=$(get_stack_dir "$stack")
    local workspace=$(get_workspace_for_stack "$stack")

    log_info "Deploying $stack stack..."

    # Save shared bucket if it was captured from shared terraform
    local saved_shared_bucket="$TF_VAR_shared_artifact_bucket"

    # Switch workspace if needed
    if [ "$workspace" != "none" ] && [ "$workspace" != "$CURRENT_WORKSPACE" ]; then
        log_info "Switching to $workspace workspace..."
        source "$REPO_ROOT/scripts/use-workspace.sh" "$workspace"
    fi

    # Restore shared bucket from shared terraform output (takes precedence over .env)
    if [ -n "$saved_shared_bucket" ]; then
        export TF_VAR_shared_artifact_bucket="$saved_shared_bucket"
    fi
    
    cd "$dir"
    
    # Initialize if needed
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
    
    log_success "$stack stack deployed!"
    
    # Capture outputs for shared bucket
    if [ "$stack" = "shared" ]; then
        SHARED_BUCKET=$(terraform output -raw bucket_name 2>/dev/null || true)
        if [ -n "$SHARED_BUCKET" ]; then
            log_info "Shared bucket: $SHARED_BUCKET"
            export TF_VAR_shared_artifact_bucket="$SHARED_BUCKET"
            log_info "Set TF_VAR_shared_artifact_bucket=$SHARED_BUCKET"
        fi
    fi
}

destroy_stack() {
    local stack="$1"
    local dir=$(get_stack_dir "$stack")
    local workspace=$(get_workspace_for_stack "$stack")
    
    log_info "Destroying $stack stack..."
    
    # Switch workspace if needed
    if [ "$workspace" != "none" ] && [ "$workspace" != "$CURRENT_WORKSPACE" ]; then
        log_info "Switching to $workspace workspace..."
        source "$REPO_ROOT/scripts/use-workspace.sh" "$workspace"
    fi
    
    cd "$dir"
    
    # Check if there's state
    if [ ! -f "terraform.tfstate" ] || [ "$(cat terraform.tfstate | grep -c '"type":' || echo 0)" -eq 0 ]; then
        log_warn "$stack stack has no resources to destroy"
        return 0
    fi
    
    # Initialize if needed
    if [ ! -d ".terraform" ]; then
        terraform init
    fi
    
    # Try to destroy, empty bucket if needed
    if ! terraform destroy -auto-approve 2>&1; then
        log_warn "Destroy failed, checking if bucket needs emptying..."
        
        # Extract bucket name and empty it
        local bucket=$(terraform state show 'google_storage_bucket.artifact_store[0]' 2>/dev/null | grep 'name.*=' | head -1 | sed 's/.*= "\(.*\)"/\1/' || true)
        if [ -z "$bucket" ]; then
            bucket=$(terraform state show 'google_storage_bucket.model_exchange' 2>/dev/null | grep 'name.*=' | head -1 | sed 's/.*= "\(.*\)"/\1/' || true)
        fi
        if [ -z "$bucket" ]; then
            bucket=$(terraform state show 'google_storage_bucket.shared_artifact_store' 2>/dev/null | grep 'name.*=' | head -1 | sed 's/.*= "\(.*\)"/\1/' || true)
        fi
        
        if [ -n "$bucket" ]; then
            log_info "Emptying bucket: $bucket"
            gsutil -m rm -r "gs://$bucket/*" 2>/dev/null || true
            terraform destroy -auto-approve
        fi
    fi
    
    log_success "$stack stack destroyed!"
}

show_status() {
    echo ""
    echo "=== ZenML Stack Deployment Status ==="
    echo ""

    for stack in shared development staging production; do
        dir=$(get_stack_dir "$stack")
        state_file="$dir/terraform.tfstate"

        if [ -f "$state_file" ]; then
            count=$(grep '"type":' "$state_file" 2>/dev/null | wc -l | tr -d ' ')
            if [ "$count" -gt 0 ] 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $stack: $count resources deployed"
            else
                echo -e "${YELLOW}○${NC} $stack: initialized but empty"
            fi
        else
            echo -e "${RED}✗${NC} $stack: not deployed"
        fi
    done
    echo ""
}

deploy_all() {
    log_info "Deploying all stacks in order..."
    echo ""

    check_gcp

    # Source dev-staging workspace first to get TF_VAR_bucket_name from .env
    # This ensures shared terraform uses the correct bucket name
    log_info "Loading environment variables from .env..."
    source "$REPO_ROOT/scripts/use-workspace.sh" dev-staging
    echo ""

    # 1. Shared (no ZenML needed, but uses TF_VAR_bucket_name from .env)
    log_info "Step 1/5: Deploying shared artifact store..."
    deploy_stack shared
    echo ""

    # 2. Development (dev-staging workspace)
    log_info "Step 2/5: Deploying development stack..."
    deploy_stack development
    echo ""

    # 3. Staging (dev-staging workspace)
    log_info "Step 3/5: Deploying staging stack..."
    deploy_stack staging
    # Capture staging service account
    cd "$STAGING_DIR"
    STAGING_SA=$(terraform output -raw service_account 2>/dev/null || true)
    echo ""

    # 4. Production (production workspace)
    log_info "Step 4/5: Deploying production stack..."
    deploy_stack production
    # Capture production service account
    cd "$PROD_DIR"
    PROD_SA=$(terraform output -raw service_account 2>/dev/null || true)
    echo ""

    # 5. Grant service accounts access to shared bucket
    if [ -n "$STAGING_SA" ] || [ -n "$PROD_SA" ]; then
        log_info "Step 5/5: Granting service account access to shared bucket..."
        cd "$SHARED_DIR"

        local tf_args=""
        if [ -n "$STAGING_SA" ]; then
            tf_args="$tf_args -var=staging_service_account=$STAGING_SA"
            log_info "Staging SA: $STAGING_SA"
        fi
        if [ -n "$PROD_SA" ]; then
            tf_args="$tf_args -var=production_service_account=$PROD_SA"
            log_info "Production SA: $PROD_SA"
        fi

        terraform apply -auto-approve $tf_args
        log_success "Service account access granted!"
        echo ""
    fi

    log_success "All stacks deployed!"
    show_status
}

destroy_all() {
    log_info "Destroying all stacks in reverse order..."
    echo ""
    
    check_gcp
    
    # Reverse order: production → staging → development → shared
    for stack in production staging development shared; do
        destroy_stack "$stack"
        echo ""
    done
    
    log_success "All stacks destroyed!"
    show_status
}

# Main
case "${1:-}" in
    deploy-all)
        deploy_all
        ;;
    destroy-all)
        destroy_all
        ;;
    deploy)
        if [ -z "$2" ]; then
            log_error "Specify a stack: shared, development, staging, production"
            exit 1
        fi
        check_gcp
        check_env "$2"
        deploy_stack "$2"
        ;;
    destroy)
        if [ -z "$2" ]; then
            log_error "Specify a stack: shared, development, staging, production"
            exit 1
        fi
        check_gcp
        destroy_stack "$2"
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 <action> [stack]"
        echo ""
        echo "Actions:"
        echo "  deploy-all    Deploy all stacks in order"
        echo "  destroy-all   Destroy all stacks in reverse order"
        echo "  deploy        Deploy a specific stack"
        echo "  destroy       Destroy a specific stack"
        echo "  status        Show deployment status"
        echo ""
        echo "Stacks: shared, development, staging, production"
        echo ""
        echo "Examples:"
        echo "  $0 deploy-all"
        echo "  $0 deploy staging"
        echo "  $0 status"
        exit 1
        ;;
esac
