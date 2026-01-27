#!/bin/bash
# Setup ZenML Stacks Script
# Registers all stack configurations for different environments

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if ZenML is installed
if ! command -v zenml &> /dev/null; then
    error "ZenML is not installed. Please install it first:"
    echo "  pip install zenml"
    exit 1
fi

info "ZenML Stack Setup Script"
echo "================================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
STACKS_DIR="$REPO_ROOT/governance/stacks"

# Check if ZenML is initialized
if [ ! -d "$REPO_ROOT/.zen" ]; then
    info "Initializing ZenML repository..."
    cd "$REPO_ROOT"
    zenml init
fi

# Function to register a stack
register_stack() {
    local stack_file=$1
    local stack_name=$(basename "$stack_file" .yaml)

    info "Registering stack: $stack_name"

    if zenml stack describe "$stack_name" &> /dev/null; then
        warn "Stack '$stack_name' already exists. Skipping..."
    else
        # Note: Stack YAML import is not directly supported yet
        # This is a placeholder - you'll need to register components individually
        warn "Stack YAML import not yet supported. Please register manually:"
        echo "  See instructions in: $stack_file"
    fi
}

# Ask user which environment to set up
echo ""
echo "Which environment do you want to set up?"
echo "1) Local development"
echo "2) Staging"
echo "3) Production"
echo "4) All"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        info "Setting up local development stack..."

        # Register local stack components
        info "Registering local orchestrator..."
        zenml orchestrator register local-orchestrator --flavor=local || true

        info "Registering local artifact store..."
        zenml artifact-store register local-artifact-store \
            --flavor=local \
            --path="$REPO_ROOT/.zenml/local_store" || true

        info "Creating local-dev stack..."
        zenml stack register local-dev \
            -o local-orchestrator \
            -a local-artifact-store \
            --set || true

        info "✅ Local development stack setup complete!"
        echo "Set as active with: zenml stack set local-dev"
        ;;

    2)
        info "Setting up staging stack..."
        warn "Staging stack requires cloud credentials and infrastructure."
        echo ""
        echo "Choose your approach:"
        echo ""
        echo "Option 1: Terraform (Recommended for production environments)"
        echo "  cd governance/stacks/terraform/environments/staging/gcp"
        echo "  cp terraform.tfvars.example terraform.tfvars"
        echo "  # Edit terraform.tfvars with your project details"
        echo "  terraform init"
        echo "  terraform apply"
        echo "  # Run output commands to register with ZenML"
        echo ""
        echo "Option 2: Python Script (Quick setup)"
        echo "  python governance/stacks/register_stack.py \\"
        echo "    --environment staging \\"
        echo "    --cloud gcp \\"
        echo "    --project-id your-project-staging \\"
        echo "    --region us-central1"
        echo ""
        echo "Note: You must provision cloud resources (GCS bucket, etc.) first!"
        ;;

    3)
        info "Setting up production stack..."
        error "Production stack setup requires elevated permissions!"
        echo "This should be done by the platform team with approval."
        echo "Please refer to: $STACKS_DIR/production-stack.yaml"
        ;;

    4)
        info "Setting up all stacks..."
        $0  # Re-run script
        ;;

    *)
        error "Invalid choice"
        exit 1
        ;;
esac

echo ""
info "Current stacks:"
zenml stack list

echo ""
info "View stack details with: zenml stack describe <stack-name>"
