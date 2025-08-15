# Google Cloud Deployment Guide

## Quick Deployment

### 1. Prerequisites
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
gcloud auth login

# Set up project
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

### 2. Deploy
```bash
./deploy.sh
```

That's it! Your dashboard will be live at the URL returned by the script.

## Manual Deployment

### Enable APIs
```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com
```

### Build and Deploy
```bash
# Build image
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/cloud-trading-bot .

# Push to registry
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/cloud-trading-bot

# Deploy to Cloud Run
gcloud run deploy cloud-trading-bot \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/cloud-trading-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1
```

## Configuration

### Environment Variables
Set these in Cloud Run console:
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `IEX_CLOUD_API_KEY`: Your IEX Cloud API key
- `TRADING_ENABLED`: `false` for paper trading, `true` for live trading
- `ENVIRONMENT`: `production`

### API Keys
- **Alpha Vantage**: Free 500 calls/day at https://www.alphavantage.co/support/#api-key
- **IEX Cloud**: Free 500k calls/month at https://iexcloud.io/cloud-login/

## Monitoring

### Cloud Console
- **Logs**: https://console.cloud.google.com/logs
- **Metrics**: https://console.cloud.google.com/run
- **Error Reporting**: https://console.cloud.google.com/errors

### Health Checks
- Health: `https://your-service-url/health`
- Status: `https://your-service-url/api/system/status`

## Costs

Typical monthly costs:
- **Cloud Run**: $5-15 (pay per use)
- **Container Registry**: $1-5 (storage)
- **Total**: $10-20/month for most use cases

## Scaling

Cloud Run automatically scales:
- **0 to millions** of requests
- **Pay only for usage**
- **Sub-second cold starts**

## Troubleshooting

### Check deployment
```bash
gcloud run services describe cloud-trading-bot --region=us-central1
```

### View logs
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Common issues
1. **Build fails**: Check Dockerfile and dependencies
2. **Service won't start**: Check environment variables
3. **API errors**: Verify API keys are set correctly