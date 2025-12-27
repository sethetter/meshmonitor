# Meshtastic MQTT Monitor
# Single container: Mosquitto + Python app + Litestream replication
FROM python:3.11-slim

# Install litestream
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && LITESTREAM_ARCH=$(case ${TARGETARCH} in \
        amd64) echo "amd64" ;; \
        arm64) echo "arm64" ;; \
        *) echo "amd64" ;; \
    esac) \
    && curl -fsSL "https://github.com/benbjohnson/litestream/releases/download/v0.5.2/litestream-v0.5.2-linux-${LITESTREAM_ARCH}.tar.gz" \
        | tar -C /usr/local/bin -xzf - \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install mosquitto, tini, and gcc (for pip packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    mosquitto \
    tini \
    gcc \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies (gcc needed here)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove gcc after pip install
RUN apt-get purge -y gcc && apt-get autoremove -y

# Copy application files
COPY . .

# Copy configs to expected locations
COPY litestream.yml /etc/litestream.yml
COPY mosquitto/config/mosquitto.conf /mosquitto/config/mosquitto.conf

# Create data directories
RUN mkdir -p /data && chmod +x /app/entrypoint.sh

EXPOSE 5000 1883 8883

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/entrypoint.sh"]
