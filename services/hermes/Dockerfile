FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Hermes agent from upstream (NousResearch). Pin via HERMES_REF if needed.
ARG HERMES_REF=main
RUN git clone --depth=1 --branch "${HERMES_REF}" \
      https://github.com/NousResearch/hermes-agent.git /opt/hermes \
    && pip install --no-cache-dir -e /opt/hermes || \
       pip install --no-cache-dir "hermes-agent" || true

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN chmod +x /app/entrypoint.sh /app/seed_memory.py

ENV HERMES_HOME=/data/hermes
ENV PORT=8080

RUN mkdir -p /data/hermes

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
