(docker container stop gptr > /dev/null 2>&1 || true) && (docker container rm gptr > /dev/null 2>&1 || true) \
  && (docker buildx build -f Dockerfile.fullstack . --tag=th3w1zard1/ai-researchwizard:latest --output=plain) \
  && (docker run -p 3000:3000 -p 8000:8000 --name=gptr --hostname=gptr --env-file .env th3w1zard1/ai-researchwizard:latest) \
#  && CONTAINER_ID=$(docker run -d -p 3000:3000 -p 8000:8000 --container-name=gptr --hostname=gptr --env-file .env th3w1zard1/ai-researchwizard:latest) \
#  && docker container logs $CONTAINER_ID -f
