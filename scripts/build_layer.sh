#!/bin/bash
# Script to create Lambda layer for heavy dependencies

set -e

echo "🏗️  Building Lambda layer for heavy dependencies..."

# Create temporary directory for layer
rm -rf /tmp/lambda_layer
mkdir -p /tmp/lambda_layer/python

# Copy layer requirements
cd "$(dirname "$0")/.."
cp aws/layer_requirements.txt /tmp/lambda_layer/

# Install dependencies in the layer structure
cd /tmp/lambda_layer
pip install -r layer_requirements.txt -t python/ --quiet

# Create zip file
zip -r lambda_layer.zip python/ -x "*.pyc" "*/__pycache__/*" "*.git*" "*.DS_Store"

# Get layer size
LAYER_SIZE=$(du -sh lambda_layer.zip | cut -f1)
echo "Lambda layer size: $LAYER_SIZE"

# Move to terraform directory
mv lambda_layer.zip "$(dirname "$0")/../infrastructure/terraform/"

echo "✅ Lambda layer created successfully"