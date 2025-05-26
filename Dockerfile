# Stage 1: Browser and build tools installation
#FROM python:3.11.4-slim-bullseye AS install-browser
FROM python:3.13.3-slim-bookworm AS install-browser

# Install Chromium, Chromedriver, Firefox, Geckodriver, and build tools in one layer
RUN apt-get update \
    && apt-get install -y gnupg wget ca-certificates --no-install-recommends \
    && wget -qO - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y chromium chromium-driver \
    && chromium --version && chromedriver --version \
    && apt-get install -y --no-install-recommends firefox-esr build-essential \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xvzf geckodriver-v0.33.0-linux64.tar.gz \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.33.0-linux64.tar.gz \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt lists to reduce image size

# Stage 2: Python dependencies installation
FROM install-browser AS gpt-researcher-install

ENV PIP_ROOT_USER_ACTION=ignore
WORKDIR /usr/src/app

# Copy and install Python dependencies in a single layer to optimize cache usage
COPY ./requirements.txt ./requirements.txt
COPY ./multi_agents/requirements.txt ./multi_agents/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r multi_agents/requirements.txt

# Stage 3: Final stage with non-root user and app
FROM gpt-researcher-install AS gpt-researcher

# Create a non-root user for security
# NOTE: Don't use this if you are relying on `_check_pkg` to pip install packages dynamically.
RUN useradd -ms /bin/bash gpt-researcher && \
    chown -R gpt-researcher:gpt-researcher /usr/src/app && \
    # Add these lines to create and set permissions for outputs directory
    mkdir -p /usr/src/app/outputs && \
    chown -R gpt-researcher:gpt-researcher /usr/src/app/outputs && \
    chmod 777 /usr/src/app/outputs
USER gpt-researcher
WORKDIR /usr/src/app

# Copy the rest of the application files with proper ownership
COPY --chown=gpt-researcher:gpt-researcher ./ ./

# Basic server configuration
ARG HOST=0.0.0.0
ENV HOST=${HOST}
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# Uvicorn parameters
ARG WORKERS=1
ENV WORKERS=${WORKERS}
ARG TIMEOUT_KEEP_ALIVE=300
ENV TIMEOUT_KEEP_ALIVE=${TIMEOUT_KEEP_ALIVE}
ARG LOG_LEVEL=info
ENV LOG_LEVEL=${LOG_LEVEL}
ARG ACCESS_LOG=true
ENV ACCESS_LOG=${ACCESS_LOG}
ARG PROXY_HEADERS=true
ENV PROXY_HEADERS=${PROXY_HEADERS}
ARG SERVER_HEADER=true
ENV SERVER_HEADER=${SERVER_HEADER}
ARG DATE_HEADER=true
ENV DATE_HEADER=${DATE_HEADER}
ARG FORWARDED_ALLOW_IPS=*
ENV FORWARDED_ALLOW_IPS=${FORWARDED_ALLOW_IPS}
ARG ROOT_PATH=""
ENV ROOT_PATH=${ROOT_PATH}
ARG BACKLOG=2048
ENV BACKLOG=${BACKLOG}
ARG LIMIT_CONCURRENCY=null
ENV LIMIT_CONCURRENCY=${LIMIT_CONCURRENCY}
ARG LIMIT_MAX_REQUESTS=null
ENV LIMIT_MAX_REQUESTS=${LIMIT_MAX_REQUESTS}
ARG RELOAD=false
ENV RELOAD=${RELOAD}
ARG RELOAD_DELAY=0.25
ENV RELOAD_DELAY=${RELOAD_DELAY}
ARG WS_MAX_SIZE=16777216
ENV WS_MAX_SIZE=${WS_MAX_SIZE}
ARG WS_PING_INTERVAL=20
ENV WS_PING_INTERVAL=${WS_PING_INTERVAL}
ARG WS_PING_TIMEOUT=20
ENV WS_PING_TIMEOUT=${WS_PING_TIMEOUT}
ARG WS_PER_MESSAGE_DEFLATE=true
ENV WS_PER_MESSAGE_DEFLATE=${WS_PER_MESSAGE_DEFLATE}

