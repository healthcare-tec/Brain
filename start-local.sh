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

# ── pip mirrors (tried in order until one works) ────────────────────────────
PIP_MIRRORS=(
    "https://mirrors.aliyun.com/pypi/simple/"       # Aliyun (China CDN, global)
    "https://pypi.tuna.tsinghua.edu.cn/simple/"     # Tsinghua University
    "https://mirrors.ustc.edu.cn/pypi/simple/"      # USTC
    "https://pypi.org/simple/"                      # Official (may be blocked)
)

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
# VENV STRATEGY: ask user or detect automatically
# ─────────────────────────────────────────────────────────────────────────────
# Possible values for CHARLIE_VENV_MODE:
#   "existing"  — use the currently active venv (VIRTUAL_ENV must be set)
#   "create"    — create a new venv at backend/.venv
#   "system"    — use system Python directly (no venv)
# Can be set as environment variable to skip the prompt:
#   CHARLIE_VENV_MODE=existing bash start-local.sh

detect_venv_mode() {
    # If already set via env var, respect it
    if [ -n "$CHARLIE_VENV_MODE" ]; then
        info "Using venv mode from environment: $CHARLIE_VENV_MODE"
        return
    fi

    # If backend/.venv already exists, skip the question
    if [ -d "$BACKEND_DIR/.venv" ]; then
        CHARLIE_VENV_MODE="create"
        return
    fi

    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Python environment setup${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Show current Python context
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "  ${GREEN}Active venv detected:${NC} $VIRTUAL_ENV"
        echo -e "  ${CYAN}Python:${NC} $(python3 --version 2>/dev/null || echo 'unknown')"
    else
        echo -e "  ${CYAN}System Python:${NC} $(python3 --version 2>/dev/null || echo 'not found')"
        echo -e "  No active virtual environment detected."
    fi

    echo ""
    echo -e "  How should Charlie install its Python dependencies?"
    echo ""
    echo -e "  ${CYAN}1${NC}  Use the ${GREEN}currently active venv${NC} (e.g. jupenv)"
    echo -e "     ${YELLOW}→ Recommended if you are already inside a venv${NC}"
    echo ""
    echo -e "  ${CYAN}2${NC}  Create a ${GREEN}new dedicated venv${NC} at backend/.venv"
    echo -e "     ${YELLOW}→ Isolated environment, won't affect your current setup${NC}"
    echo ""
    echo -e "  ${CYAN}3${NC}  Use ${GREEN}system Python${NC} directly (no venv)"
    echo -e "     ${YELLOW}→ Only if you manage packages globally (e.g. pip install --break-system-packages)${NC}"
    echo ""

    while true; do
        read -rp "  Your choice [1/2/3]: " VENV_CHOICE
        case "$VENV_CHOICE" in
            1)
                if [ -z "$VIRTUAL_ENV" ]; then
                    warn "No active venv found (\$VIRTUAL_ENV is not set)."
                    warn "Please activate your venv first, then re-run this script."
                    warn "Example: source /path/to/jupenv/bin/activate"
                    echo ""
                    read -rp "  Continue anyway with system Python? [y/N]: " FALLBACK
                    if [[ "$FALLBACK" =~ ^[Yy]$ ]]; then
                        CHARLIE_VENV_MODE="system"
                    else
                        exit 1
                    fi
                else
                    CHARLIE_VENV_MODE="existing"
                    ok "Will use active venv: $VIRTUAL_ENV"
                fi
                break
                ;;
            2)
                CHARLIE_VENV_MODE="create"
                ok "Will create a new venv at backend/.venv"
                break
                ;;
            3)
                CHARLIE_VENV_MODE="system"
                warn "Using system Python — packages will be installed globally."
                break
                ;;
            *)
                warn "Please enter 1, 2, or 3."
                ;;
        esac
    done

    echo ""
    # Save choice for subsequent runs (so the question is not asked again)
    echo "CHARLIE_VENV_MODE=$CHARLIE_VENV_MODE" > "$SCRIPT_DIR/.charlie-env"
    info "Choice saved to .charlie-env (delete this file to reset)"
}

