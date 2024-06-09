# Use python:3.11.4-slim-bullseye as the base image
FROM python:3.11.4-slim-bullseye as install-browser

# Install Docker CLI
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

RUN echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update && apt-get install -y docker-ce-cli

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the host to the container
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy everything from the root folder into the /app directory in the container
COPY . /app

# Expose the port that the API server will run on
EXPOSE 8123

# Command to start the API server
CMD ["langgraph", "up"]