# SSL configuration
ARG SSL_KEYFILE=""
ENV SSL_KEYFILE=${SSL_KEYFILE}
ARG SSL_CERTFILE=""
ENV SSL_CERTFILE=${SSL_CERTFILE}
ARG SSL_KEYFILE_PASSWORD=""
ENV SSL_KEYFILE_PASSWORD=${SSL_KEYFILE_PASSWORD}
ARG SSL_CA_CERTS=""
ENV SSL_CA_CERTS=${SSL_CA_CERTS}
ARG SSL_CIPHERS=TLSv1
ENV SSL_CIPHERS=${SSL_CIPHERS}

# CORS middleware configuration
ARG CORS_ENABLED=true
ENV CORS_ENABLED=${CORS_ENABLED}
ARG CORS_ORIGINS=http://localhost:3000,http://localhost:${PORT}
ENV CORS_ORIGINS=${CORS_ORIGINS}
ARG CORS_ALLOW_CREDENTIALS=true
ENV CORS_ALLOW_CREDENTIALS=${CORS_ALLOW_CREDENTIALS}
ARG CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
ENV CORS_ALLOW_METHODS=${CORS_ALLOW_METHODS}
ARG CORS_ALLOW_HEADERS=*
ENV CORS_ALLOW_HEADERS=${CORS_ALLOW_HEADERS}

# Command to run the application
CMD uvicorn main:app \
    --host ${HOST} \
    --port ${PORT} \
    --workers ${WORKERS} \
    --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE} \
    --log-level ${LOG_LEVEL} \
    $([ "${ACCESS_LOG}" = "true" ] && echo "--access-log" || echo "--no-access-log") \
    $([ "${PROXY_HEADERS}" = "true" ] && echo "--proxy-headers" || echo "--no-proxy-headers") \
    $([ "${SERVER_HEADER}" = "true" ] && echo "--server-header" || echo "--no-server-header") \
    $([ "${DATE_HEADER}" = "true" ] && echo "--date-header" || echo "--no-date-header") \
    --forwarded-allow-ips ${FORWARDED_ALLOW_IPS} \
    $([ -n "${ROOT_PATH}" ] && echo "--root-path ${ROOT_PATH}") \
    --backlog ${BACKLOG} \
    $([ "${LIMIT_CONCURRENCY}" != "null" ] && echo "--limit-concurrency ${LIMIT_CONCURRENCY}") \
    $([ "${LIMIT_MAX_REQUESTS}" != "null" ] && echo "--limit-max-requests ${LIMIT_MAX_REQUESTS}") \
    $([ "${RELOAD}" = "true" ] && echo "--reload") \
    $([ "${RELOAD}" = "true" ] && echo "--reload-delay ${RELOAD_DELAY}") \
    --ws-max-size ${WS_MAX_SIZE} \
    --ws-ping-interval ${WS_PING_INTERVAL} \
    --ws-ping-timeout ${WS_PING_TIMEOUT} \
    $([ "${WS_PER_MESSAGE_DEFLATE}" = "true" ] && echo "--ws-per-message-deflate") \
    $([ -n "${SSL_KEYFILE}" ] && echo "--ssl-keyfile ${SSL_KEYFILE}") \
    $([ -n "${SSL_CERTFILE}" ] && echo "--ssl-certfile ${SSL_CERTFILE}") \
    $([ -n "${SSL_KEYFILE_PASSWORD}" ] && echo "--ssl-keyfile-password ${SSL_KEYFILE_PASSWORD}") \
    $([ -n "${SSL_CA_CERTS}" ] && echo "--ssl-ca-certs ${SSL_CA_CERTS}") \
    $([ -n "${SSL_CIPHERS}" ] && echo "--ssl-ciphers ${SSL_CIPHERS}")
