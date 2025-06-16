########################################################################
# Stage 1: Frontend build
########################################################################
FROM node:slim AS frontend-builder
WORKDIR /app/frontend/nextjs

# Copy package files and install dependencies
COPY frontend/nextjs/package.json frontend/nextjs/package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend application and build it
COPY frontend/nextjs/ ./
RUN npm run build

########################################################################
# Stage 2: Browser and backend build tools installation
########################################################################
FROM python:3.13.3-slim-bookworm AS install-browser

# Install Chromium, Chromedriver, Firefox, Geckodriver, and build tools in one layer
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
  && echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries \
  && echo 'Acquire::https::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries \
  && echo 'Acquire::ftp::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries \
  && apt-get update \
  && apt-get install -y gnupg wget ca-certificates --no-install-recommends \
  && ARCH=$(dpkg --print-architecture) \
  && if [ "$ARCH" = "arm64" ]; then \
  apt-get install -y chromium chromium-driver \
  && chromium --version && chromedriver --version; \
  else \
  wget -qO - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb [arch=${ARCH}] http://dl.google.com/linux/chrome/deb/ stable main" \
  > /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update \
  && apt-get install -y google-chrome-stable; \
  fi \
  && apt-get install -y --no-install-recommends firefox-esr build-essential \
  && GECKO_ARCH=$(case ${ARCH} in amd64) echo "linux64" ;; arm64) echo "linux-aarch64" ;; *) echo "linux64" ;; esac) \
  && wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
  && tar -xvzf geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
  && chmod +x geckodriver \
  && mv geckodriver /usr/local/bin/ \
  && rm geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
  && rm -rf /var/lib/apt/lists/*

########################################################################
# Stage 3: Python dependencies installation
########################################################################
FROM install-browser AS backend-builder
WORKDIR /usr/src/app

ENV PIP_ROOT_USER_ACTION=ignore

COPY ./requirements.txt ./requirements.txt
COPY ./multi_agents/requirements.txt ./multi_agents/requirements.txt

# Install Python packages with retry logic and timeout configuration
RUN pip config set global.timeout 60 && \
  pip config set global.retries 3 && \
  pip install --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt --upgrade --prefer-binary && \
  pip install --no-cache-dir -r multi_agents/requirements.txt --upgrade --prefer-binary

########################################################################
# Stage 4: Final image with backend, frontend
########################################################################
FROM backend-builder AS final

WORKDIR /usr/src/app

# Install Node.js and supervisord with retry logic
RUN apt-get update && \
  apt-get install -y curl supervisor nginx && \
  curl -fsSL --retry 3 --retry-delay 10 https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  rm -rf /var/lib/apt/lists/*

# Set backend server configuration
ARG HOST=0.0.0.0
ENV HOST=${HOST}

ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

ARG NEXT_PORT=3000
ENV NEXT_PORT=${NEXT_PORT}
EXPOSE ${NEXT_PORT}

# Internal Next.js port (not exposed)
ARG NEXT_INTERNAL_PORT=3001
ENV NEXT_INTERNAL_PORT=${NEXT_INTERNAL_PORT}

# Copy application files
COPY ./ ./

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/nextjs/.next ./frontend/nextjs/.next
COPY --from=frontend-builder /app/frontend/nextjs/node_modules ./frontend/nextjs/node_modules
COPY --from=frontend-builder /app/frontend/nextjs/public ./frontend/nextjs/public
COPY --from=frontend-builder /app/frontend/nextjs/package.json ./frontend/nextjs/package.json
# Ensure next.config.mjs and other necessary files are present
COPY --from=frontend-builder /app/frontend/nextjs/next.config.mjs ./frontend/nextjs/next.config.mjs

# Create nginx configuration
RUN echo 'events {' > /etc/nginx/nginx.conf && \
  echo '    worker_connections 1024;' >> /etc/nginx/nginx.conf && \
  echo '}' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo 'http {' >> /etc/nginx/nginx.conf && \
  echo '    include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf && \
  echo '    default_type application/octet-stream;' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '    # Logging' >> /etc/nginx/nginx.conf && \
  echo '    access_log /var/log/nginx/access.log;' >> /etc/nginx/nginx.conf && \
  echo '    error_log /var/log/nginx/error.log;' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '    # Gzip compression' >> /etc/nginx/nginx.conf && \
  echo '    gzip on;' >> /etc/nginx/nginx.conf && \
  echo '    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '    # WebSocket support' >> /etc/nginx/nginx.conf && \
  echo '    map $http_upgrade $connection_upgrade {' >> /etc/nginx/nginx.conf && \
  echo '        default upgrade;' >> /etc/nginx/nginx.conf && \
  echo '        '"'"''"'"' close;' >> /etc/nginx/nginx.conf && \
  echo '    }' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '    server {' >> /etc/nginx/nginx.conf && \
  echo '        listen 3000;' >> /etc/nginx/nginx.conf && \
  echo '        server_name _;' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '        # Proxy backend routes to FastAPI server' >> /etc/nginx/nginx.conf && \
  echo '        location /outputs {' >> /etc/nginx/nginx.conf && \
  echo '            proxy_pass http://127.0.0.1:8000;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Host $host;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/nginx.conf && \
  echo '        }' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '        location /reports {' >> /etc/nginx/nginx.conf && \
  echo '            proxy_pass http://127.0.0.1:8000;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Host $host;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/nginx.conf && \
  echo '        }' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '        location /ws {' >> /etc/nginx/nginx.conf && \
  echo '            proxy_pass http://127.0.0.1:8000;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_http_version 1.1;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Upgrade $http_upgrade;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Connection $connection_upgrade;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Host $host;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/nginx.conf && \
  echo '        }' >> /etc/nginx/nginx.conf && \
  echo '' >> /etc/nginx/nginx.conf && \
  echo '        # Proxy all other requests to Next.js' >> /etc/nginx/nginx.conf && \
  echo '        location / {' >> /etc/nginx/nginx.conf && \
  echo '            proxy_pass http://127.0.0.1:3001;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header Host $host;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
  echo '            proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/nginx.conf && \
  echo '        }' >> /etc/nginx/nginx.conf && \
  echo '    }' >> /etc/nginx/nginx.conf && \
  echo '}' >> /etc/nginx/nginx.conf

# Create supervisord configuration
# stdout/stderr_maxbytes prevents log file rotation and ensures continuous output
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
  echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '[program:backend]' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'command=uvicorn main:app --host %(ENV_HOST)s --port %(ENV_PORT)s' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'directory=/usr/src/app' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '[program:frontend]' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'command=npm run start -- -p %(ENV_NEXT_INTERNAL_PORT)s' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'directory=/usr/src/app/frontend/nextjs' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo '[program:nginx]' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'command=nginx -g "daemon off;"' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
  echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf

# Start supervisord to manage both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
