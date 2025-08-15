# Cloud Trading Bot - Modern Cloud Deployment Guide

This guide covers deploying the Cloud Trading Bot to modern, developer-friendly cloud platforms using Google Cloud Run for the backend and Vercel for the frontend.

## 🚀 Quick Start

### Prerequisites

1. **GitHub Account** - For code repository and CI/CD
2. **Google Cloud Account** - For backend deployment
3. **Vercel Account** - For frontend deployment
4. **Local Development Environment**:
   - Python 3.11+
   - Node.js 18+
   - Docker (for local testing)

### 1. Fork and Clone Repository

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Cloud-Trading.git
cd Cloud-Trading
```

### 2. Set Up Google Cloud Project

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login and create a new project
gcloud auth login
gcloud projects create YOUR_PROJECT_ID --name="Cloud Trading Bot"
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Set Up Vercel

1. Go to [vercel.com](https://vercel.com) and sign up with GitHub
2. Import your forked repository
3. Note your Organization ID and Project ID from the dashboard

### 4. Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and Variables > Actions and add:

**Google Cloud Secrets:**
```
GCP_PROJECT_ID=your-gcp-project-id
GCP_SERVICE_ACCOUNT_KEY=<service-account-json-key>
```

**Vercel Secrets:**
```
VERCEL_TOKEN=<your-vercel-token>
VERCEL_ORG_ID=<your-vercel-org-id>
VERCEL_PROJECT_ID=<your-vercel-project-id>
```

### 5. Deploy

Push to the main branch to trigger automatic deployment:

```bash
git add .
git commit -m "Initial deployment setup"
git push origin main
```

## 📋 Detailed Setup Instructions

### Google Cloud Setup

#### 1. Create Service Account

```bash
# Create a service account for deployment
gcloud iam service-accounts create cloud-trading-bot \
    --display-name="Cloud Trading Bot Deployment"

# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Cloud Trading Bot Deployment" \
    --format="value(email)")

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Create and download the key
gcloud iam service-accounts keys create ~/key.json \
    --iam-account=$SA_EMAIL

# Copy the content of ~/key.json for the GCP_SERVICE_ACCOUNT_KEY secret
cat ~/key.json
```

#### 2. Test Local Deployment

```bash
# Set up authentication
export GOOGLE_APPLICATION_CREDENTIALS=~/key.json
gcloud auth activate-service-account --key-file=~/key.json

# Build and test Docker image locally
docker build -t cloud-trading-bot .
docker run -p 8080:8080 -e PORT=8080 cloud-trading-bot

# Test the API
curl http://localhost:8080/health
curl http://localhost:8080/api/status
```

### Vercel Setup

#### 1. Get Vercel Token

```bash
# Install Vercel CLI
npm install -g vercel

# Login and get token
vercel login
vercel whoami
```

Go to [vercel.com/account/tokens](https://vercel.com/account/tokens) to create a new token.

#### 2. Import Project

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Import Project"
3. Select your GitHub repository
4. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

#### 3. Configure Environment Variables

In Vercel dashboard, go to your project > Settings > Environment Variables:

```
REACT_APP_API_URL=https://cloud-trading-bot-YOUR_PROJECT_ID.run.app
```

## 🔧 Configuration

### Environment Variables

#### Backend (Google Cloud Run)

Set these in the GitHub Actions workflow or Cloud Run console:

```bash
ENVIRONMENT=production
PYTHONPATH=/app
TRADING_ENABLED=false
PAPER_TRADING=true
USE_MOCK_DATA=true
LOG_LEVEL=INFO
```

#### Frontend (Vercel)

```bash
REACT_APP_API_URL=https://your-backend-url.run.app
```

### API Keys (Optional)

If you have real API keys, add them as Cloud Run environment variables:

```bash
# Deploy with environment variables
gcloud run deploy cloud-trading-bot \
    --image gcr.io/$PROJECT_ID/cloud-trading-bot:latest \
    --platform managed \
    --region us-west1 \
    --allow-unauthenticated \
    --set-env-vars "YAHOO_API_KEY=your_key,ALPHA_VANTAGE_KEY=your_key"
