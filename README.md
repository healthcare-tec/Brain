# Charlie — Cognitive Operating System

Charlie is a personal **Cognitive Operating System** designed to capture inputs instantly, organize execution (GTD), structure knowledge (Second Brain / PARA), support deep thinking (System 2), learn from past decisions (Memory Palace), and amplify cognition using AI.

Charlie is not a task manager. It is a system for **thinking, deciding, and improving over time**.

---

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Python 3.11 | REST API, business logic, event system |
| **Database** | PostgreSQL 16 | Tasks, projects, events, decision logs, note metadata |
| **Knowledge** | Markdown filesystem (PARA) | Notes, thinking documents, knowledge base |
| **Frontend** | React 18 + Tailwind CSS | Complete UI for all modules |
| **Infrastructure** | Docker Compose | Stand-alone deployment |
| **Migrations** | Alembic | Database schema versioning |

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
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/healthcare-tec/Brain.git
cd Brain

# Start all services (PostgreSQL + Backend + Frontend)
docker compose up --build

# The system will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production Mode

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Frontend: http://localhost (port 80)
# Backend API: http://localhost:8000
```

### Run Migrations Manually

```bash
docker compose exec backend alembic upgrade head
```

### Run Tests

```bash
# Install test dependencies locally
cd backend
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

---

## Project Structure

```
Brain/
├── README.md                    # This file
├── docker-compose.yml           # Development environment
├── docker-compose.prod.yml      # Production override
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── start.sh
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
│   ├── Dockerfile
│   ├── nginx.conf               # Production nginx config
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
├── knowledge/                   # PARA structure (Markdown)
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

Full interactive API documentation is available at `http://localhost:8000/docs` (Swagger UI).

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

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://charlie:charlie@db:5432/charlie` | Async database URL |
| `DATABASE_URL_SYNC` | `postgresql://charlie:charlie@db:5432/charlie` | Sync database URL (Alembic) |
| `KNOWLEDGE_BASE_PATH` | `/app/knowledge` | Path to PARA Markdown files |
| `DEBUG` | `false` | Enable debug mode |

---

## Development Roadmap

- **Phase 1** (implemented): Capture Engine, Task System, Done System, Project Management
- **Phase 2** (implemented): Notes (PARA), Thinking Engine, Decision Logs
- **Phase 3** (stubs): Memory Palace integration, AI Classification
- **Phase 4** (stubs): AI Interpretation, Pattern Detection
- **Future**: WhatsApp capture, email ingestion, calendar sync, local LLM integration

---

## License

See [LICENSE](LICENSE) for details.
