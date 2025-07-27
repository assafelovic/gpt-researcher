# Deploy GPT Researcher to Cloud (Cheapest Options)

## Option 1: Railway (Recommended - Easiest)

1. Fork this repository on GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your forked repository
5. Add environment variables:
   ```
   OPENAI_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here
   ```
6. Deploy! Access at: `https://your-app.railway.app`

**Cost**: Free tier ($5 credit) or ~$5-10/month

## Option 2: Fly.io (Free Tier Available)

1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login and launch:
   ```bash
   fly auth login
   fly launch
   ```

3. Set secrets:
   ```bash
   fly secrets set OPENAI_API_KEY="your_key_here"
   fly secrets set TAVILY_API_KEY="your_key_here"
   ```

4. Deploy:
   ```bash
   fly deploy --dockerfile Dockerfile.minimal
   ```

**Cost**: Free tier (3 VMs) or ~$5-7/month

## Option 3: Google Cloud Run (Pay-per-use)

1. Install gcloud CLI and authenticate
2. Build and push image:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/gpt-researcher
   ```

3. Deploy:
   ```bash
   gcloud run deploy gpt-researcher \
     --image gcr.io/YOUR_PROJECT/gpt-researcher \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY="your_key",TAVILY_API_KEY="your_key"
   ```

**Cost**: $0-5/month (scales to zero when not in use)

## Option 4: Oracle Cloud (Always Free)

1. Create Oracle Cloud account
2. Create a compute instance (ARM-based for free tier)
3. SSH into instance and run:
   ```bash
   # Install Docker
   sudo apt update
   sudo apt install docker.io docker-compose
   
   # Clone repo
   git clone https://github.com/your-fork/gpt-researcher
   cd gpt-researcher
   
   # Create .env file
   echo "OPENAI_API_KEY=your_key" > .env
   echo "TAVILY_API_KEY=your_key" >> .env
   
   # Run with docker-compose (backend only)
   docker-compose up gpt-researcher
   ```

**Cost**: $0 forever

## Tips to Minimize Costs:

1. **Use backend only** - Skip the NextJS frontend
2. **Set auto-scaling to zero** when not in use
3. **Use smaller instances** (512MB RAM is enough)
4. **Monitor usage** and set spending alerts
5. **Cache results** to reduce API calls

## Environment Variables Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `TAVILY_API_KEY` - Your Tavily API key (for web search)
- `LANGCHAIN_API_KEY` - Optional, for tracing
- `DOC_PATH` - Optional, for local documents