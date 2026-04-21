#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Install Docker Compose V2 Plugin
#
# Fixes: docker-compose 1.29.2 broken on Python 3.12
#        (ModuleNotFoundError: No module named 'distutils')
#
# Solution: install Docker Compose V2 (pure Go binary, no Python dependency)
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "🔧  Installing Docker Compose V2 plugin..."
echo "    (Fixes docker-compose 1.29.2 + Python 3.12 incompatibility)"
echo ""

# ── Detect architecture ──────────────────────────────────────────────────────
ARCH=$(uname -m)
case $ARCH in
    x86_64)   ARCH_LABEL="x86_64" ;;
    aarch64)  ARCH_LABEL="aarch64" ;;
    armv7l)   ARCH_LABEL="armv7" ;;
    *)
        echo "❌  Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# ── Method 1: apt (Docker official repo) ────────────────────────────────────
echo "Trying apt install..."
if sudo apt-get update -qq 2>/dev/null && sudo apt-get install -y docker-compose-plugin 2>/dev/null; then
    echo ""
    echo "✅  docker-compose-plugin installed via apt."
    docker compose version
    exit 0
fi

# ── Method 2: Download binary from GitHub releases ──────────────────────────
echo "apt method failed, downloading binary from GitHub..."

# Get latest version tag
COMPOSE_VERSION=$(curl -fsSL https://api.github.com/repos/docker/compose/releases/latest \
    | grep '"tag_name"' | head -1 | cut -d'"' -f4)
COMPOSE_VERSION=${COMPOSE_VERSION:-v2.27.1}

echo "Version: $COMPOSE_VERSION  Arch: $ARCH_LABEL"

# Install to Docker CLI plugins directory
DEST="/usr/local/lib/docker/cli-plugins"
sudo mkdir -p "$DEST"

URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH_LABEL}"
echo "Downloading from: $URL"

sudo curl -fsSL "$URL" -o "$DEST/docker-compose"
sudo chmod +x "$DEST/docker-compose"

echo ""
echo "✅  Docker Compose V2 installed at $DEST/docker-compose"
docker compose version
