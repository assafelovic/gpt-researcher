FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g gitnexus@latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PATH="/opt/venv/bin:$PATH"
ENV GITNEXUS_HOME=/data/gitnexus
ENV REPOS_DIR=/data/repos
ENV PORT=8080
ENV GITNEXUS_MCP_READ_ONLY=1

RUN mkdir -p /data/gitnexus /data/repos \
    && chmod +x /app/entrypoint.sh /app/reindex.sh

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
