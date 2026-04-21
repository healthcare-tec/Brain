# 🧠 Charlie — Cognitive Operating System

Charlie is a personal **Cognitive Operating System** — a stand-alone system designed to capture inputs instantly, organize execution (GTD), structure knowledge (Second Brain / PARA), support deep thinking (System 2), and build a feedback loop over time.

Charlie is not a task manager. It is a system for **thinking, deciding, and improving over time**.

> **Stand-alone:** runs without Docker, without PostgreSQL, without external services. The database is SQLite — a single local file. Works on Ubuntu, proot-distro, Termux, VMs, and bare-metal servers.

---

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Python 3.10+ | REST API, business logic, event system |
| **Database** | SQLite (aiosqlite) | Tasks, projects, events, decision logs, note metadata |
| **Knowledge** | Markdown filesystem (PARA) | Notes, thinking documents, knowledge base |
| **Frontend** | React 18 + Tailwind CSS | Full web UI for all modules |
| **Migrations** | Alembic | Database schema versioning |
| **CLI** | Python (built-in) | Terminal interface — all modules, no browser needed |

---

## Core Modules

### 1. Capture Engine (Inbox)
Frictionless input — capture tasks, ideas, notes without any structure required. Everything lands in the Inbox first.

### 2. Clarification Engine (GTD)
Process inbox items into actionable tasks, projects, knowledge notes, or trash. Each item must answer: *Is it actionable? What is the next physical action?*

### 3. Task System
GTD execution layer with statuses: **Next**, **Waiting**, **Someday**, **Done**. Supports context-based filtering (`@work`, `@home`, `@computer`), time estimation, and priority levels.

### 4. Task Completion System
Mark tasks as DONE with execution metadata (estimated vs actual time, context, project). Turns execution into feedback data.

### 5. Knowledge System (Second Brain / PARA)
Markdown-based knowledge base organized by the PARA method: **Projects**, **Areas**, **Resources**, **Archive**. Human-readable and portable.

### 6. Thinking Engine (System 2)
Structured reasoning through Decision Logs, Risk Analysis, and Problem Breakdown templates. Each thinking note includes context, hypotheses, options, decision, and expected outcome.

### 7. Memory Palace (stub)
Semantic indexing and context-aware retrieval. Prepared with interfaces for future integration.

### 8. AI Cognitive Layer (stub)
Three levels: Classification (L1), Interpretation (L2), Analysis (L3). Prepared with stubs for future LLM integration.

### 9. Feedback System
Weekly review dashboard with metrics: pending inbox, completed tasks, next actions, project progress, and time estimation accuracy.

---

## Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm` or `pnpm`
- No database server required (SQLite is a local file)

---

## Quick Start

```bash
git clone https://github.com/healthcare-tec/Brain.git
cd Brain
```

### Install missing Python packages

If you are using an existing venv (e.g. **jupenv**):

```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r backend/requirements-missing.txt
```

To install all Python dependencies from scratch:

```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r backend/requirements.txt
```

### Start Charlie

```bash
bash start-local.sh
```

On first run, the script asks which Python environment to use, installs dependencies, creates the SQLite database, runs migrations, and starts both services.

**Access the system:**
- Frontend UI → http://localhost:8080
- Backend API → http://localhost:8085
- Swagger UI  → http://localhost:8085/docs

---

## Configuration (`Brain/.env`)

All configuration lives in a single `.env` file at the **project root** (`Brain/.env`). This file is protected by `.gitignore` and will never be committed.

```bash
# Create your .env from the example template
cp .env.example .env
```

The only setting you need to add manually is the OpenAI API key to enable AI features:

```ini
# Brain/.env
OPENAI_API_KEY=sk-your-key-here
```

All other settings (database path, knowledge base path) are auto-detected and do not need to be set manually. The backend reads `Brain/.env` first; if not found, falls back to `Brain/backend/.env` for compatibility.

---

## Script commands

```bash
bash start-local.sh start          # Start backend and frontend
bash start-local.sh stop           # Stop all services
bash start-local.sh restart        # Restart all services
bash start-local.sh status         # Show status + database info
bash start-local.sh logs           # Follow backend logs
bash start-local.sh logs frontend  # Follow frontend logs
bash start-local.sh migrate        # Run Alembic migrations manually
bash start-local.sh reset-venv     # Reset saved venv choice
```

Skip the venv prompt:

```bash
CHARLIE_VENV_MODE=existing bash start-local.sh   # use active venv (e.g. jupenv)
CHARLIE_VENV_MODE=create   bash start-local.sh   # create backend/.venv
CHARLIE_VENV_MODE=system   bash start-local.sh   # use system Python
```

---

## CLI Mode

Charlie includes a full interactive command-line interface covering all modules. Use it when the browser is not available or when you prefer terminal interaction.

