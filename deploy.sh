#!/bin/bash

# Google Cloud Deployment Script for Cloud Trading Bot
# This script deploys the bot to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="cloud-trading-bot"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if [ -z "$PROJECT_ID" ]; then
        log_error "GOOGLE_CLOUD_PROJECT environment variable is not set."
        echo "Please set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Setup Google Cloud project
setup_project() {
    log_info "Setting up Google Cloud project..."
    
    # Set the active project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required Google Cloud APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    
    log_info "Project setup complete"
}

# Build and push Docker image
build_and_push() {
    log_info "Building Docker image..."
    
    # Build the image
    docker build -t "$IMAGE_NAME:latest" .
    
    if [ $? -ne 0 ]; then
        log_error "Docker build failed"
        exit 1
    fi
    
    log_info "Pushing image to Google Container Registry..."
    docker push "$IMAGE_NAME:latest"
    
    if [ $? -ne 0 ]; then
        log_error "Docker push failed"
        exit 1
    fi
    
    log_info "Image build and push complete"
}

# Deploy to Cloud Run
deploy_service() {
    log_info "Deploying to Cloud Run..."
    
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME:latest" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10 \
        --timeout 300 \
        --port 8080 \
        --set-env-vars "ENVIRONMENT=production,PYTHONPATH=/app"
    
    if [ $? -ne 0 ]; then
        log_error "Cloud Run deployment failed"
        exit 1
    fi
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    
    log_info "Deployment complete!"
    log_info "Service URL: $SERVICE_URL"
    log_info "Dashboard: $SERVICE_URL/dashboard"
    log_info "Health check: $SERVICE_URL/health"
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    
    # Test health endpoint
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        log_info "Health check passed"
    else
        log_warn "Health check failed - service might still be starting up"
    fi
    
    # Test API status endpoint
    if curl -f -s "$SERVICE_URL/api/system/status" > /dev/null; then
        log_info "API status check passed"
    else
        log_warn "API status check failed - service might still be starting up"
    fi
}

# Main deployment process
main() {
    log_info "Starting Cloud Trading Bot deployment to Google Cloud Run..."
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Service: $SERVICE_NAME"
    
    check_prerequisites
    setup_project
    build_and_push
    deploy_service
    test_deployment
    
    log_info "Deployment completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Visit the dashboard at: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")"
    log_info "2. Configure any API keys as environment variables in Cloud Run console"
    log_info "3. Set up monitoring and alerting in Google Cloud Console"
    log_info ""
    log_info "To update the service, run this script again."
}

# Script options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "setup")
        check_prerequisites
        setup_project
        ;;
    "build")
        check_prerequisites
        build_and_push
        ;;
    "test")
        test_deployment
        ;;
    "url")
        SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)" 2>/dev/null)
        if [ -n "$SERVICE_URL" ]; then
            echo "$SERVICE_URL"
        else
            log_error "Service not found or not deployed"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [deploy|setup|build|test|url]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  setup   - Setup project and enable APIs only"
        echo "  build   - Build and push Docker image only"
        echo "  test    - Test existing deployment"
        echo "  url     - Get service URL"
        exit 1
        ;;
esac