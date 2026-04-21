#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Install Docker Compose V2 Plugin
#
# Detects architecture automatically:
#   x86_64  → docker-compose-linux-x86_64   (conventional PC/server)
#   aarch64 → docker-compose-linux-aarch64  (ARM64: Raspberry Pi 4/5, AWS Graviton, Apple M*)
#   armv7l  → docker-compose-linux-armv7    (ARM 32-bit: older Raspberry Pi)
#
# Works as root (no sudo needed). Fixes docker-compose 1.29.2 + Python 3.12.
# ─────────────────────────────────────────────────────────────────────────────
set -e

COMPOSE_VERSION="v2.27.1"   # Stable fallback version

echo "🧠  Charlie — Docker Compose V2 Installer"
echo "─────────────────────────────────────────"

# ── Step 1: Detect architecture ─────────────────────────────────────────────
RAW_ARCH=$(uname -m)
echo "Detected hardware architecture: $RAW_ARCH"

case "$RAW_ARCH" in
    x86_64)
        ARCH_LABEL="x86_64"
        ARCH_DESC="Conventional PC/server (Intel/AMD 64-bit)"
        ;;
    aarch64 | arm64)
        ARCH_LABEL="aarch64"
        ARCH_DESC="ARM 64-bit (Raspberry Pi 4/5, AWS Graviton, Apple M-series)"
        ;;
    armv7l | armv7)
        ARCH_LABEL="armv7"
        ARCH_DESC="ARM 32-bit (older Raspberry Pi, embedded)"
        ;;
    i386 | i686)
        echo "❌  32-bit x86 is not supported by Docker Compose V2."
        echo "    Please use a 64-bit system."
        exit 1
        ;;
    *)
        echo "❌  Unknown architecture: $RAW_ARCH"
        echo "    Supported: x86_64, aarch64, armv7l"
        exit 1
        ;;
esac

echo "Architecture profile: $ARCH_DESC"
echo ""

# ── Step 2: Try apt first (cleanest method) ──────────────────────────────────
echo "Trying apt install (docker-compose-plugin)..."
if apt-get update -qq 2>/dev/null && apt-get install -y docker-compose-plugin 2>/dev/null; then
    echo ""
    echo "✅  docker-compose-plugin installed via apt."
    docker compose version
    exit 0
fi
echo "apt method unavailable, falling back to binary download."
echo ""

# ── Step 3: Download binary from GitHub ─────────────────────────────────────
# Try to get the latest stable release tag from GitHub API
echo "Fetching latest release version from GitHub..."
LATEST=$(curl -fsSL --connect-timeout 8 \
    "https://api.github.com/repos/docker/compose/releases/latest" 2>/dev/null \
    | grep '"tag_name"' | head -1 | cut -d'"' -f4)

# Validate: must start with "v" and look like a semver (e.g. v2.27.1)
if echo "$LATEST" | grep -qE '^v2\.[0-9]+\.[0-9]+$'; then
    COMPOSE_VERSION="$LATEST"
    echo "Latest release: $COMPOSE_VERSION"
else
    echo "Could not determine latest version (got: '$LATEST'), using fallback: $COMPOSE_VERSION"
fi

URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH_LABEL}"
DEST="/usr/local/lib/docker/cli-plugins"

echo ""
echo "Downloading Docker Compose V2:"
echo "  Version : $COMPOSE_VERSION"
echo "  Arch    : $ARCH_LABEL ($ARCH_DESC)"
echo "  URL     : $URL"
echo "  Dest    : $DEST/docker-compose"
echo ""

mkdir -p "$DEST"
curl -fsSL --progress-bar "$URL" -o "$DEST/docker-compose"
chmod +x "$DEST/docker-compose"

echo ""
echo "✅  Docker Compose V2 installed successfully!"
docker compose version
echo ""
echo "You can now run: bash start.sh"
