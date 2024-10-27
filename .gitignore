#This is an example webapp.io configuration for Docker!
FROM vm/ubuntu:18.04

# To note: Layerfiles create entire VMs, *not* containers!

# install the latest version of Docker, as in the official Docker installation tutorial.
RUN apt-get update && \
    apt-get install ca-certificates curl gnupg lsb-release && \
    sudo mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" |\
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install docker-ce docker-ce-cli containerd.io

# copy files from the repository into this staging server
COPY . .

RUN docker build -t image .
RUN docker run -d -p 80:80 image
EXPOSE WEBSITE http://localhost:80
