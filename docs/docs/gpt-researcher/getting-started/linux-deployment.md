# Betrieb unter Linux

Diese Anleitung zeigt dir, wie du GPT Researcher auf einem Linux-Server bereitstellst.

## Server-Anforderungen

Das Standard-Ubuntu-Angebot bei [DigitalOcean](https://m.do.co/c/1a2af257efba) passt gut, aber das Setup funktioniert auch auf anderen Anbietern mit ähnlicher Ausstattung:

- 2 GB RAM
- 1 vCPU
- 50 GB SSD-Speicher

## Bereitstellungsschritte

Nachdem dein Server eingerichtet ist, installierst du Docker, Docker Compose und Nginx.

### 1. System aktualisieren

```bash
sudo apt update
```

### 2. Git installieren

```bash
sudo apt install git -y
git --version
```

### 3. Docker installieren

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce -y
sudo systemctl status docker
```

Optional kannst du deinen Benutzer zur Docker-Gruppe hinzufügen, damit Docker ohne `sudo` läuft:

```bash
sudo usermod -aG docker ${USER}
```

Melde dich danach einmal ab und wieder an, damit die Gruppenänderung wirksam wird.

### 4. Nginx installieren

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

## Nginx-Konfiguration

Nutze beispielsweise diese Konfiguration als Reverse Proxy für Frontend und Backend:

```nginx
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

Wenn du SSL verwendest, kannst du die Konfiguration so erweitern:

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

  listen 443 ssl;
  ssl_certificate /etc/letsencrypt/live/name.example/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/name.example/privkey.pem;
  include /etc/letsencrypt/options-ssl-nginx.conf;
  ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
  if ($host = name.example) {
    return 301 https://$host$request_uri;
  }

  listen 80;
  server_name name.example;
  return 404;
}
```

## Beispielhafte Befehle

```bash
vim /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx
```

Wenn du die Anwendung direkt auf dem Server starten möchtest, kannst du zusätzlich Folgendes nutzen:

```bash
cp .env.example .env
docker-compose up --build
```

## Hinweis

Je nach Deployment-Szenario kannst du die Ports für Frontend und Backend anpassen. Die Standardkonfiguration geht von `3000` für das Frontend und `8000` für das Backend aus.
