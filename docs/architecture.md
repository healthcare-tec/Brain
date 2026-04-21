# Charlie — Architecture Documentation

## System Overview

Charlie is a personal Cognitive Operating System built as a stand-alone application. It follows a three-tier architecture with clear separation of concerns.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │Inbox │ │Tasks │ │Projects│ │Thinking│ │  Notes   │  │
│  └──┬───┘ └──┬───┘ └───┬────┘ └───┬────┘ └────┬─────┘  │
│     └────────┴─────────┴─────────┴──────────┘          │
│                    API Service Layer                     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────┴────────────────────────────────┐
│                  Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  API Routers                      │   │
│  │  inbox │ tasks │ projects │ notes │ reviews │ ai  │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────┴───────────────────────────┐   │
│  │               Service Layer                       │   │
│  │  inbox_service │ task_service │ project_service   │   │
│  │  note_service  │ decision_log_service │ review    │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────┴───────────────────────────┐   │
│  │              Event System                         │   │
│  │  captured │ clarified │ scheduled │ completed     │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │           AI Cognitive Layer (stubs)              │   │
│  │  L1: Classifier │ L2: Interpreter │ L3: Analyzer │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────┴──────────┐    ┌────────────┴────────────┐
│   PostgreSQL       │    │   Markdown Filesystem   │
│  ┌──────────────┐  │    │  ┌───────────────────┐  │
│  │ inbox_items  │  │    │  │ knowledge/        │  │
│  │ tasks        │  │    │  │   projects/       │  │
│  │ projects     │  │    │  │   areas/          │  │
│  │ task_events  │  │    │  │   resources/      │  │
│  │ decision_logs│  │    │  │   archive/        │  │
│  │ notes        │  │    │  └───────────────────┘  │
│  └──────────────┘  │    └─────────────────────────┘
└────────────────────┘
```

---

## Data Flow

### Capture Flow
1. User enters text in the Inbox quick capture field
2. Frontend calls `POST /api/inbox/`
3. Backend creates `InboxItem` with status `pending`
4. Event system emits `captured` event
5. Item appears in Inbox list

### Clarification Flow (GTD)
1. User clicks "Clarify" on a pending inbox item
2. User selects type: task, project, note, or trash
3. Frontend calls `POST /api/inbox/{id}/clarify`
4. Backend creates the target entity (Task, Project, or Note)
5. Updates InboxItem with `clarified_as` and `clarified_ref_id`
6. Event system emits `clarified` event

### Task Completion Flow
1. User clicks the Done button on a task
2. Optionally enters actual time spent
3. Frontend calls `POST /api/tasks/{id}/complete`
4. Backend sets `status=done`, `completed_at=now()`
5. Stores execution metadata (actual_time, context)
6. Event system emits `completed` event with full metadata

---

## Database Schema

### inbox_items
Stores all captured inputs before clarification.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| content | TEXT | Raw captured content |
| item_type | VARCHAR(50) | quick_note, task, idea, other |
| status | ENUM | pending, processed, trashed |
| clarified_as | VARCHAR(50) | task, project, note, trash |
| clarified_ref_id | UUID | FK to created entity |
| captured_at | TIMESTAMP | When captured |
| processed_at | TIMESTAMP | When clarified |

### tasks
Core task management table.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR(500) | Task title |
| description | TEXT | Optional description |
| status | ENUM | next, waiting, someday, done |
| priority | ENUM | low, medium, high, critical |
| context | VARCHAR(100) | GTD context (@work, @home) |
| project_id | UUID | FK to projects |
| estimated_time | INT | Minutes (estimated) |
| actual_time | INT | Minutes (actual) |
| due_date | TIMESTAMP | Optional deadline |
| created_at | TIMESTAMP | Creation time |
| completed_at | TIMESTAMP | Completion time |
| updated_at | TIMESTAMP | Last update |

### projects
Groups tasks into projects.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(500) | Project name |
| description | TEXT | Optional description |
| status | ENUM | active, on_hold, completed, archived |
| area | VARCHAR(200) | PARA area |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### task_events
Event sourcing table for all system actions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| task_id | UUID | FK to tasks (nullable) |
| event_type | ENUM | captured, clarified, scheduled, completed, reviewed, updated, created |
| description | TEXT | Human-readable description |
| metadata_json | TEXT | JSON with extra data |
| created_at | TIMESTAMP | Event time |

### decision_logs
Thinking Engine metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR(500) | Decision title |
| log_type | ENUM | decision, risk_analysis, problem_breakdown |
| context | TEXT | Situation context |
| hypotheses | TEXT | Working hypotheses |
| options | TEXT | Available options |
| decision | TEXT | Chosen option |
| expected_outcome | TEXT | What was expected |
| actual_outcome | TEXT | What actually happened |
| markdown_path | VARCHAR(1000) | Path to full Markdown doc |
| tags | VARCHAR(500) | Comma-separated tags |

### notes
Knowledge System metadata (content in Markdown files).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR(500) | Note title |
| category | ENUM | project, area, resource, archive |
| tags | VARCHAR(500) | Comma-separated tags |
| markdown_path | VARCHAR(1000) | Path to Markdown file |
| content | TEXT | Inline content (if no file) |
| linked_note_ids | VARCHAR(2000) | Linked notes |

---

## Event System

Every significant action generates an event stored in `task_events`. Events feed the Memory Palace and AI analysis layers.

| Event Type | Trigger |
|-----------|---------|
| `captured` | New inbox item created |
| `clarified` | Inbox item processed |
| `created` | New task created directly |
| `updated` | Task fields modified |
| `scheduled` | Task assigned a due date |
| `completed` | Task marked as done |
| `reviewed` | Weekly review completed |

---

## AI Cognitive Layer

The AI layer is designed with three levels, currently implemented as stubs ready for LLM integration.

### Level 1 — Classification
- Input categorization (task vs note vs project)
- Suggest next actions
- Reduce friction in GTD processing

### Level 2 — Interpretation
- Retrieve relevant past knowledge via Memory Palace
- Connect current problem to past decisions
- Provide contextual insights

### Level 3 — Analysis
- Detect patterns over time
- Identify recurring errors
- Compare expected vs actual outcomes
- Suggest improvements

### Rules
- AI does not store data (PostgreSQL + Markdown do)
- AI does not make final decisions
- AI operates on demand or triggered events

---

## Storage Philosophy

> PostgreSQL stores what you do.
> Markdown stores what you think.
> Memory Palace surfaces what matters.
> AI helps you see what you would miss.

The dual storage model ensures that structured data (tasks, events, metadata) lives in PostgreSQL for efficient querying, while knowledge content (notes, thinking documents) lives as portable Markdown files in the PARA structure.
