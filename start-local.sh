#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Charlie — Cognitive Operating System
# Local startup script (no Docker, no PostgreSQL required)
# Database: SQLite (file-based, zero configuration)
# Works on: Ubuntu, proot-distro, bare-metal, VMs, Android Termux
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/.logs"
PID_DIR="$SCRIPT_DIR/.pids"

BACKEND_PORT=8085
FRONTEND_PORT=8080

# SQLite database file lives inside the backend directory
DB_FILE="$BACKEND_DIR/charlie.db"

mkdir -p "$LOG_DIR" "$PID_DIR"

# ── pip mirrors (tried in order until one works) ─────────────────────────────
PIP_MIRRORS=(
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://mirrors.ustc.edu.cn/pypi/simple/"
    "https://pypi.org/simple/"
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
echo -e "${BLUE}    SQLite mode (no server required)${NC}"
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
detect_venv_mode() {
    if [ -n "$CHARLIE_VENV_MODE" ]; then
        info "Using venv mode from environment: $CHARLIE_VENV_MODE"
        return
    fi

    if [ -d "$BACKEND_DIR/.venv" ]; then
        CHARLIE_VENV_MODE="create"
        return
    fi

    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Python environment setup${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

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
    echo -e "     ${YELLOW}→ Only if you manage packages globally${NC}"
    echo ""

    while true; do
        read -rp "  Your choice [1/2/3]: " VENV_CHOICE
        case "$VENV_CHOICE" in
            1)
                if [ -z "$VIRTUAL_ENV" ]; then
                    warn "No active venv found. Activate your venv first, then re-run."
                    read -rp "  Continue with system Python? [y/N]: " FALLBACK
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
    echo "CHARLIE_VENV_MODE=$CHARLIE_VENV_MODE" > "$SCRIPT_DIR/.charlie-env"
    info "Choice saved to .charlie-env (delete or run reset-venv to change)"
}

if [ -f "$SCRIPT_DIR/.charlie-env" ]; then
    source "$SCRIPT_DIR/.charlie-env"
fi

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: detect working pip mirror
# ─────────────────────────────────────────────────────────────────────────────
detect_pip_mirror() {
    if [ -n "$PIP_INDEX_URL" ]; then
        return
    fi
    info "Detecting accessible pip mirror..."
    local PIP_CMD="pip"
    command -v pip &>/dev/null || PIP_CMD="pip3"
    if [ "$CHARLIE_VENV_MODE" = "create" ] && [ -f "$BACKEND_DIR/.venv/bin/pip" ]; then
        PIP_CMD="$BACKEND_DIR/.venv/bin/pip"
    fi
    for mirror in "${PIP_MIRRORS[@]}"; do
        local HOST
        HOST=$(echo "$mirror" | sed 's|https\?://||;s|/.*||')
        if $PIP_CMD index versions pip \
            -i "$mirror" --trusted-host "$HOST" &>/dev/null 2>&1; then
            export PIP_INDEX_URL="$mirror"
            ok "Using pip mirror: $mirror"
            return
        fi
    done
    # Aliyun confirmed working — force it as last resort
    export PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
    warn "Mirror auto-detect failed — forcing Aliyun mirror."
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: pip install in the correct context
# ─────────────────────────────────────────────────────────────────────────────
pip_install() {
    local INDEX_ARGS=""
    if [ -n "$PIP_INDEX_URL" ]; then
        local HOST
        HOST=$(echo "$PIP_INDEX_URL" | sed 's|https\?://||;s|/.*||')
        INDEX_ARGS="-i $PIP_INDEX_URL --trusted-host $HOST"
    fi
    case "$CHARLIE_VENV_MODE" in
        existing) pip install --quiet $INDEX_ARGS "$@" ;;
        create)   "$BACKEND_DIR/.venv/bin/pip" install --quiet $INDEX_ARGS "$@" ;;
        system)
            pip3 install --quiet $INDEX_ARGS --break-system-packages "$@" 2>/dev/null || \
            pip3 install --quiet $INDEX_ARGS "$@"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: alembic in the correct context
