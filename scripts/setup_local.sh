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
    echo "   Please activate your virtual environment first:"
    echo "   source /Users/htahir1/Envs/zenml_enterprise_mlops/bin/activate"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize ZenML
echo "🔧 Initializing ZenML..."
zenml init

# Register local MLflow experiment tracker
echo "📊 Registering MLflow experiment tracker..."
zenml experiment-tracker register mlflow_local --flavor=mlflow || echo "MLflow tracker already registered"

# Update default stack with MLflow
echo "🏗️  Updating stack with MLflow..."
zenml stack update default -e mlflow_local || echo "Stack already configured"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start ZenML UI (optional): zenml up"
echo "  2. Run training pipeline: python run.py --pipeline training"
echo "  3. Check dashboard: http://localhost:8237"
