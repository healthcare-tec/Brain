# 🧠 Charlie — Cognitive Operating System

Charlie is a personal **Cognitive Operating System** — a stand-alone system designed to capture inputs instantly, organize execution (GTD), structure knowledge (Second Brain / PARA), support deep thinking (System 2), and build a feedback loop over time.

Charlie is not a task manager. It is a system for **thinking, deciding, and improving over time**.

---

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Python 3.11 | REST API, business logic, event system |
| **Database** | PostgreSQL | Tasks, projects, events, decision logs, note metadata |
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

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+

> On Ubuntu/Debian, install all prerequisites with:
> ```bash
> apt-get update && apt-get install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib
> ```

### Start Charlie (first run)

```bash
git clone https://github.com/healthcare-tec/Brain.git
cd Brain

# First run: installs deps, configures database, starts everything
bash start-local.sh
```

The script will:
1. Create a Python virtual environment in `backend/.venv`
2. Install all Python dependencies
3. Start PostgreSQL and create the `charlie` database
4. Run Alembic migrations
5. Install frontend dependencies
6. Start backend on **port 8085** and frontend on **port 8080** in background

**Access the system:**
- Frontend UI → http://localhost:8080
- Backend API → http://localhost:8085
- Swagger UI  → http://localhost:8085/docs

### Subsequent runs

```bash
bash start-local.sh start
```

### All commands

```bash
bash start-local.sh start    # Start all services
bash start-local.sh stop     # Stop all services
bash start-local.sh restart  # Restart all services
bash start-local.sh status   # Show running status
bash start-local.sh logs     # Follow backend logs
bash start-local.sh logs frontend  # Follow frontend logs
bash start-local.sh migrate  # Run Alembic migrations manually
```

---

## CLI Mode

Charlie includes a full interactive command-line interface that covers all modules. Use it when the browser is not available or when you prefer terminal interaction.

### Start the CLI

```bash
# Backend must be running first
bash start-local.sh start

# Then launch the CLI
python3 charlie-cli.py
```

### CLI modules

| Module | Description |
|--------|-------------|
| **Quick Capture** | Instantly add anything to inbox (frictionless) |
| **Inbox** | Process inbox with GTD clarification (task / project / note / trash) |
| **Tasks** | View next actions, add tasks, mark as DONE with metadata |
| **Projects** | Create and manage projects, view tasks per project |
| **Thinking** | Create Decision Logs, Risk Analysis, Problem Breakdowns |
| **Knowledge** | Create and browse PARA notes (projects / areas / resources / archive) |
| **Weekly Review** | Metrics dashboard + interactive review checklist |

### Typical workflow

```
1. Quick Capture  →  dump everything on your mind into inbox
2. Inbox          →  clarify each item (is it actionable?)
3. Tasks          →  work through next actions, mark done
4. Weekly Review  →  reflect, adjust, plan ahead
```

---

## Manual Setup (step by step)

If you prefer to set up each component manually:

### 1. PostgreSQL

```bash
# Start PostgreSQL
service postgresql start   # or: pg_ctlcluster <version> main start

# Create database and user
psql -U postgres -c "CREATE USER charlie WITH PASSWORD 'charlie';"
psql -U postgres -c "CREATE DATABASE charlie OWNER charlie;"
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment variables
export DATABASE_URL="postgresql+asyncpg://charlie:charlie@localhost:5432/charlie"
export DATABASE_URL_SYNC="postgresql://charlie:charlie@localhost:5432/charlie"
export KNOWLEDGE_BASE_PATH="../knowledge"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

### 3. Frontend

```bash
cd frontend
npm install        # or: pnpm install
npm run dev -- --host 0.0.0.0 --port 8080
```

### 4. Run tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

---

## Project Structure

```
Brain/
├── README.md                    # This file
├── start-local.sh               # Local startup script
├── charlie-cli.py               # Interactive CLI (all modules)
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── models/              # ORM models
│   │   │   ├── inbox.py         # Capture Engine
│   │   │   ├── task.py          # Task System
│   │   │   ├── project.py       # Project management
│   │   │   ├── event.py         # Event System
│   │   │   ├── decision_log.py  # Thinking Engine
│   │   │   └── note.py          # Knowledge System
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # FastAPI routers
│   │   │   ├── inbox.py         # POST /api/inbox, POST /api/inbox/{id}/clarify
│   │   │   ├── tasks.py         # CRUD + POST /api/tasks/{id}/complete
│   │   │   ├── projects.py      # CRUD with task counts
│   │   │   ├── decision_logs.py # CRUD for thinking notes
│   │   │   ├── notes.py         # CRUD (DB + Markdown)
│   │   │   ├── reviews.py       # GET /api/reviews/weekly
│   │   │   ├── events.py        # GET /api/events
│   │   │   └── ai.py            # AI stubs
│   │   ├── services/            # Business logic
│   │   ├── events/              # Event emitter
│   │   └── ai/                  # AI stubs (L1, L2, L3)
│   └── tests/
│       ├── conftest.py          # Test config (SQLite in-memory)
│       └── test_api.py          # API endpoint tests
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx              # Router setup
│       ├── index.css            # Tailwind CSS
│       ├── components/
│       │   ├── Layout.jsx       # Sidebar navigation
│       │   ├── QuickCapture.jsx # Frictionless input
│       │   ├── ClarifyModal.jsx # GTD clarification
│       │   ├── TaskCard.jsx     # Task with quick Done
│       │   └── TaskFormModal.jsx
│       ├── pages/
│       │   ├── InboxPage.jsx    # Capture + Clarify
│       │   ├── TasksPage.jsx    # Next Actions
│       │   ├── ProjectsPage.jsx # Project Dashboard
│       │   ├── ThinkingPage.jsx # Decision Logs
│       │   ├── NotesPage.jsx    # Knowledge Base (PARA)
│       │   └── ReviewPage.jsx   # Weekly Review
│       └── services/
│           └── api.js           # API client
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

Full interactive API documentation is available at `http://localhost:8085/docs` (Swagger UI).

---

## Philosophy

> Charlie is an external System 2.
>
> PostgreSQL stores what you do.
> Markdown stores what you think.
> Memory Palace surfaces what matters.
> AI helps you see what you would miss.
>
> The goal is not automation.
> **The goal is better thinking.**
