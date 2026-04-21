#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Cognitive Operating System
# Startup script — handles Docker Compose V1 and V2 automatically
# Works as root (no sudo needed)
# ─────────────────────────────────────────────────────────────────────────────
set -e

COMPOSE_CMD=""

# Detect available compose command
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    # Test if docker-compose V1 actually works (broken on Python 3.12)
    if docker-compose version &>/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        echo ""
        echo "❌  docker-compose is installed but broken (Python 3.12 incompatibility)."
        echo "    Run: bash install-compose.sh"
        echo ""
        exit 1
    fi
else
    echo ""
    echo "❌  Docker Compose not found."
    echo "    Run: bash install-compose.sh"
    echo ""
    exit 1
fi

echo "🧠  Charlie — Cognitive Operating System"
echo "Using: $COMPOSE_CMD"
echo ""

ACTION="${1:-up}"

case "$ACTION" in
    up)
        echo "▶  Starting all services..."
        $COMPOSE_CMD up --build "${@:2}"
        ;;
    down)
        echo "■  Stopping all services..."
        $COMPOSE_CMD down "${@:2}"
        ;;
    restart)
        echo "↺  Restarting all services..."
        $COMPOSE_CMD down
        $COMPOSE_CMD up --build
        ;;
    logs)
        $COMPOSE_CMD logs -f "${@:2}"
        ;;
    migrate)
        echo "⚙  Running database migrations..."
        $COMPOSE_CMD exec backend alembic upgrade head
        ;;
    test)
        echo "🧪  Running backend tests..."
        $COMPOSE_CMD exec backend python -m pytest tests/ -v
        ;;
    *)
        $COMPOSE_CMD "$@"
        ;;
esac
