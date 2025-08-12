#!/bin/bash

# Test Lambda Package Creation Script (without pip install)
# Usage: ./test_package_lambda.sh [output_file.zip]

set -e

OUTPUT_FILE="${1:-test_lambda.zip}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🧪 Testing Lambda package creation (without dependencies)"
echo "Project root: $PROJECT_ROOT"
echo "Output file: $OUTPUT_FILE"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temp dir: $TEMP_DIR"

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

cd "$PROJECT_ROOT"

# Copy source files
echo "📦 Copying source files..."
cp -r backend "$TEMP_DIR/"
cp -r aws "$TEMP_DIR/"

# Copy any additional Python files
for file in *.py; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
    fi
done

# Create basic requirements file
cat > "$TEMP_DIR/requirements.txt" << 'EOF'
# Lambda requirements (installed in Lambda runtime)
boto3
# Additional requirements would be installed here
yfinance
requests
pandas
numpy
EOF

cd "$TEMP_DIR"

# Clean up unnecessary files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Create zip
echo "🗜️  Creating ZIP package..."
zip -r "$OUTPUT_FILE" . -x "*.pyc" "*/__pycache__/*"

# Move to project root
mv "$OUTPUT_FILE" "$PROJECT_ROOT/"

cd "$PROJECT_ROOT"

# Get size
PACKAGE_SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE" 2>/dev/null || echo "unknown")
PACKAGE_SIZE_KB=$((PACKAGE_SIZE / 1024))

echo ""
echo "✅ Test package created successfully!"
echo "📦 Package: $OUTPUT_FILE"
echo "📏 Size: ${PACKAGE_SIZE_KB}KB"
echo ""
echo "Package contents:"
unzip -l "$OUTPUT_FILE" | head -20