# Load saved choice if it exists
if [ -f "$SCRIPT_DIR/.charlie-env" ]; then
    source "$SCRIPT_DIR/.charlie-env"
fi

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: run pip in the correct context
# ─────────────────────────────────────────────────────────────────────────────
# Detect a working pip mirror
detect_pip_mirror() {
    if [ -n "$PIP_INDEX_URL" ]; then
        return  # already set by user
    fi
    info "Detecting accessible pip mirror..."
    for mirror in "${PIP_MIRRORS[@]}"; do
        if curl -sf --max-time 5 "$mirror" -o /dev/null 2>/dev/null; then
            export PIP_INDEX_URL="$mirror"
            ok "Using pip mirror: $mirror"
            return
        fi
    done
    warn "No pip mirror responded. Install may fail if PyPI is blocked."
}

pip_install() {
    local INDEX_ARGS=""
    if [ -n "$PIP_INDEX_URL" ]; then
        INDEX_ARGS="-i $PIP_INDEX_URL --trusted-host $(echo $PIP_INDEX_URL | sed 's|https\?://||;s|/.*||')"
    fi
    case "$CHARLIE_VENV_MODE" in
        existing)
            pip install --quiet $INDEX_ARGS "$@"
            ;;
        create)
            "$BACKEND_DIR/.venv/bin/pip" install --quiet $INDEX_ARGS "$@"
            ;;
        system)
            pip3 install --quiet $INDEX_ARGS --break-system-packages "$@" 2>/dev/null || \
            pip3 install --quiet $INDEX_ARGS "$@"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: run a Python command in the correct context
# ─────────────────────────────────────────────────────────────────────────────
python_exec() {
    case "$CHARLIE_VENV_MODE" in
        existing)
            python3 "$@"
            ;;
        create)
            "$BACKEND_DIR/.venv/bin/python3" "$@"
            ;;
        system)
            python3 "$@"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: run uvicorn in the correct context
# ─────────────────────────────────────────────────────────────────────────────
uvicorn_exec() {
    case "$CHARLIE_VENV_MODE" in
        existing)
            uvicorn "$@"
            ;;
        create)
            "$BACKEND_DIR/.venv/bin/uvicorn" "$@"
            ;;
        system)
            uvicorn "$@"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: run alembic in the correct context
