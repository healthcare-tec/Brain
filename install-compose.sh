#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Install Docker Compose V2 Plugin
#
# Fixes: docker-compose 1.29.2 broken on Python 3.12
#        (ModuleNotFoundError: No module named 'distutils')
#
# Works as root (no sudo needed) on aarch64 and x86_64
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "🔧  Installing Docker Compose V2 plugin..."
echo "    (Fixes docker-compose 1.29.2 + Python 3.12 incompatibility)"
echo ""

# ── Detect architecture ──────────────────────────────────────────────────────
ARCH=$(uname -m)
case $ARCH in
    x86_64)  ARCH_LABEL="x86_64" ;;
    aarch64) ARCH_LABEL="aarch64" ;;
    armv7l)  ARCH_LABEL="armv7" ;;
    *)
        echo "❌  Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

echo "Architecture: $ARCH_LABEL"

# ── Method 1: apt (no sudo needed when running as root) ─────────────────────
echo "Trying apt install..."
if apt-get update -qq 2>/dev/null && apt-get install -y docker-compose-plugin 2>/dev/null; then
    echo ""
    echo "✅  docker-compose-plugin installed via apt."
    docker compose version
    exit 0
fi

# ── Method 2: Download binary from GitHub releases ──────────────────────────
echo "apt method failed, downloading binary from GitHub..."

# Use a known stable version (v2.27.1) to avoid API rate limits
COMPOSE_VERSION="v2.27.1"

# Try to get latest version from GitHub API (optional, fallback to above)
LATEST=$(curl -fsSL --connect-timeout 5 \
    "https://api.github.com/repos/docker/compose/releases/latest" 2>/dev/null \
    | grep '"tag_name"' | head -1 | cut -d'"' -f4)
if [ -n "$LATEST" ]; then
    COMPOSE_VERSION="$LATEST"
fi

echo "Version: $COMPOSE_VERSION  Arch: $ARCH_LABEL"

# Install to system-wide Docker CLI plugins directory
DEST="/usr/local/lib/docker/cli-plugins"
mkdir -p "$DEST"

URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH_LABEL}"
echo "Downloading: $URL"

curl -fsSL "$URL" -o "$DEST/docker-compose"
chmod +x "$DEST/docker-compose"

echo ""
echo "✅  Docker Compose V2 installed at $DEST/docker-compose"
docker compose version
