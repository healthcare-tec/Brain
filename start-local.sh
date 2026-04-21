#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Cognitive Operating System
# Local startup script (no Docker required)
# Works on: Ubuntu 22.04/24.04, proot-distro, bare-metal, VMs
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/.logs"
PID_DIR="$SCRIPT_DIR/.pids"

BACKEND_PORT=8085
FRONTEND_PORT=8080
DB_NAME="charlie"
DB_USER="charlie"
DB_PASS="charlie"
DB_HOST="localhost"
DB_PORT=5432

mkdir -p "$LOG_DIR" "$PID_DIR"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${BLUE}══ $* ══${NC}"; }

echo ""
echo -e "${BLUE}🧠  Charlie — Cognitive Operating System${NC}"
echo -e "${BLUE}    Local mode (no Docker required)${NC}"
echo ""

ACTION="${1:-start}"

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: check if a port is in use
# ─────────────────────────────────────────────────────────────────────────────
port_in_use() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " || \
    netstat -tlnp 2>/dev/null | grep -q ":$1 " || \
    lsof -i ":$1" &>/dev/null 2>&1
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Install system dependencies
# ─────────────────────────────────────────────────────────────────────────────
install_deps() {
    section "Installing system dependencies"

    # Python
    if ! command -v python3 &>/dev/null; then
        info "Installing Python 3..."
        apt-get update -qq && apt-get install -y python3 python3-pip python3-venv
    else
        ok "Python 3: $(python3 --version)"
    fi

    # pip
    if ! command -v pip3 &>/dev/null; then
        apt-get install -y python3-pip
    fi

    # Node.js
    if ! command -v node &>/dev/null; then
        info "Installing Node.js 20..."
        apt-get update -qq
        apt-get install -y curl
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    else
        ok "Node.js: $(node --version)"
    fi

    # PostgreSQL
    if ! command -v psql &>/dev/null; then
        info "Installing PostgreSQL..."
        apt-get update -qq && apt-get install -y postgresql postgresql-contrib
    else
        ok "PostgreSQL: $(psql --version)"
    fi

    # pnpm (optional, fallback to npm)
    if ! command -v pnpm &>/dev/null; then
        info "Installing pnpm..."
        npm install -g pnpm 2>/dev/null || warn "pnpm install failed, will use npm"
    else
        ok "pnpm: $(pnpm --version)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Setup PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────
setup_postgres() {
    section "Setting up PostgreSQL"

    # Try to start PostgreSQL (multiple methods for different environments)
    if command -v pg_ctlcluster &>/dev/null; then
        PG_VERSION=$(pg_lsclusters -h 2>/dev/null | awk '{print $1}' | head -1)
        PG_CLUSTER=$(pg_lsclusters -h 2>/dev/null | awk '{print $2}' | head -1)
        if [ -n "$PG_VERSION" ] && [ -n "$PG_CLUSTER" ]; then
            info "Starting PostgreSQL cluster $PG_VERSION/$PG_CLUSTER..."
            pg_ctlcluster "$PG_VERSION" "$PG_CLUSTER" start 2>/dev/null || true
        fi
    elif command -v service &>/dev/null; then
        info "Starting PostgreSQL via service..."
        service postgresql start 2>/dev/null || true
    fi

    # Wait for PostgreSQL to be ready
    info "Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 15); do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" &>/dev/null 2>&1; then
            ok "PostgreSQL is ready."
            break
        fi
        sleep 1
        if [ "$i" -eq 15 ]; then
            # Try starting manually as fallback
            warn "PostgreSQL not responding, trying manual start..."
            if command -v postgres &>/dev/null; then
                PGDATA="${PGDATA:-/var/lib/postgresql/data}"
                if [ ! -d "$PGDATA/base" ]; then
                    info "Initializing PostgreSQL data directory..."
                    mkdir -p "$PGDATA"
                    chown -R postgres:postgres "$PGDATA" 2>/dev/null || true
                    su -c "initdb -D $PGDATA" postgres 2>/dev/null || \
                    initdb -D "$PGDATA" 2>/dev/null || true
                fi
                su -c "pg_ctl -D $PGDATA -l $LOG_DIR/postgres.log start" postgres 2>/dev/null || \
                pg_ctl -D "$PGDATA" -l "$LOG_DIR/postgres.log" start 2>/dev/null || true
                sleep 3
            fi
        fi
    done

    # Create database and user
    info "Creating database '$DB_NAME' and user '$DB_USER'..."
    # Run as postgres superuser
    run_psql() {
        if id postgres &>/dev/null; then
            su -c "psql -c \"$1\"" postgres 2>/dev/null || \
            psql -U postgres -c "$1" 2>/dev/null || true
        else
            psql -c "$1" 2>/dev/null || true
        fi
    }

    run_psql "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
    run_psql "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
    run_psql "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
    ok "Database setup complete."
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Setup Python virtual environment and install backend deps
# ─────────────────────────────────────────────────────────────────────────────
setup_backend() {
    section "Setting up backend"

    cd "$BACKEND_DIR"

    # Create virtual environment
    if [ ! -d ".venv" ]; then
        info "Creating Python virtual environment..."
        python3 -m venv .venv
    fi

    # Activate venv
    source .venv/bin/activate

    info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt

    ok "Backend dependencies installed."

    # Create .env file
    cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_SYNC=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
KNOWLEDGE_BASE_PATH=${SCRIPT_DIR}/knowledge
DEBUG=true
EOF
    ok ".env file created."

    # Run migrations
    info "Running database migrations..."
    alembic upgrade head 2>&1 | tail -5 || warn "Migration warning (may already be applied)"
    ok "Migrations complete."

    deactivate
    cd "$SCRIPT_DIR"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Install frontend dependencies
# ─────────────────────────────────────────────────────────────────────────────
setup_frontend() {
    section "Setting up frontend"

    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        info "Installing frontend dependencies..."
        if command -v pnpm &>/dev/null; then
            pnpm install 2>&1 | tail -5
        else
            npm install 2>&1 | tail -5
        fi
    else
        ok "Frontend dependencies already installed."
    fi

    cd "$SCRIPT_DIR"
}

# ─────────────────────────────────────────────────────────────────────────────
# START: Launch backend and frontend
# ─────────────────────────────────────────────────────────────────────────────
start_services() {
    section "Starting services"

    # Backend
    if port_in_use "$BACKEND_PORT"; then
        warn "Port $BACKEND_PORT already in use — backend may already be running."
    else
        info "Starting backend on port $BACKEND_PORT..."
        cd "$BACKEND_DIR"
        source .venv/bin/activate
        DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        KNOWLEDGE_BASE_PATH="$SCRIPT_DIR/knowledge" \
        nohup uvicorn app.main:app \
            --host 0.0.0.0 \
            --port "$BACKEND_PORT" \
            --reload \
            > "$LOG_DIR/backend.log" 2>&1 &
        echo $! > "$PID_DIR/backend.pid"
        deactivate
        cd "$SCRIPT_DIR"
        sleep 2
        ok "Backend started (PID $(cat $PID_DIR/backend.pid))"
    fi

    # Frontend
    if port_in_use "$FRONTEND_PORT"; then
        warn "Port $FRONTEND_PORT already in use — frontend may already be running."
    else
        info "Starting frontend on port $FRONTEND_PORT..."
        cd "$FRONTEND_DIR"
        if command -v pnpm &>/dev/null; then
            nohup pnpm dev --host 0.0.0.0 --port "$FRONTEND_PORT" \
                > "$LOG_DIR/frontend.log" 2>&1 &
        else
            nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" \
                > "$LOG_DIR/frontend.log" 2>&1 &
        fi
        echo $! > "$PID_DIR/frontend.pid"
        cd "$SCRIPT_DIR"
        sleep 3
        ok "Frontend started (PID $(cat $PID_DIR/frontend.pid))"
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  Charlie is running!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  Frontend  →  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "  Backend   →  ${CYAN}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "  API Docs  →  ${CYAN}http://localhost:${BACKEND_PORT}/docs${NC}"
    echo ""
    echo -e "  CLI mode  →  ${CYAN}python3 charlie-cli.py${NC}"
    echo ""
    echo -e "  Logs      →  ${YELLOW}$LOG_DIR/${NC}"
    echo -e "  Stop      →  ${YELLOW}bash start-local.sh stop${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# STOP
# ─────────────────────────────────────────────────────────────────────────────
stop_services() {
    section "Stopping services"
    for svc in backend frontend; do
        PID_FILE="$PID_DIR/${svc}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID" && ok "$svc stopped (PID $PID)"
            else
                warn "$svc was not running."
            fi
            rm -f "$PID_FILE"
        fi
    done
}

# ─────────────────────────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────────────────────────
status_services() {
    section "Service status"
    for svc in backend frontend; do
        PID_FILE="$PID_DIR/${svc}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                ok "$svc is running (PID $PID)"
            else
                warn "$svc PID file exists but process is not running."
            fi
        else
            warn "$svc is not running."
        fi
    done
    echo ""
    info "Backend port $BACKEND_PORT: $(port_in_use $BACKEND_PORT && echo 'IN USE' || echo 'free')"
    info "Frontend port $FRONTEND_PORT: $(port_in_use $FRONTEND_PORT && echo 'IN USE' || echo 'free')"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
case "$ACTION" in
    install)
        install_deps
        setup_postgres
        setup_backend
        setup_frontend
        ok "Installation complete. Run: bash start-local.sh start"
        ;;
    start)
        # Auto-install if venv doesn't exist yet
        if [ ! -d "$BACKEND_DIR/.venv" ]; then
            info "First run detected — running full setup..."
            install_deps
            setup_postgres
            setup_backend
            setup_frontend
        fi
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 1
        start_services
        ;;
    status)
        status_services
        ;;
    logs)
        SVC="${2:-backend}"
        tail -f "$LOG_DIR/${SVC}.log"
        ;;
    migrate)
        cd "$BACKEND_DIR"
        source .venv/bin/activate
        DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        alembic upgrade head
        deactivate
        ;;
    setup)
        install_deps
        setup_postgres
        setup_backend
        setup_frontend
        ;;
    *)
        echo "Usage: bash start-local.sh [start|stop|restart|status|install|setup|logs|migrate]"
        echo ""
        echo "  start    — Start backend and frontend (auto-installs on first run)"
        echo "  stop     — Stop all services"
        echo "  restart  — Restart all services"
        echo "  status   — Show service status"
        echo "  install  — Install all dependencies and configure database"
        echo "  setup    — Same as install"
        echo "  logs     — Follow logs (default: backend). Use: logs frontend"
        echo "  migrate  — Run Alembic database migrations"
        ;;
esac