```bash
# Backend must be running first
bash start-local.sh start

# Then launch the CLI
python3 charlie-cli.py
```

| Module | Description |
|--------|-------------|
| **Quick Capture** | Instantly add anything to inbox (frictionless) |
| **Inbox** | Process inbox with GTD clarification (task / project / note / trash) |
| **Tasks** | View next actions, add tasks, mark as DONE with metadata |
| **Projects** | Create and manage projects, view tasks per project |
| **Thinking** | Create Decision Logs, Risk Analysis, Problem Breakdowns |
| **Knowledge** | Create and browse PARA notes (projects / areas / resources / archive) |
| **Weekly Review** | Metrics dashboard + interactive review checklist |

Typical workflow:

```
1. Quick Capture  →  dump everything on your mind into inbox
2. Inbox          →  clarify each item (is it actionable?)
3. Tasks          →  work through next actions, mark done
4. Weekly Review  →  reflect, adjust, plan ahead
```

---

## Database

Charlie uses **SQLite** — a local file, no server, no configuration.

```
backend/charlie.db    ← database (created automatically on first run)
knowledge/            ← Markdown files (PARA structure)
```

Inspect the database directly:

```bash
sqlite3 backend/charlie.db ".tables"
sqlite3 backend/charlie.db "SELECT * FROM inbox_items LIMIT 5;"
```

Backup:

```bash
cp backend/charlie.db backend/charlie.db.bak
```

---

## Manual Setup (step by step)

If you prefer to set up each component manually:

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Run migrations (creates charlie.db automatically)
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

### Frontend

```bash
cd frontend
npm install        # or: pnpm install
npm run dev -- --host 0.0.0.0 --port 8080
```

### Run tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
Brain/
├── README.md                    # This file
├── .env                         # Your configuration (copy from .env.example — never committed)
├── .env.example                 # Configuration template
├── start-local.sh               # Local startup script (no Docker required)
├── charlie-cli.py               # Interactive CLI (all modules)
├── backend/
│   ├── requirements.txt         # All Python dependencies
│   ├── requirements-missing.txt # Only packages missing from jupenv
│   ├── charlie.db               # SQLite database (created on first run)
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py              # FastAPI application
│       ├── config.py            # Settings (env vars, SQLite defaults)
│       ├── database.py          # Async SQLAlchemy engine (SQLite/aiosqlite)
│       ├── models/              # ORM models (String-based enums, SQLite-compatible)
│       ├── schemas/             # Pydantic schemas
│       ├── api/                 # FastAPI routers
│       ├── services/            # Business logic
│       ├── events/              # Event emitter
│       └── ai/                  # AI stubs (L1 Classification, L2 Interpretation, L3 Analysis)
├── frontend/
│   └── src/
│       ├── pages/               # Inbox, Tasks, Projects, Thinking, Notes, Review
│       ├── components/          # Layout, QuickCapture, TaskCard, modals
│       └── services/api.js      # API client
├── knowledge/                   # PARA structure (Markdown files)
│   ├── projects/
│   ├── areas/
│   ├── resources/
│   └── archive/
└── docs/
    └── architecture.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/inbox/` | Capture a new item |
| `GET` | `/api/inbox/` | List inbox items |
| `POST` | `/api/inbox/{id}/clarify` | Clarify item (task/project/note/trash) |
| `POST` | `/api/tasks/` | Create a task |
| `GET` | `/api/tasks/` | List tasks (filter by status/project/context) |
| `PATCH` | `/api/tasks/{id}` | Update a task |
| `POST` | `/api/tasks/{id}/complete` | Mark task as DONE with metadata |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `POST` | `/api/projects/` | Create a project |
| `GET` | `/api/projects/` | List projects with task counts |
| `PATCH` | `/api/projects/{id}` | Update a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
| `POST` | `/api/decision-logs/` | Create a thinking note |
| `GET` | `/api/decision-logs/` | List decision logs |
| `POST` | `/api/notes/` | Create a note (DB + Markdown) |
| `GET` | `/api/notes/` | List notes (filter by PARA category) |
| `GET` | `/api/reviews/weekly` | Weekly review summary |
| `GET` | `/api/events/` | List system events |
| `POST` | `/api/ai/classify` | AI classification (stub) |
| `POST` | `/api/ai/interpret` | AI interpretation (stub) |
| `GET` | `/api/ai/patterns` | AI pattern detection (stub) |
| `GET` | `/health` | Health check |

Full interactive API documentation: `http://localhost:8085/docs`

---

## Philosophy

> Charlie is an external System 2.
>
> SQLite stores what you do.
> Markdown stores what you think.
> Memory Palace surfaces what matters.
> AI helps you see what you would miss.
>
> The goal is not automation.
> **The goal is better thinking.**
