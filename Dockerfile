# Stage 1: Browser and build tools installation
FROM python:3.11.4-slim-bullseye AS install-browser

# Configure apt to be more resilient to temporary network issues
RUN echo "Acquire::Retries \"5\";" > /etc/apt/apt.conf.d/80retries && \
    echo "Acquire::http::Timeout \"120\";" > /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::https::Timeout \"120\";" >> /etc/apt/apt.conf.d/99timeout

# Install browser packages with architecture-specific handling
RUN apt-get update && \
    apt-get install -y gnupg wget ca-certificates --no-install-recommends && \
    # Detect architecture
    ARCH=$(dpkg --print-architecture) && \
    # Install build-essential on all architectures
    apt-get install -y --no-install-recommends build-essential && \
    # Install architecture-appropriate browsers
    if [ "$ARCH" = "amd64" ]; then \
        # Add Chrome repo and install Chrome on amd64
        wget -qO - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
        apt-get update && \
        # Install Chrome and Firefox on x86_64
        apt-get install -y google-chrome-stable && \
        apt-get install -y -t bullseye-backports firefox-esr || apt-get install -y firefox-esr && \
        # Try to install Chromium driver (may not be needed with Chrome)
        apt-get install -y chromium chromium-driver || echo "Chromium not available, using Chrome" && \
        # Install geckodriver for Firefox
        wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz && \
        tar -xvzf geckodriver-v0.33.0-linux64.tar.gz && \
        chmod +x geckodriver && \
        mv geckodriver /usr/local/bin/ && \
        rm geckodriver-v0.33.0-linux64.tar.gz && \
        # Print versions
        google-chrome --version && \
        firefox --version || firefox-esr --version; \
    elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "armhf" ]; then \
        # ARM architectures - try to install Firefox and Chromium if available
        # Try backports first for newer versions
        echo "deb http://deb.debian.org/debian bullseye-backports main" > /etc/apt/sources.list.d/backports.list && \
        apt-get update && \
        apt-get install -y -t bullseye-backports firefox-esr || echo "Firefox not available from backports" && \
        apt-get install -y firefox-esr || echo "Firefox not available" && \
        apt-get install -y chromium || echo "Chromium not available" && \
        apt-get install -y chromium-driver || echo "Chromium driver not available" && \
        # Print versions if available
        chromium --version || echo "Chromium version check skipped" && \
        firefox --version || firefox-esr --version || echo "Firefox version check skipped"; \
    fi && \
    # Cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies installation
FROM install-browser AS gpt-researcher-install

ENV PIP_ROOT_USER_ACTION=ignore
# Add environment variable to use binary wheels where possible
ENV PIP_PREFER_BINARY=1
WORKDIR /usr/src/app

# Install system dependencies required for Python packages
# Added libffi-dev, python3-dev, and additional dependencies for building packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip for better dependency resolution
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install Python dependencies in a single layer to optimize cache usage
COPY ./requirements.txt ./requirements.txt
COPY ./multi_agents/requirements.txt ./multi_agents/requirements.txt

# Install packages with optimizations for ARM
# - Split the installation to handle core dependencies first
# - Use --no-build-isolation for better performance on ARM
# - Set timeout to handle slow ARM builds
RUN pip install --no-cache-dir --timeout 300 numpy && \
    pip install --no-cache-dir --timeout 300 -r requirements.txt && \
    pip install --no-cache-dir --timeout 300 -r multi_agents/requirements.txt

# Stage 3: Final stage with non-root user and app
FROM gpt-researcher-install AS gpt-researcher

# Create a non-root user for security
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

# Make sure frontend static files are properly organized
# Create static directories if they don't exist
RUN mkdir -p /usr/src/app/frontend/static/new

# Copy frontend files specifically to ensure they're in the right place
COPY --chown=gpt-researcher:gpt-researcher ./frontend/index.html /usr/src/app/frontend/
COPY --chown=gpt-researcher:gpt-researcher ./frontend/styles.css /usr/src/app/frontend/
COPY --chown=gpt-researcher:gpt-researcher ./frontend/scripts.js /usr/src/app/frontend/
COPY --chown=gpt-researcher:gpt-researcher ./frontend/pdf_styles.css /usr/src/app/frontend/
COPY --chown=gpt-researcher:gpt-researcher ./frontend/static/* /usr/src/app/frontend/static/
COPY --chown=gpt-researcher:gpt-researcher ./frontend/static/new/* /usr/src/app/frontend/static/new/

# Expose the application's port
EXPOSE 8000

# Define the default command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
