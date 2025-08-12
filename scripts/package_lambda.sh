#!/bin/bash

# Simple Lambda Package Creation Script
# This script creates a Lambda deployment package with all required dependencies
# Usage: ./package_lambda.sh [output_file.zip]

set -e

# Function to print error and exit
function error_exit() {
    echo "❌ $1"
    exit 1
}

# Configuration
OUTPUT_FILE="${1:-lambda_deployment.zip}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🚀 Creating Lambda deployment package"
echo "Project root: $PROJECT_ROOT"
echo "Output file: $OUTPUT_FILE"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v pip &> /dev/null; then
    error_exit "pip is not installed. Please install Python and pip first."
fi

if ! command -v zip &> /dev/null; then
    error_exit "zip utility is not installed. Please install it first."
fi

echo "✅ Prerequisites check passed"
echo ""

# Create temporary directory for Lambda package
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

cd "$PROJECT_ROOT"

# Check for required directories
if [ ! -d "backend" ]; then
    error_exit "'backend' directory not found in project root."
fi
if [ ! -d "aws" ]; then
    error_exit "'aws' directory not found in project root."
fi

echo "📦 Copying source files..."

# Copy backend modules
cp -r backend "$TEMP_DIR/"
cp -r aws "$TEMP_DIR/"

# Copy any additional Python files that might be needed
for file in *.py; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
    fi
done

# Handle requirements file
echo "📋 Processing requirements..."
if [ -f "requirements_Version9.txt" ]; then
    echo "Found requirements_Version9.txt, creating optimized Lambda requirements..."
    # Create Lambda-specific requirements (exclude non-Lambda packages)
    cat > "$TEMP_DIR/requirements.txt" << 'EOF'
boto3
yfinance
requests
pandas
numpy
EOF
    echo "Created optimized requirements for Lambda deployment"
elif [ -f "requirements.txt" ]; then
    echo "Using requirements.txt"
    cp requirements.txt "$TEMP_DIR/requirements.txt"
else
    echo "⚠️  No requirements file found, creating basic one"
    cat > "$TEMP_DIR/requirements.txt" << 'EOF'
boto3
yfinance
requests
pandas
numpy
EOF
fi

# Install dependencies
echo "⬇️  Installing Python dependencies..."
cd "$TEMP_DIR"

# Create virtual environment for clean dependency installation
python -m venv temp_venv
source temp_venv/bin/activate

# Install dependencies to current directory with timeout and retries
pip install --upgrade pip
if ! pip install -r requirements.txt -t . --timeout 300 --retries 3; then
    echo "⚠️  Failed to install all dependencies. Creating package with available files..."
    echo "   Some dependencies may be missing. Verify Lambda function works correctly."
fi

# Remove virtual environment
deactivate
rm -rf temp_venv

# Remove unnecessary files to reduce package size
echo "🧹 Removing unnecessary files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove test files and documentation to reduce size
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.md" -delete 2>/dev/null || true
find . -name "*.rst" -delete 2>/dev/null || true
find . -name "LICENSE*" -delete 2>/dev/null || true

# Create zip file
echo "🗜️  Creating ZIP package..."
zip -r "$OUTPUT_FILE" . -x "*.pyc" "*/__pycache__/*" "temp_venv/*"

# Move zip to project root
mv "$OUTPUT_FILE" "$PROJECT_ROOT/"

cd "$PROJECT_ROOT"

# Get package size
PACKAGE_SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE" 2>/dev/null || echo "unknown")
PACKAGE_SIZE_MB=$((PACKAGE_SIZE / 1024 / 1024))

echo ""
echo "✅ Lambda deployment package created successfully!"
echo "📦 Package: $OUTPUT_FILE"
echo "📏 Size: ${PACKAGE_SIZE_MB}MB"
echo ""

# Validate package size
if [ "$PACKAGE_SIZE_MB" -gt 250 ]; then
    echo "⚠️  WARNING: Package size (${PACKAGE_SIZE_MB}MB) exceeds AWS Lambda limit of 250MB for S3 deployment"
    echo "   Consider removing unnecessary dependencies or files"
elif [ "$PACKAGE_SIZE_MB" -gt 70 ]; then
    echo "ℹ️  Package size (${PACKAGE_SIZE_MB}MB) requires S3-based deployment (>70MB)"
    echo "   Direct upload to Lambda is not supported for this size"
else
    echo "ℹ️  Package size (${PACKAGE_SIZE_MB}MB) supports both direct upload and S3-based deployment"
fi

echo ""
echo "📝 Next steps:"
echo "1. Upload to S3: ./scripts/upload_lambda_to_s3.sh $OUTPUT_FILE <bucket-name> <s3-key>"
echo "2. Deploy infrastructure: ./scripts/deploy.sh"
echo "3. Or use the full deployment: ./scripts/deploy.sh"