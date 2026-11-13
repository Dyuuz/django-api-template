# Base Image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    unzip \
    gcc \
    bash \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# geoipupdate — used at startup (see start.sh) to fetch the current
# GeoLite2-City database into a Railway volume mounted at /app/geoip.
# Check https://github.com/maxmind/geoipupdate/releases for the latest
# version before bumping this.
RUN wget -q https://github.com/maxmind/geoipupdate/releases/download/v7.1.0/geoipupdate_7.1.0_linux_amd64.deb \
    && apt-get update \
    && apt-get install -y ./geoipupdate_7.1.0_linux_amd64.deb --no-install-recommends \
    && rm geoipupdate_7.1.0_linux_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Copy start script
COPY start.sh .
RUN chmod +x start.sh

# Set entrypoint
ENTRYPOINT ["./start.sh"]