# ─────────────────────────────────────────────────────────────────────────────
alembic_exec() {
    case "$CHARLIE_VENV_MODE" in
        existing)
            alembic "$@"
            ;;
        create)
            "$BACKEND_DIR/.venv/bin/alembic" "$@"
            ;;
        system)
            alembic "$@"
            ;;
    esac
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
# STEP 3: Setup Python environment and install backend deps
# ─────────────────────────────────────────────────────────────────────────────
setup_backend() {
    section "Setting up backend"

    cd "$BACKEND_DIR"

    detect_pip_mirror

    case "$CHARLIE_VENV_MODE" in
        existing)
            ok "Using active venv: $VIRTUAL_ENV"
            info "Installing Python dependencies into active venv..."
            pip_install --upgrade pip
            pip_install -r requirements.txt
            ;;
        create)
            if [ ! -d ".venv" ]; then
                info "Creating Python virtual environment at backend/.venv..."
                python3 -m venv .venv
                ok "venv created."
            else
                ok "venv already exists at backend/.venv"
            fi
            info "Installing Python dependencies..."
            pip_install --upgrade pip
            pip_install -r requirements.txt
            ;;
        system)
            info "Installing Python dependencies into system Python..."
            pip_install --upgrade pip 2>/dev/null || true
            pip_install -r requirements.txt
            ;;
    esac

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
    DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
    alembic_exec upgrade head 2>&1 | tail -5 || warn "Migration warning (may already be applied)"
    ok "Migrations complete."

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
        DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        KNOWLEDGE_BASE_PATH="$SCRIPT_DIR/knowledge" \
        nohup $(
            case "$CHARLIE_VENV_MODE" in
                create) echo "$BACKEND_DIR/.venv/bin/uvicorn" ;;
                *)       echo "uvicorn" ;;
            esac
        ) app.main:app \
            --host 0.0.0.0 \
            --port "$BACKEND_PORT" \
            --reload \
            > "$LOG_DIR/backend.log" 2>&1 &
        echo $! > "$PID_DIR/backend.pid"
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
    echo ""
    if [ -n "$CHARLIE_VENV_MODE" ]; then
        info "Python venv mode: $CHARLIE_VENV_MODE"
        case "$CHARLIE_VENV_MODE" in
            existing) info "Active venv: ${VIRTUAL_ENV:-'(not detected in this shell)'}" ;;
            create)   info "venv path: $BACKEND_DIR/.venv" ;;
            system)   info "Using system Python: $(python3 --version 2>/dev/null)" ;;
        esac
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# RESET venv choice
# ─────────────────────────────────────────────────────────────────────────────
reset_venv_choice() {
    if [ -f "$SCRIPT_DIR/.charlie-env" ]; then
        rm -f "$SCRIPT_DIR/.charlie-env"
        ok "venv choice reset. Next 'start' will ask again."
    else
        info "No saved venv choice found."
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
case "$ACTION" in
    install|setup)
        detect_venv_mode
        install_deps
        setup_postgres
        setup_backend
        setup_frontend
        ok "Installation complete. Run: bash start-local.sh start"
        ;;
    start)
        # Auto-install on first run (no venv exists yet and no saved choice)
        NEEDS_SETUP=false
        if [ "$CHARLIE_VENV_MODE" = "create" ] && [ ! -d "$BACKEND_DIR/.venv" ]; then
            NEEDS_SETUP=true
        elif [ -z "$CHARLIE_VENV_MODE" ]; then
            NEEDS_SETUP=true
        fi

        if [ "$NEEDS_SETUP" = "true" ]; then
            info "First run detected — running full setup..."
            detect_venv_mode
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
        if [ -z "$CHARLIE_VENV_MODE" ] && [ -f "$SCRIPT_DIR/.charlie-env" ]; then
            source "$SCRIPT_DIR/.charlie-env"
        fi
        cd "$BACKEND_DIR"
        DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        alembic_exec upgrade head
        ;;
    reset-venv)
        reset_venv_choice
        ;;
    *)
        echo ""
        echo -e "  ${CYAN}Usage:${NC} bash start-local.sh [command]"
        echo ""
        echo -e "  ${GREEN}start${NC}       Start backend and frontend (asks about venv on first run)"
        echo -e "  ${GREEN}stop${NC}        Stop all services"
        echo -e "  ${GREEN}restart${NC}     Restart all services"
        echo -e "  ${GREEN}status${NC}      Show service status and venv info"
        echo -e "  ${GREEN}install${NC}     Install all dependencies and configure database"
        echo -e "  ${GREEN}logs${NC}        Follow logs (default: backend). Use: logs frontend"
        echo -e "  ${GREEN}migrate${NC}     Run Alembic database migrations"
        echo -e "  ${GREEN}reset-venv${NC}  Reset the saved venv choice (will ask again on next start)"
        echo ""
        echo -e "  ${YELLOW}Venv modes (set via env var to skip the prompt):${NC}"
        echo -e "    CHARLIE_VENV_MODE=existing bash start-local.sh  # use active venv (e.g. jupenv)"
        echo -e "    CHARLIE_VENV_MODE=create   bash start-local.sh  # create backend/.venv"
        echo -e "    CHARLIE_VENV_MODE=system   bash start-local.sh  # use system Python"
        echo ""
        ;;
esac
