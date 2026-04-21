# Charlie — Architecture Documentation

## System Overview

Charlie is a personal Cognitive Operating System built as a stand-alone application. It follows a three-tier architecture with clear separation of concerns. All data is stored locally using SQLite and Markdown files — no external services required (OpenAI is optional for AI features).

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Tailwind)                    │
│  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌─────────────┐  │
│  │Inbox │ │Tasks │ │Kanban  │ │Projects│ │Notes │ │  Dashboard  │  │
│  │(D&D) │ │(Adv) │ │(D&D)  │ │        │ │(PARA)│ │ (Analytics) │  │
│  └──┬───┘ └──┬───┘ └──┬────┘ └───┬────┘ └──┬───┘ └──────┬──────┘  │
│  ┌──┴───┐ ┌──┴───┐ ┌──┴────┐ ┌───┴────┐ ┌──┴───┐ ┌──────┴──────┐  │
│  │Voice │ │Think │ │Review │ │Insights│ │Search│ │  Calendar   │  │
│  │Captur│ │  ing │ │       │ │  (AI)  │ │Global│ │  (GCal)     │  │
│  └──────┘ └──────┘ └───────┘ └────────┘ └──────┘ └─────────────┘  │
│                                                                      │
│  Dark Mode ◆ Keyboard Shortcuts ◆ Notifications ◆ Export            │
│                    API Service Layer                                  │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────┴─────────────────────────────────────────────┐
│                      Backend (FastAPI)                                │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                       API Routers                             │   │
│  │  inbox │ tasks │ projects │ notes │ reviews │ ai │ events     │   │
│  │  search │ analytics │ export │ voice │ insights │ decision    │   │
│  └──────────────────────────┬────────────────────────────────────┘   │
│  ┌──────────────────────────┴────────────────────────────────────┐   │
│  │                    Service Layer                               │   │
│  │  inbox_service │ task_service (recurring, tags, reminders)    │   │
│  │  project_service │ note_service │ decision_log_service        │   │
│  │  review_service                                               │   │
│  └──────────────────────────┬────────────────────────────────────┘   │
│  ┌──────────────────────────┴────────────────────────────────────┐   │
│  │                   Event System                                │   │
│  │  captured │ clarified │ scheduled │ completed │ recurring     │   │
│  └───────────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │              AI Cognitive Layer (OpenAI GPT)                   │   │
│  │  L1: Classifier │ L2: Interpreter │ L3: Analyzer             │   │
│  │  Voice Splitter │ Proactive Insights │ Weekly Review AI       │   │
│  └───────────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────┴──────────┐    ┌────────────┴────────────┐
│   SQLite            │    │   Markdown Filesystem   │
│  ┌──────────────┐  │    │  ┌───────────────────┐  │
│  │ inbox_items  │  │    │  │ knowledge/        │  │
│  │ tasks (+tags │  │    │  │   projects/       │  │
│  │  +recurring) │  │    │  │   areas/          │  │
│  │ projects     │  │    │  │   resources/      │  │
│  │ task_events  │  │    │  │   archive/        │  │
│  │ decision_logs│  │    │  └───────────────────┘  │
│  │ notes        │  │    └─────────────────────────┘
│  └──────────────┘  │
└────────────────────┘
```

---

## Features Overview

### Quick Wins
| Feature | Description |
|---------|-------------|
| **Dark Mode** | Toggle in header, CSS class strategy via Tailwind |
| **Global Search** | Unified search across tasks, notes, projects, decision logs |
| **Drag & Drop Inbox** | Drag items to Task/Project/Note/Trash drop zones |
| **Keyboard Shortcuts** | N=capture, D=done, C=clarify, arrows=navigate |
| **Notifications** | Reminders for tasks with deadlines, Web Notifications API |

### Structural Features
| Feature | Description |
|---------|-------------|
| **Dashboard Analytics** | Charts: tasks/day, estimated vs actual time, context/project distribution |
| **Recurring Tasks** | Daily/weekly/monthly recurrence, auto-creates next occurrence on completion |
| **Tags & Advanced Filters** | Free-form tags + combined filters (tag+status+project+priority) |
| **Kanban View** | Columns: Next → In Progress → Waiting → Done with drag & drop |
| **Data Export** | CSV, JSON, or Markdown export for tasks, notes, decision logs |

### Advanced Features
| Feature | Description |
|---------|-------------|
| **AI Proactive Insights** | Pattern detection: stale tasks, estimation accuracy, bottlenecks |
| **Google Calendar** | Sync tasks with deadlines to Google Calendar (stub ready) |
| **Voice Capture** | Web Speech API + AI splits spoken text into multiple inbox items |

---

## Data Flow

### Capture Flow
1. User enters text in Inbox quick capture (or voice capture)
2. Frontend calls `POST /api/inbox/`
3. Backend creates `InboxItem` with status `pending`
4. Event system emits `captured` event
5. Item appears in Inbox list

### AI Clarification Flow
1. User clicks "AI Clarify" on a pending inbox item
2. Frontend calls `POST /api/ai/classify` with item content
3. OpenAI GPT classifies: task/project/note/idea/trash + metadata
4. Suggestion displayed inline with confidence bar
5. User can Apply (auto-clarify) or Edit (pre-filled modal)
6. Frontend calls `POST /api/inbox/{id}/clarify`
7. Event system emits `clarified` event

### Voice Capture Flow
1. User speaks into microphone (Web Speech API)
2. Transcribed text sent to `POST /api/voice/capture`
3. AI splits text into multiple distinct items
4. Each item created as separate inbox entry
5. User reviews and clarifies each item

### Task Completion Flow (with Recurring)
1. User clicks Done on a task
2. Frontend calls `POST /api/tasks/{id}/complete`
3. Backend sets `status=done`, `completed_at=now()`
4. If task has `recurrence_pattern`, creates next occurrence
5. Event system emits `completed` event

---

## Database Schema

### tasks (updated)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR(500) | Task title |
| description | TEXT | Optional description |
| status | VARCHAR(20) | next, in_progress, waiting, someday, done |
| priority | VARCHAR(20) | low, medium, high, critical |
| context | VARCHAR(100) | GTD context (@work, @home) |
| project_id | UUID | FK to projects |
| estimated_time | INT | Minutes (estimated) |
| actual_time | INT | Minutes (actual) |
| due_date | TIMESTAMP | Optional deadline |
| tags | VARCHAR(1000) | Comma-separated tags |
| recurrence_pattern | VARCHAR(20) | daily, weekly, monthly, null |
| recurrence_parent_id | UUID | FK to parent task (for recurring) |
| reminder_at | TIMESTAMP | When to send reminder |
| created_at | TIMESTAMP | Creation time |
| completed_at | TIMESTAMP | Completion time |
| updated_at | TIMESTAMP | Last update |

---

## API Endpoints

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/inbox/ | Capture new item |
| POST | /api/inbox/{id}/clarify | Clarify inbox item (GTD) |
| GET | /api/tasks/ | List tasks (advanced filters) |
| POST | /api/tasks/{id}/complete | Complete task |
| GET | /api/tasks/reminders | Get upcoming reminders |
| GET/POST | /api/projects/ | CRUD projects |
| GET/POST | /api/notes/ | CRUD notes |
| GET/POST | /api/decision-logs/ | CRUD decision logs |
| GET | /api/reviews/weekly | Weekly review metrics |

### New Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/search/ | Global search across all entities |
| GET | /api/analytics/dashboard | Productivity metrics and charts |
| GET | /api/export/{entity} | Export data as CSV/JSON/Markdown |
| POST | /api/voice/capture | AI-powered voice text splitting |
| GET | /api/insights/ | AI proactive insights |

### AI Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/ai/classify | L1: Classify inbox item |
| POST | /api/ai/interpret | L2: Deep interpretation |
| GET | /api/ai/patterns | L3: Pattern analysis |
| POST | /api/ai/weekly-review | AI-generated weekly review |
| GET | /api/ai/status | Check if AI is configured |

---

## Storage Philosophy

> SQLite stores what you do.
> Markdown stores what you think.
> Memory Palace surfaces what matters.
> AI helps you see what you would miss.

The dual storage model ensures that structured data (tasks, events, metadata) lives in SQLite for zero-config local operation, while knowledge content (notes, thinking documents) lives as portable Markdown files in the PARA structure.

---

## Deployment

Charlie runs entirely locally without Docker:

```bash
bash start-local.sh    # Backend (8085) + Frontend (8080)
python3 charlie-cli.py # CLI alternative
```

No external services required. OpenAI API key is optional for AI features.
