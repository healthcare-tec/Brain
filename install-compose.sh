#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Install Docker Compose Plugin
# Tested on Ubuntu 22.04 / 24.04 with Docker 24+
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "🔧  Installing docker-compose-plugin..."

# Method 1: apt (Ubuntu/Debian with Docker official repo)
if apt-cache show docker-compose-plugin &>/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y docker-compose-plugin
    echo "✅  docker-compose-plugin installed via apt."
    docker compose version
    exit 0
fi

# Method 2: Download binary directly from GitHub
echo "apt package not found, downloading binary..."
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
COMPOSE_VERSION=${COMPOSE_VERSION:-v2.27.0}
ARCH=$(uname -m)
case $ARCH in
    x86_64) ARCH="x86_64" ;;
    aarch64) ARCH="aarch64" ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

DEST="${DOCKER_CLI_PLUGINS_DIR:-$HOME/.docker/cli-plugins}"
mkdir -p "$DEST"
curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
    -o "$DEST/docker-compose"
chmod +x "$DEST/docker-compose"

echo "✅  docker compose plugin installed at $DEST/docker-compose"
docker compose version
