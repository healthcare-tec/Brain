#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Cognitive Operating System
# Startup script — handles Docker Compose V1 and V2 automatically
# ─────────────────────────────────────────────────────────────────────────────
set -e

COMPOSE_CMD=""

# Detect available compose command
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo ""
    echo "❌  Docker Compose not found."
    echo ""
    echo "Install it with one of the following commands:"
    echo ""
    echo "  # Ubuntu/Debian (recommended for Docker 28+):"
    echo "  sudo apt-get update && sudo apt-get install -y docker-compose-plugin"
    echo ""
    echo "  # Or install standalone docker-compose V1:"
    echo "  sudo apt-get install -y docker-compose"
    echo ""
    echo "  # Or install via pip:"
    echo "  pip install docker-compose"
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
