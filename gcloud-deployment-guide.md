# Google Cloud Project Update Guide

## Prerequisites
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Initialize and authenticate
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Method 1: Cloud Build (Recommended)
```bash
# Simple deployment
gcloud builds submit --config cloudbuild.yaml

# With substitutions
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_SERVICE_NAME=gpt-researcher

# View logs in real-time
gcloud beta builds submit --config cloudbuild.yaml
```

## Method 2: Direct Cloud Run Deployment
```bash
# Build and deploy in one command
gcloud run deploy gpt-researcher \
  --source . \
  --region us-central1 \
  --allow-unauthenticated

# Deploy pre-built image
gcloud run deploy gpt-researcher \
  --image gcr.io/YOUR_PROJECT_ID/gpt-researcher \
  --region us-central1 \
  --platform managed
```

## Method 3: Manual Steps
```bash
# 1. Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/gpt-researcher -f Dockerfile.minimal .

# 2. Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/gpt-researcher

# 3. Deploy to Cloud Run
gcloud run deploy gpt-researcher \
  --image gcr.io/YOUR_PROJECT_ID/gpt-researcher \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 1 \
  --port 8000 \
  --allow-unauthenticated
```

## Common Update Scenarios

### Update environment variables:
```bash
gcloud run services update gpt-researcher \
  --set-env-vars OPENAI_API_KEY=your-key,TAVILY_API_KEY=your-key \
  --region us-central1
```

### Update memory/CPU:
```bash
gcloud run services update gpt-researcher \
  --memory 2Gi --cpu 2 \
  --region us-central1
```

### View deployment status:
```bash
gcloud run services describe gpt-researcher --region us-central1
```

### Check logs:
```bash
gcloud run logs read --service gpt-researcher --region us-central1
```

## Troubleshooting Commands
```bash
# List all builds
gcloud builds list --limit=5

# View specific build logs
gcloud builds log BUILD_ID

# Check service status
gcloud run services list --region us-central1

# View service logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

## Quick Deploy Script

For convenience, use the existing deploy script:

```bash
./deploy-to-gcloud.sh
```

## Cost Optimization

- **Min instances = 0**: App scales to zero when not in use
- **Max instances = 1**: Prevents multiple instances (since you're the only user)
- **Memory = 1Gi**: Sufficient for GPT Researcher
- **Region**: Choose closest to you for better latency

## Estimated Costs

- **When idle**: $0 (scales to zero)
- **Active usage**: ~$0.00002400/second
- **Monthly estimate**: $0-5 for personal use

## Access Your App

After deployment, you'll get a URL like:
```
https://gpt-researcher-xxxxx-uc.a.run.app
```

## Monitoring

View logs:
```bash
gcloud run services logs read gpt-researcher
```

Check metrics in [Google Cloud Console](https://console.cloud.google.com/run)

## Troubleshooting

1. **Authentication errors**: Make sure you're logged in with `gcloud auth login`
2. **Quota errors**: Enable billing on your Google Cloud project
3. **Build errors**: Ensure Docker is running
4. **API not enabled**: Run the enable services command from step 1