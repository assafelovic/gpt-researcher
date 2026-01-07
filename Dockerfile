# Stage 1: Browser and build tools installation
#FROM python:3.13.3-slim-bookworm AS install-browser
FROM python:3.11.4-slim-bullseye AS install-browser

# Install Chromium, Chromedriver, Firefox, Geckodriver, and build tools in one layer
RUN apt-get update \
    && apt-get install -y gnupg wget ca-certificates --no-install-recommends \
    && ARCH=$(dpkg --print-architecture) \
    && wget -qO - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=${ARCH}] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y chromium chromium-driver \
    && chromium --version && chromedriver --version \
    && apt-get install -y --no-install-recommends firefox-esr build-essential curl pkg-config libssl-dev cmake git clang llvm \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && rustup default stable \
    && GECKO_ARCH=$(case ${ARCH} in amd64) echo "linux64" ;; arm64) echo "linux-aarch64" ;; *) echo "linux64" ;; esac) \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
    && tar -xvzf geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.36.0-${GECKO_ARCH}.tar.gz \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt lists to reduce image size

# Stage 2: Python dependencies installation
FROM install-browser AS gpt-researcher-install

ENV PIP_ROOT_USER_ACTION=ignore
ENV PATH="/root/.cargo/bin:${PATH}"
WORKDIR /usr/src/app

# Copy only the files needed for pip install first
COPY ./requirements.txt ./requirements.txt
COPY ./multi_agents/requirements.txt ./multi_agents/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir maturin && \
    pip install --no-cache-dir -r requirements.txt --upgrade --prefer-binary && \
    pip install --no-cache-dir -r multi_agents/requirements.txt --upgrade --prefer-binary

# Stage 3: Final stage with non-root user and app
FROM gpt-researcher-install AS gpt-researcher

# Basic server configuration
ARG HOST=0.0.0.0
ENV HOST=${HOST}
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# Uvicorn parameters used in CMD
ARG WORKERS=1
ENV WORKERS=${WORKERS}

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

# Copy the rest of the application files LAST
# This ensures that changing python code doesn't invalidate the pip install layer
COPY --chown=gpt-researcher:gpt-researcher ./ ./
CMD uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}
