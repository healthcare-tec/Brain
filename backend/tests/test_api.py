"""
Tests for Charlie API endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["system"] == "Charlie"


# ── Inbox (Capture Engine) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_capture_item(client):
    resp = await client.post("/api/inbox/", json={"content": "Buy groceries", "item_type": "task"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Buy groceries"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_inbox(client):
    await client.post("/api/inbox/", json={"content": "Item 1"})
    await client.post("/api/inbox/", json={"content": "Item 2"})
    resp = await client.get("/api/inbox/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_clarify_as_task(client):
    # Capture
    resp = await client.post("/api/inbox/", json={"content": "Write report"})
    item_id = resp.json()["id"]
    # Clarify as task
    resp = await client.post(
        f"/api/inbox/{item_id}/clarify",
        json={"clarified_as": "task", "title": "Write Q1 report"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["clarified_as"] == "task"
    assert data["status"] == "processed"
    assert data["clarified_ref_id"] is not None


@pytest.mark.asyncio
async def test_clarify_as_trash(client):
    resp = await client.post("/api/inbox/", json={"content": "Random noise"})
    item_id = resp.json()["id"]
    resp = await client.post(
        f"/api/inbox/{item_id}/clarify",
        json={"clarified_as": "trash"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "trashed"


# ── Tasks ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task(client):
    resp = await client.post("/api/tasks/", json={
        "title": "Deploy app",
        "priority": "high",
        "context": "@work",
        "estimated_time": 60,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Deploy app"
    assert data["status"] == "next"


@pytest.mark.asyncio
async def test_complete_task(client):
    # Create
    resp = await client.post("/api/tasks/", json={"title": "Fix bug"})
    task_id = resp.json()["id"]
    # Complete
    resp = await client.post(
        f"/api/tasks/{task_id}/complete",
        json={"actual_time": 30, "notes": "Fixed the null pointer issue"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["actual_time"] == 30
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_update_task(client):
    resp = await client.post("/api/tasks/", json={"title": "Old title"})
    task_id = resp.json()["id"]
    resp = await client.patch(f"/api/tasks/{task_id}", json={"title": "New title", "status": "waiting"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"
    assert resp.json()["status"] == "waiting"


@pytest.mark.asyncio
async def test_delete_task(client):
    resp = await client.post("/api/tasks/", json={"title": "To delete"})
    task_id = resp.json()["id"]
    resp = await client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client):
    await client.post("/api/tasks/", json={"title": "Next task", "status": "next"})
    await client.post("/api/tasks/", json={"title": "Someday task", "status": "someday"})
    resp = await client.get("/api/tasks/?status=next")
    assert resp.status_code == 200
    for t in resp.json():
        assert t["status"] == "next"


# ── Projects ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_project(client):
    resp = await client.post("/api/projects/", json={
        "name": "Charlie MVP",
        "description": "Build the cognitive OS",
        "area": "Technology",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Charlie MVP"


@pytest.mark.asyncio
async def test_list_projects(client):
    await client.post("/api/projects/", json={"name": "Project A"})
    resp = await client.get("/api/projects/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Decision Logs ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_decision_log(client):
    resp = await client.post("/api/decision-logs/", json={
        "title": "Choose database",
        "log_type": "decision",
        "context": "Need a reliable DB for Charlie",
        "options": "PostgreSQL vs MySQL vs SQLite",
        "decision": "PostgreSQL",
        "expected_outcome": "Reliable, scalable storage",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "Choose database"


# ── Notes ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_note(client):
    resp = await client.post("/api/notes/", json={
        "title": "GTD Methodology",
        "category": "resource",
        "tags": "productivity,gtd",
        "content": "Getting Things Done is a personal productivity methodology.",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "GTD Methodology"


# ── Reviews ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_weekly_review(client):
    resp = await client.get("/api/reviews/weekly")
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_inbox" in data
    assert "completed_tasks" in data


# ── Events ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_events(client):
    # Create a task to generate events
    await client.post("/api/tasks/", json={"title": "Event test"})
    resp = await client.get("/api/events/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── AI Stubs ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_classify(client):
    resp = await client.post("/api/ai/classify?content=Buy milk")
    assert resp.status_code == 200
    assert "suggested_type" in resp.json()


@pytest.mark.asyncio
async def test_ai_interpret(client):
    resp = await client.post("/api/ai/interpret?query=database choice")
    assert resp.status_code == 200
    assert resp.json()["ai_powered"] is False


@pytest.mark.asyncio
async def test_ai_patterns(client):
    resp = await client.get("/api/ai/patterns")
    assert resp.status_code == 200
    assert resp.json()["ai_powered"] is False
