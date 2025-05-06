# Running on Linux

This guide will walk you through the process of deploying GPT Researcher on a Linux server.

## Server Requirements

The default Ubuntu droplet option on [DigitalOcean](https://m.do.co/c/1a2af257efba) works well, but this setup should work on any hosting service with similar specifications:

- 2 GB RAM
- 1 vCPU
- 50 GB SSD Storage

Here's a screenshot of the recommended Ubuntu machine specifications:

![Ubuntu Server Specifications](https://github.com/user-attachments/assets/035865c0-d1a2-4990-b7fb-544c229d5198)

## Deployment Steps

After setting up your server, follow these steps to install Docker, Docker Compose, and Nginx.


Some more commands to achieve that:

### Step 1: Update the System
### First, ensure your package index is up-to-date:

```bash
sudo apt update
### Step 2: Install Git
### Git is a version control system. Install it using:

sudo apt install git -y

### Verify the installation by checking the Git version:
git --version
### Step 3: Install Docker
### Docker is a platform for developing, shipping, and running applications inside containers.

### Install prerequisites:

sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
### Add Docker’s official GPG key:

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
### Set up the stable repository:

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
### Update the package index again and install Docker:

sudo apt update
sudo apt install docker-ce -y
### Verify Docker installation:

sudo systemctl status docker
### Optionally, add your user to the docker group to run Docker without sudo:

sudo usermod -aG docker ${USER}
### Log out and back in for the group change to take effect.

Step 4: Install Nginx
### Nginx is a high-performance web server.

### Install Nginx:

sudo apt install nginx -y
### Start and enable Nginx:

sudo systemctl start nginx
sudo systemctl enable nginx
### Verify Nginx installation:

sudo systemctl status nginx
```

Here's your nginx config file:

```bash
events {}

http {
   server {
       listen 80;
       server_name name.example;
       
       client_max_body_size 64M;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }

       location ~ ^/(ws|upload|files|outputs|getConfig|setConfig) {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "Upgrade";
           proxy_set_header Host $host;
       }
   }
}
```

And if you're using SSL:

```nginx
server {
    server_name name.example;
    
    client_max_body_size 64M;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location ~ ^/(ws|upload|files|outputs|getConfig|setConfig) {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
    
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/name.example/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/name.example/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = name.example) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    
    listen 80;
    server_name name.example;
    return 404; # managed by Certbot
}
```

And the relevant commands:


```bash
vim /etc/nginx/nginx.conf
### Edit it to reflect above. Then verify all is good with:

sudo nginx -t
# If there are no errors:

sudo systemctl restart nginx

# Clone .env.example as .env
# Run from root: 

docker-compose up --build

```