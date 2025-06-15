docker buildx build -f Dockerfile.fullstack . --tag=th3w1zard1/ai-researchwizard:latest
CONTAINER_ID=$(docker run -p 3000:3000 -p 8000:8000 -v .env:/app/.env --env-file .env th3w1zard1/ai-researchwizard:latest)
docker container logs $CONTAINER_ID -f
