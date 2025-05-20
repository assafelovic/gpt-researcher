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
    pip install --no-cache-dir --prefer-binary \
    bottleneck>=1.5.0 \
    cachetools>=5.5.2 \
    docstring-parser>=0.16 \
    google-api-core>=2.24.2 \
    google-auth>=2.40.1 \
    google-cloud-aiplatform>=1.93.0 \
    google-cloud-bigquery>=3.32.0 \
    google-cloud-core>=2.4.3 \
    google-cloud-resource-manager>=1.14.2 \
    google-cloud-storage>=2.19.0 \
    google-crc32c>=1.7.1 \
    google-genai>=1.15.0 \
    google-resumable-media>=2.7.2 \
    googleapis-common-protos>=1.70.0 \
    grpc-google-iam-v1>=0.14.2 \
    grpcio>=1.72.0rc1 \
    grpcio-status>=1.72.0rc1 \
    langchain-aws \
    langchain-cohere \
    langchain-google-vertexai>=2.0.24 \
    numpy \
    numexpr>=2.10.2 \
    proto-plus>=1.26.1 \
    protobuf>=6.31.0 \
    pyarrow>=19.0.1 \
    pyasn1>=0.6.1 \
    pyasn1-modules>=0.4.2 \
    python-dateutil>=2.9.0.post0 \
    rsa>=4.9.1 \
    shapely>=2.1.0 \
    uvicorn \
    validators>=0.35.0 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r multi_agents/requirements.txt --only-binary=:all:

# Stage 3: Final stage with non-root user and app
FROM gpt-researcher-install AS gpt-researcher

WORKDIR /usr/src/app

COPY ./ ./

ARG HOST=0.0.0.0
ENV HOST=${HOST}
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

ARG WORKER_COUNT=1
ENV WORKER_COUNT=${WORKER_COUNT}
ARG AUTO_RELOAD=true
ENV AUTO_RELOAD=${AUTO_RELOAD}
ARG AUTO_RELOAD_DIR=/usr/src/app
ENV AUTO_RELOAD_DIR=${AUTO_RELOAD_DIR}

# Define the default command to run the application
CMD ["sh", "-c", "if [ \"${AUTO_RELOAD}\" = \"true\" ]; then \
    uvicorn main:app --host ${HOST} --port ${PORT} --reload --reload-dir ${AUTO_RELOAD_DIR} --workers ${WORKER_COUNT}; \
    else \
    uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKER_COUNT}; \
    fi"]