```

## 🏗️ Architecture

### Modern Cloud Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub        │    │   Vercel         │    │  Google Cloud   │
│   - Source Code │    │   - React App    │    │  - Cloud Run    │
│   - CI/CD       │───▶│   - Static Host  │───▶│  - Auto Scale   │
│   - Automation  │    │   - Global CDN   │    │  - Serverless   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Benefits Over AWS

| Feature | Old (AWS) | New (Modern) |
|---------|-----------|--------------|
| **Complexity** | High (Terraform, ECS, Lambda, DynamoDB) | Low (Cloud Run + Vercel) |
| **Setup Time** | Hours | Minutes |
| **Maintenance** | Manual infrastructure management | Zero maintenance |
| **Scaling** | Manual configuration | Automatic |
| **Cost** | Complex pricing, always-on | Pay-per-use, scales to zero |
| **Developer Experience** | Complex deployment process | Git push = deploy |

## 🚀 Deployment Workflow

### Automatic Deployment

Every push to `main` branch triggers:

1. **Testing**: Run Python and Node.js tests
2. **Backend Deployment**: 
   - Build Docker image
   - Push to Google Container Registry
   - Deploy to Cloud Run
3. **Frontend Deployment**:
   - Build React application
   - Deploy to Vercel
   - Update API URLs

### Manual Deployment

#### Backend Only

```bash
# Build and deploy backend manually
gcloud builds submit --tag gcr.io/$PROJECT_ID/cloud-trading-bot
gcloud run deploy cloud-trading-bot \
    --image gcr.io/$PROJECT_ID/cloud-trading-bot \
    --platform managed \
    --region us-west1 \
    --allow-unauthenticated
```

#### Frontend Only

```bash
cd frontend
vercel --prod
```

## 🔍 Monitoring and Debugging

### Cloud Run Logs

```bash
# View real-time logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=cloud-trading-bot"

# View specific time range
gcloud logs read "resource.type=cloud_run_revision" --since=1h
```

### Health Checks

- **Backend Health**: `https://your-backend-url.run.app/health`
- **API Status**: `https://your-backend-url.run.app/api/status`
- **Market Data**: `https://your-backend-url.run.app/api/market-data`

### Vercel Logs

```bash
# View deployment logs
vercel logs YOUR_DEPLOYMENT_URL
```

## 💰 Cost Estimation

### Google Cloud Run
- **Free Tier**: 2 million requests/month, 360,000 GB-seconds/month
- **Typical Cost**: $0-10/month for development, $10-50/month for production

### Vercel
- **Free Tier**: 100 GB bandwidth, unlimited static hosting
- **Typical Cost**: $0-20/month for most use cases

### Total Estimated Monthly Cost
- **Development**: $0-5/month
- **Production**: $10-70/month

*Compared to AWS: 60-80% cost reduction for similar workload*

## 🛠️ Local Development

### Backend Development

```bash
# Install dependencies
pip install -r requirements_Version9.txt
pip install flask flask-cors gunicorn

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your settings

# Run development server
export PYTHONPATH=$(pwd)
python api.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:8080" > .env.local

# Run development server
npm start
```

### Full Stack Development

```bash
# Terminal 1: Backend
python api.py

# Terminal 2: Frontend
cd frontend && npm start
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API Documentation: http://localhost:8080/api/status

## 🔒 Security Best Practices

### API Keys Management

1. **Never commit API keys** to the repository
2. **Use environment variables** in Cloud Run
3. **Use Vercel environment variables** for frontend config
4. **Rotate keys regularly**

### CORS Configuration

The API is configured with CORS to allow frontend access. For production, update `api.py` to restrict origins:

```python
CORS(app, origins=["https://your-frontend-domain.vercel.app"])
```

## 🆘 Troubleshooting

### Common Issues

#### "Permission Denied" during deployment
```bash
# Ensure service account has correct permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:SA_EMAIL" \
    --role="roles/run.admin"
```

#### "Image not found" error
```bash
# Verify image was pushed
gcloud container images list
```

#### Frontend can't connect to backend
1. Check CORS configuration in `api.py`
2. Verify `REACT_APP_API_URL` in Vercel environment variables
3. Ensure Cloud Run service allows unauthenticated requests

#### Backend returns 500 errors
```bash
# Check Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

### Getting Help

1. **Check GitHub Actions logs** for deployment issues
2. **View Cloud Run logs** for runtime issues  
3. **Check Vercel deployment logs** for frontend issues
4. **Open GitHub Issues** for bugs or questions

## 🎯 Next Steps

### Production Enhancements

1. **Add real API keys** for live market data
2. **Set up monitoring** with Cloud Monitoring
3. **Configure custom domain** for both frontend and backend
4. **Add database** (Cloud SQL) for persistent data
5. **Implement authentication** for secure access
6. **Add caching** with Cloud Memorystore

### Development Workflow

1. **Create feature branches** for new development
2. **Use pull requests** for code review
3. **Set up staging environment** for testing
4. **Add automated tests** for better reliability

---

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [React Deployment Guide](https://create-react-app.dev/docs/deployment/)