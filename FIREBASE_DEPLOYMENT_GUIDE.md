# Firebase Deployment and Testing Guide

## 🚀 Deployment Architecture

### Current Setup
- **Frontend**: React app → Firebase Hosting (global CDN)
- **Backend**: Python Functions → Firebase Functions (serverless)
- **Database**: Firestore (real-time, scalable)
- **CI/CD**: GitHub Actions (automated deployment)

### Firebase Project Details
- **Project ID**: `cloud-trading-bot-468900`
- **Region**: us-central1
- **Hosting URL**: https://cloud-trading-bot-468900.web.app
- **Functions URL**: https://us-central1-cloud-trading-bot-468900.cloudfunctions.net

## 🔧 Configuration Files

### Firebase Configuration (`frontend/firebase.json`)
```json
{
  "hosting": {
    "public": "build",
    "rewrites": [
      { "source": "/api/**", "function": "api" }
    ]
  },
  "functions": {
    "source": "../functions",
    "runtime": "python39"
  }
}
```

### Frontend Environment (`.env.production`)
```env
REACT_APP_API_URL=/api
REACT_APP_ENVIRONMENT=production
REACT_APP_API_TIMEOUT=30000
```

## 🚀 Deployment Process

### 1. Automatic Deployment (Recommended)
Triggered on push to `main` branch:

```bash
git push origin main
```

This runs the `firebase-hosting.yml` workflow which:
1. Builds the React frontend
2. Installs Python dependencies for Functions
3. Deploys both hosting and functions to Firebase

### 2. Manual Deployment
```bash
# Install dependencies
cd frontend && npm install
cd ../functions && pip install -r requirements.txt

# Build frontend
cd ../frontend && npm run build

# Deploy to Firebase
firebase deploy --project cloud-trading-bot-468900
```

## 🧪 Testing

### Production Deployment Test
Run the comprehensive test suite:

```bash
python test_production_deployment.py
```

This tests:
- ✅ Site connectivity
- ✅ API endpoints (/health, /status)
- ✅ Backtest workflow
- ✅ Error handling
- ✅ Direct Firebase Functions (fallback)

### Manual API Testing
```bash
# Test health endpoint
curl https://cloud-trading-bot-468900.web.app/api/health

# Test status endpoint  
curl https://cloud-trading-bot-468900.web.app/api/status

# Test backtest start
curl -X POST https://cloud-trading-bot-468900.web.app/api/backtest/start \
  -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL"],"initial_capital":10000}'
```

### Direct Functions Testing (Troubleshooting)
```bash
# Test Functions directly (bypassing hosting)
curl https://us-central1-cloud-trading-bot-468900.cloudfunctions.net/api/health
curl https://us-central1-cloud-trading-bot-468900.cloudfunctions.net/api/status
```

## 🚨 Troubleshooting

### Common Issues

#### 1. API Endpoints Return 404
**Cause**: Firebase Functions not deployed
**Solution**: 
- Check if the firebase-hosting.yml workflow completed successfully
- Ensure `firebase deploy` includes functions
- Verify Functions are listed in Firebase Console

#### 2. Functions Deploy But Return Errors
**Cause**: Missing dependencies or import errors
**Solution**:
- Check `functions/requirements.txt` includes all dependencies
- Review Firebase Functions logs in the console
- Test Functions locally first

#### 3. CORS Issues
**Cause**: Cross-origin request restrictions
**Solution**:
- Verify CORS configuration in `functions/main.py`
- Check Firebase Functions CORS settings
- Ensure frontend is served from same domain

#### 4. Slow Response Times
**Cause**: Cold start delays in serverless functions
**Solution**:
- Consider warming functions with scheduled pings
- Optimize function startup time
- Use Firebase Functions concurrency settings

### Debug Commands

```bash
# Check Firebase project status
firebase projects:list

# Check Functions deployment
firebase functions:list --project cloud-trading-bot-468900

# View Functions logs
firebase functions:log --project cloud-trading-bot-468900

# Test local Functions
cd functions && python -c "from main import handle_request; print('Import successful')"
```

## 📊 Monitoring

### GitHub Actions
- Monitor deployment workflows in the Actions tab
- Check for failed deployments and error logs
- Review test results from automated runs

### Firebase Console
- Monitor Functions execution and errors
- Check hosting deployment status
- Review usage metrics and quotas

### Production Testing
- Automated tests run every 6 hours
- Manual tests can be triggered via GitHub Actions
- Test results uploaded as artifacts

## 🔒 Security

### Environment Variables
- Secrets stored in GitHub repository secrets
- Firebase service account for deployment
- No sensitive data in source code

### Access Control
- Firebase project access restricted to authorized users
- GitHub repository protected branches
- Deployment requires successful tests

## 📈 Performance

### Optimization Tips
- Functions deploy with minimal dependencies
- Frontend built with production optimizations
- Static assets served via Firebase CDN
- Gzip compression enabled by default

### Scaling
- Firebase Functions auto-scale based on demand
- Hosting uses global CDN for fast delivery
- Database can handle high concurrent loads

## 🆘 Support

### Getting Help
1. Check GitHub Actions logs for deployment issues
2. Review Firebase Console for runtime errors
3. Run production tests to identify specific problems
4. Check this documentation for common solutions

### Reporting Issues
1. Run `python test_production_deployment.py`
2. Include test output in issue report
3. Check Firebase Functions logs
4. Provide deployment workflow status