# ─────────────────────────────────────────────────────────────────────────────
alembic_exec() {
    case "$CHARLIE_VENV_MODE" in
        existing) alembic "$@" ;;
        create)   "$BACKEND_DIR/.venv/bin/alembic" "$@" ;;
        system)   alembic "$@" ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Install system dependencies (Python + Node only)
# ─────────────────────────────────────────────────────────────────────────────
install_deps() {
    section "Installing system dependencies"

    if ! command -v python3 &>/dev/null; then
        info "Installing Python 3..."
        apt-get update -qq && apt-get install -y python3 python3-pip python3-venv
    else
        ok "Python 3: $(python3 --version)"
    fi

    if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
        apt-get install -y python3-pip
    fi

    if ! command -v node &>/dev/null; then
        info "Installing Node.js 20..."
        apt-get update -qq && apt-get install -y curl
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    else
        ok "Node.js: $(node --version)"
    fi

    if ! command -v pnpm &>/dev/null; then
        info "Installing pnpm..."
        npm install -g pnpm 2>/dev/null || warn "pnpm install failed, will use npm"
    else
        ok "pnpm: $(pnpm --version)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Setup Python environment and install backend deps
# ─────────────────────────────────────────────────────────────────────────────
setup_backend() {
    section "Setting up backend"

    cd "$BACKEND_DIR"

    detect_pip_mirror

    case "$CHARLIE_VENV_MODE" in
        existing)
            ok "Using active venv: $VIRTUAL_ENV"
            info "Installing Python dependencies..."
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

    # Write .env at PROJECT ROOT (Brain/.env) — config.py reads from there first
    _ROOT_ENV="${SCRIPT_DIR}/.env"
    if [ ! -f "${_ROOT_ENV}" ]; then
        printf 'DATABASE_URL=sqlite+aiosqlite://%s\n' "/${DB_FILE}" > "${_ROOT_ENV}"
        printf 'DATABASE_URL_SYNC=sqlite:///%s\n' "${DB_FILE}" >> "${_ROOT_ENV}"
        printf 'KNOWLEDGE_BASE_PATH=%s\n' "${SCRIPT_DIR}/knowledge" >> "${_ROOT_ENV}"
        printf 'DEBUG=false\n' >> "${_ROOT_ENV}"
        ok ".env created at project root: ${_ROOT_ENV}"
        info "To enable AI features, add: OPENAI_API_KEY=sk-... to ${_ROOT_ENV}"
    else
        ok ".env already exists at project root: ${_ROOT_ENV}"
    fi

    # Run Alembic migrations
    info "Running database migrations..."
    alembic_exec upgrade head 2>&1 | tail -5 || warn "Migration warning (may already be applied)"
    ok "Migrations complete. Database: $DB_FILE"

    cd "$SCRIPT_DIR"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Install frontend dependencies
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
# START services
# ─────────────────────────────────────────────────────────────────────────────
start_services() {
    section "Starting services"

    # Backend
    if port_in_use "$BACKEND_PORT"; then
        warn "Port $BACKEND_PORT already in use — backend may already be running."
    else
        info "Starting backend on port $BACKEND_PORT..."
        cd "$BACKEND_DIR"

        local UVICORN_CMD="uvicorn"
        if [ "$CHARLIE_VENV_MODE" = "create" ] && [ -f "$BACKEND_DIR/.venv/bin/uvicorn" ]; then
            UVICORN_CMD="$BACKEND_DIR/.venv/bin/uvicorn"
        elif [ "$CHARLIE_VENV_MODE" = "existing" ] && [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/uvicorn" ]; then
            UVICORN_CMD="$VIRTUAL_ENV/bin/uvicorn"
        fi

        # Load ALL variables from Brain/.env into the current shell environment
        # so they are inherited by the nohup subprocess (including OPENAI_API_KEY)
        if [ -f "${SCRIPT_DIR}/.env" ]; then
            set -a
            # shellcheck disable=SC1090
            source "${SCRIPT_DIR}/.env"
            set +a
            ok "Loaded Brain/.env into backend environment"
        fi
        # Ensure SQLite vars are always set (override any stale DATABASE_URL from .env)
        export DATABASE_URL="sqlite+aiosqlite:///${DB_FILE}"
        export DATABASE_URL_SYNC="sqlite:///${DB_FILE}"
        export KNOWLEDGE_BASE_PATH="$SCRIPT_DIR/knowledge"

        # ── Extra safety: explicitly extract OPENAI_API_KEY from .env and export it
        # This handles cases where `source` fails silently (e.g. lines with `export KEY=val`)
        if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "${SCRIPT_DIR}/.env" ]; then
            _RAW_KEY=$(grep -E '^[[:space:]]*OPENAI_API_KEY[[:space:]]*=' "${SCRIPT_DIR}/.env" \
                | head -1 | sed 's/^[^=]*=//;s/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//;s/^'\''/;s/'\''//')
            if [ -n "$_RAW_KEY" ]; then
                export OPENAI_API_KEY="$_RAW_KEY"
                ok "OPENAI_API_KEY extracted directly from Brain/.env (fallback method)"
            fi
        fi
        if [ -n "${OPENAI_API_KEY:-}" ]; then
            ok "OPENAI_API_KEY is set (${#OPENAI_API_KEY} chars) — AI features enabled"
        else
            warn "OPENAI_API_KEY not found — AI features will be disabled"
            warn "Add OPENAI_API_KEY=sk-... to ${SCRIPT_DIR}/.env to enable AI"
        fi

        nohup $UVICORN_CMD app.main:app \
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
        # Use 127.0.0.1 (not 0.0.0.0) to avoid proot-distro uv_interface_addresses error
        if command -v pnpm &>/dev/null; then
            nohup pnpm dev --host 127.0.0.1 --port "$FRONTEND_PORT" \
                > "$LOG_DIR/frontend.log" 2>&1 &
        else
            nohup npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" \
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
    echo -e "  Database  →  ${CYAN}${DB_FILE}${NC}"
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
    info "Database: $DB_FILE"
    [ -f "$DB_FILE" ] && ok "Database file exists ($(du -sh "$DB_FILE" | cut -f1))" || warn "Database file not found (run: bash start-local.sh migrate)"
    echo ""
    if [ -n "$CHARLIE_VENV_MODE" ]; then
        info "Python venv mode: $CHARLIE_VENV_MODE"
        case "$CHARLIE_VENV_MODE" in
            existing) info "Active venv: ${VIRTUAL_ENV:-'(not detected in this shell)'}" ;;
            create)   info "venv path: $BACKEND_DIR/.venv" ;;
            system)   info "System Python: $(python3 --version 2>/dev/null)" ;;
        esac
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
case "$ACTION" in
    install|setup)
        detect_venv_mode
        install_deps
        setup_backend
        setup_frontend
        ok "Installation complete. Run: bash start-local.sh start"
        ;;
    start)
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
        alembic_exec upgrade head
        ok "Migrations applied. Database: $DB_FILE"
        ;;
    reset-venv)
        rm -f "$SCRIPT_DIR/.charlie-env"
        ok "venv choice reset. Next 'start' will ask again."
        ;;
    *)
        echo ""
        echo -e "  ${CYAN}Usage:${NC} bash start-local.sh [command]"
        echo ""
        echo -e "  ${GREEN}start${NC}       Start backend and frontend (asks about venv on first run)"
        echo -e "  ${GREEN}stop${NC}        Stop all services"
        echo -e "  ${GREEN}restart${NC}     Restart all services"
        echo -e "  ${GREEN}status${NC}      Show service status and database info"
        echo -e "  ${GREEN}install${NC}     Install all dependencies"
        echo -e "  ${GREEN}logs${NC}        Follow logs (default: backend). Use: logs frontend"
        echo -e "  ${GREEN}migrate${NC}     Run Alembic database migrations"
        echo -e "  ${GREEN}reset-venv${NC}  Reset the saved venv choice"
        echo ""
        echo -e "  ${YELLOW}Skip the venv prompt:${NC}"
        echo -e "    CHARLIE_VENV_MODE=existing bash start-local.sh  # use active venv (e.g. jupenv)"
        echo -e "    CHARLIE_VENV_MODE=create   bash start-local.sh  # create backend/.venv"
        echo -e "    CHARLIE_VENV_MODE=system   bash start-local.sh  # use system Python"
        echo ""
        ;;
esac
