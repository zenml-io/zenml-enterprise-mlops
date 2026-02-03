#!/bin/bash
# Apache Software License 2.0
#
# Copyright (c) ZenML GmbH 2026. All rights reserved.
#
# Setup script for local development

set -e

echo "🚀 Setting up ZenML Enterprise MLOps Template..."

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Please create and activate a virtual environment first:"
    echo ""
    echo "   # Option 1: Using venv"
    echo "   python -m venv .venv && source .venv/bin/activate"
    echo ""
    echo "   # Option 2: Using uv"
    echo "   uv venv && source .venv/bin/activate"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize ZenML
echo "🔧 Initializing ZenML..."
zenml init

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start ZenML UI (optional): zenml login"
echo "  2. Run training pipeline: python run.py --pipeline training"
echo "  3. Check dashboard: http://localhost:8237"
