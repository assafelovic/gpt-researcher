#!/bin/bash

# Deploy GPT Researcher to Google Cloud Run

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying GPT Researcher to Google Cloud Run${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# Load environment variables from .env file
export $(cat .env | grep  -v '^#' | xargs)

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ] || [ -z "$TAVILY_API_KEY" ]; then
    echo -e "${RED}❌ Missing required environment variables in .env file${NC}"
    echo "Required: OPENAI_API_KEY, TAVILY_API_KEY"
    exit 1
fi

# Get project ID
# PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  No Google Cloud project set${NC}"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}📦 Using project: $PROJECT_ID${NC}"

# Set variables
SERVICE_NAME="gpt-researcher"
REGION="us-central1" # Changed to a European region for better latency for local users
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build the Docker image
echo -e "${GREEN}🔨 Building Docker image...${NC}"
docker build -t $IMAGE -f Dockerfile.fullstack .

# Push to Container Registry
echo -e "${GREEN}📤 Pushing image to Container Registry...${NC}"
docker push $IMAGE

# Deploy to Cloud Run
echo -e "${GREEN}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 1 \
    --min-instances 0 \
    --port 8000 \
    --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY,TAVILY_API_KEY=$TAVILY_API_KEY,DOC_PATH=$DOC_PATH,LOGGING_LEVEL=INFO"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

if [ ! -z "$SERVICE_URL" ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🌐 Your app is running at: $SERVICE_URL${NC}"
    echo -e "${YELLOW}💡 Tip: The app scales to zero when not in use to save costs${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi