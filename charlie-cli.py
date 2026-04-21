#!/usr/bin/env python3
"""
Charlie — Cognitive Operating System
Interactive CLI

Works standalone: connects directly to the backend API.
If the backend is not running, starts it automatically (if venv exists).

Usage:
    python3 charlie-cli.py
    python3 charlie-cli.py --api http://localhost:8085
"""

import sys
import os
import json
import argparse
import subprocess
import time
from datetime import datetime
from typing import Optional

# ── Try to import requests; install if missing ────────────────────────────────
try:
    import requests
except ImportError:
    print("Installing 'requests'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_API = os.environ.get("CHARLIE_API", "http://localhost:8085")

# ─────────────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    WHITE  = "\033[97m"

def c(color, text): return f"{color}{text}{C.RESET}"
def bold(t): return c(C.BOLD, t)
def ok(t):   print(c(C.GREEN,  f"  ✓  {t}"))
def err(t):  print(c(C.RED,    f"  ✗  {t}"))
def info(t): print(c(C.CYAN,   f"  ·  {t}"))
def warn(t): print(c(C.YELLOW, f"  !  {t}"))

def header(title):
    w = 56
    print()
    print(c(C.BLUE, "═" * w))
    print(c(C.BLUE, f"  {bold(title)}"))
    print(c(C.BLUE, "═" * w))

def divider():
    print(c(C.GRAY, "  " + "─" * 52))

# ─────────────────────────────────────────────────────────────────────────────
# API client
# ─────────────────────────────────────────────────────────────────────────────
class CharlieAPI:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _url(self, path): return f"{self.base}/api{path}"

    def get(self, path, params=None):
        r = self.session.get(self._url(path), params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def post(self, path, data=None):
        r = self.session.post(self._url(path), json=data, timeout=10)
        r.raise_for_status()
        return r.json()

    def patch(self, path, data=None):
        r = self.session.patch(self._url(path), json=data, timeout=10)
        r.raise_for_status()
        return r.json()

    def delete(self, path):
        r = self.session.delete(self._url(path), timeout=10)
        r.raise_for_status()
        return r.status_code

    def health(self):
        try:
            r = self.session.get(f"{self.base}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

# ─────────────────────────────────────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────────────────────────────────────
def prompt(label, default=None, required=True):
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"  {c(C.CYAN, label)}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if val:
            return val
        if not required:
            return ""
        warn("This field is required.")

def prompt_optional(label, default=""):
    val = input(f"  {c(C.GRAY, label)} (optional): ").strip()
    return val if val else default

def prompt_choice(label, choices, default=None):
    opts = " / ".join(
        [c(C.YELLOW, ch) if ch == default else ch for ch in choices]
    )
    while True:
        val = input(f"  {c(C.CYAN, label)} ({opts}): ").strip().lower()
        if not val and default:
            return default
        if val in choices:
            return val
        warn(f"Choose one of: {', '.join(choices)}")

def prompt_int(label, default=None, required=False):
    suffix = f" [{default}]" if default is not None else ""
    val = input(f"  {c(C.CYAN, label)}{suffix}: ").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        warn("Please enter a number.")
        return default

def confirm(question):
    val = input(f"  {c(C.YELLOW, question)} (y/N): ").strip().lower()
    return val == "y"

def menu(title, options):
    """Display a numbered menu and return the selected key."""
    print()
    print(c(C.BOLD, f"  {title}"))
    divider()
    keys = list(options.keys())
    for i, key in enumerate(keys, 1):
        print(f"  {c(C.CYAN, str(i))}  {options[key]}")
    print(f"  {c(C.GRAY, '0')}  {c(C.GRAY, 'Back / Exit')}")
    divider()
    while True:
        val = input(f"  {c(C.CYAN, 'Choose')}: ").strip()
        if val == "0":
            return None
        try:
            idx = int(val) - 1
            if 0 <= idx < len(keys):
                return keys[idx]
        except ValueError:
            pass
        warn("Invalid choice.")

# ─────────────────────────────────────────────────────────────────────────────
# Format helpers
# ─────────────────────────────────────────────────────────────────────────────
def fmt_date(iso):
    if not iso:
        return c(C.GRAY, "—")
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso

def fmt_status(s):
    colors = {
        "next": C.GREEN, "waiting": C.YELLOW, "someday": C.GRAY,
        "done": C.BLUE, "active": C.GREEN, "completed": C.BLUE,
        "on_hold": C.YELLOW, "pending": C.CYAN, "clarified": C.GREEN,
        "trashed": C.RED,
    }
    return c(colors.get(s, C.WHITE), s.upper())

def fmt_priority(p):
    colors = {"urgent": C.RED, "high": C.YELLOW, "medium": C.CYAN, "low": C.GRAY}
    return c(colors.get(p, C.WHITE), p.upper() if p else "—")

def print_task(t, idx=None):
    prefix = f"  {c(C.GRAY, str(idx)+'.')} " if idx else "  "
    status = fmt_status(t.get("status", ""))
    pri = fmt_priority(t.get("priority", ""))
    title = t.get("title", "")
    project = c(C.GRAY, f"[{t['project_id']}]") if t.get("project_id") else ""
    ctx = c(C.GRAY, t.get("context", "")) if t.get("context") else ""
    est = c(C.GRAY, f"~{t['estimated_time']}m") if t.get("estimated_time") else ""
    print(f"{prefix}{bold(title)}")
    print(f"       {status}  {pri}  {ctx}  {est}  {project}")
    if t.get("notes"):
        print(f"       {c(C.GRAY, t['notes'][:80])}")

def print_inbox(item, idx=None):
    prefix = f"  {c(C.GRAY, str(idx)+'.')} " if idx else "  "
    status = fmt_status(item.get("status", "pending"))
    print(f"{prefix}{bold(item.get('content', ''))}")
    print(f"       {status}  {c(C.GRAY, fmt_date(item.get('created_at', '')))}")

def print_project(p, idx=None):
    prefix = f"  {c(C.GRAY, str(idx)+'.')} " if idx else "  "
    status = fmt_status(p.get("status", ""))
    total = p.get("task_count", 0)
    done = p.get("done_count", 0)
    pct = f"{int(done/total*100)}%" if total else "0%"
    print(f"{prefix}{bold(p.get('name', ''))}  {status}  {c(C.GRAY, f'{done}/{total} ({pct})')}")
    if p.get("description"):
        print(f"       {c(C.GRAY, p['description'][:80])}")

def print_note(n, idx=None):
    prefix = f"  {c(C.GRAY, str(idx)+'.')} " if idx else "  "
    cat = c(C.CYAN, n.get("category", ""))
    tags = c(C.GRAY, ", ".join(n.get("tags", []))) if n.get("tags") else ""
    print(f"{prefix}{bold(n.get('title', ''))}  {cat}  {tags}")

def print_decision(d, idx=None):
    prefix = f"  {c(C.GRAY, str(idx)+'.')} " if idx else "  "
    dtype = c(C.CYAN, d.get("log_type", ""))
    print(f"{prefix}{bold(d.get('title', ''))}  {dtype}")
    if d.get("decision"):
        print(f"       {c(C.GRAY, 'Decision: ')}{d['decision'][:80]}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Capture (Inbox)
# ─────────────────────────────────────────────────────────────────────────────
def module_capture(api: CharlieAPI):
    header("CAPTURE — Quick Inbox")
    print(c(C.GRAY, "  Capture anything without structure. Process later."))
    print()
    content = prompt("What's on your mind?")
    source = prompt_optional("Source (e.g. @meeting, @shower, @reading)", "cli")

    try:
        item = api.post("/inbox/", {"content": content, "source": source or "cli"})
        ok(f"Captured to inbox (ID: {item['id']})")
    except Exception as e:
        err(f"Failed to capture: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Inbox
# ─────────────────────────────────────────────────────────────────────────────
def module_inbox(api: CharlieAPI):
    while True:
        header("INBOX — Clarification Engine (GTD)")

        try:
            items = api.get("/inbox/", {"status": "pending"})
        except Exception as e:
            err(f"Could not load inbox: {e}")
            return

        if not items:
            ok("Inbox is empty. Great work!")
            input(c(C.GRAY, "\n  Press Enter to continue..."))
            return

        info(f"{len(items)} item(s) pending clarification")
        print()
        for i, item in enumerate(items, 1):
            print_inbox(item, i)

        print()
        choice = menu("Inbox actions", {
            "clarify": "Clarify an item (GTD process)",
            "view_all": "View all items (including processed)",
            "delete": "Delete an item",
        })

        if choice is None:
            return

        elif choice == "clarify":
            idx = prompt_int("Item number to clarify", required=True)
            if not idx or idx < 1 or idx > len(items):
                warn("Invalid item number.")
                continue
            item = items[idx - 1]
            print()
            print(f"  Item: {bold(item['content'])}")
            print()
            outcome = prompt_choice(
                "What is this?",
                ["task", "project", "note", "trash"],
                default="task"
            )
            clarify_data = {"outcome": outcome}

            if outcome == "task":
                clarify_data["title"] = prompt("Task title", default=item["content"][:80])
                clarify_data["status"] = prompt_choice("Status", ["next", "waiting", "someday"], "next")
                clarify_data["priority"] = prompt_choice("Priority", ["urgent", "high", "medium", "low"], "medium")
                clarify_data["context"] = prompt_optional("Context (@work, @home, @computer)")
                est = prompt_int("Estimated time (minutes)", required=False)
                if est:
                    clarify_data["estimated_time"] = est

            elif outcome == "project":
                clarify_data["title"] = prompt("Project name", default=item["content"][:80])
                clarify_data["description"] = prompt_optional("Description")

            elif outcome == "note":
                clarify_data["title"] = prompt("Note title", default=item["content"][:80])
                clarify_data["category"] = prompt_choice(
                    "PARA category", ["projects", "areas", "resources", "archive"], "resources"
                )
                clarify_data["content"] = prompt_optional("Note content (or leave blank)")

            try:
                result = api.post(f"/inbox/{item['id']}/clarify", clarify_data)
                ok(f"Item clarified as {outcome}.")
            except Exception as e:
                err(f"Clarification failed: {e}")

        elif choice == "view_all":
            try:
                all_items = api.get("/inbox/")
                print()
                for i, item in enumerate(all_items, 1):
                    print_inbox(item, i)
                input(c(C.GRAY, "\n  Press Enter to continue..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "delete":
            idx = prompt_int("Item number to delete", required=True)
            if not idx or idx < 1 or idx > len(items):
                warn("Invalid item number.")
                continue
            item = items[idx - 1]
            if confirm(f"Delete '{item['content'][:50]}'?"):
                try:
                    api.delete(f"/inbox/{item['id']}")
                    ok("Item deleted.")
                except Exception as e:
                    err(f"Failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Tasks
# ─────────────────────────────────────────────────────────────────────────────
def module_tasks(api: CharlieAPI):
    while True:
        header("TASKS — Next Actions")

        choice = menu("Task actions", {
            "next": "View Next Actions",
            "all": "View all tasks",
            "add": "Add new task",
            "done": "Mark task as DONE",
            "edit": "Edit a task",
            "delete": "Delete a task",
        })

        if choice is None:
            return

        elif choice in ("next", "all"):
            params = {} if choice == "all" else {"status": "next"}
            try:
                tasks = api.get("/tasks/", params)
            except Exception as e:
                err(f"Failed: {e}")
                continue

            if not tasks:
                ok("No tasks found.")
                input(c(C.GRAY, "\n  Press Enter..."))
                continue

            print()
            for i, t in enumerate(tasks, 1):
                print_task(t, i)
            input(c(C.GRAY, "\n  Press Enter..."))

        elif choice == "add":
            print()
            title = prompt("Task title")
            status = prompt_choice("Status", ["next", "waiting", "someday"], "next")
            priority = prompt_choice("Priority", ["urgent", "high", "medium", "low"], "medium")
            context = prompt_optional("Context (@work, @home, @computer)")
            notes = prompt_optional("Notes")
            est = prompt_int("Estimated time (minutes)", required=False)

            data = {
                "title": title,
                "status": status,
                "priority": priority,
            }
            if context: data["context"] = context
            if notes:   data["notes"] = notes
            if est:     data["estimated_time"] = est

            # Optional: link to project
            try:
                projects = api.get("/projects/", {"status": "active"})
                if projects:
                    print()
                    print(c(C.GRAY, "  Available projects:"))
                    for i, p in enumerate(projects, 1):
                        print(f"    {c(C.CYAN, str(i))}  {p['name']}")
                    pidx = prompt_int("Link to project (0 to skip)", required=False)
                    if pidx and 1 <= pidx <= len(projects):
                        data["project_id"] = projects[pidx - 1]["id"]
            except Exception:
                pass

            try:
                task = api.post("/tasks/", data)
                ok(f"Task created (ID: {task['id']})")
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "done":
            try:
                tasks = api.get("/tasks/", {"status": "next"})
            except Exception as e:
                err(f"Failed: {e}")
                continue

            if not tasks:
                ok("No next actions to complete.")
                input(c(C.GRAY, "\n  Press Enter..."))
                continue

            print()
            for i, t in enumerate(tasks, 1):
                print_task(t, i)
            print()

            idx = prompt_int("Task number to mark DONE", required=True)
            if not idx or idx < 1 or idx > len(tasks):
                warn("Invalid number.")
                continue

            task = tasks[idx - 1]
            print()
            actual = prompt_int(
                f"Actual time spent (minutes, estimated: {task.get('estimated_time', '?')})",
                required=False
            )
            completion_notes = prompt_optional("Completion notes")

            done_data = {}
            if actual: done_data["actual_time"] = actual
            if completion_notes: done_data["completion_notes"] = completion_notes

            try:
                api.post(f"/tasks/{task['id']}/complete", done_data)
                ok(f"Task '{task['title']}' marked as DONE!")
                if actual and task.get("estimated_time"):
                    diff = actual - task["estimated_time"]
                    if diff > 0:
                        warn(f"Took {diff}m longer than estimated.")
                    elif diff < 0:
                        ok(f"Finished {abs(diff)}m ahead of estimate!")
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "edit":
            try:
                tasks = api.get("/tasks/")
            except Exception as e:
                err(f"Failed: {e}")
                continue

            if not tasks:
                ok("No tasks.")
                continue

            print()
            for i, t in enumerate(tasks, 1):
                print_task(t, i)
            print()

            idx = prompt_int("Task number to edit", required=True)
            if not idx or idx < 1 or idx > len(tasks):
                warn("Invalid number.")
                continue

            task = tasks[idx - 1]
            print()
            print(c(C.GRAY, "  Leave blank to keep current value."))
            print()

            updates = {}
            title = input(f"  {c(C.CYAN, 'Title')} [{task['title']}]: ").strip()
            if title: updates["title"] = title

            status = input(f"  {c(C.CYAN, 'Status')} [{task['status']}] (next/waiting/someday/done): ").strip()
            if status and status in ["next", "waiting", "someday", "done"]:
                updates["status"] = status

            priority = input(f"  {c(C.CYAN, 'Priority')} [{task.get('priority','')}] (urgent/high/medium/low): ").strip()
            if priority and priority in ["urgent", "high", "medium", "low"]:
                updates["priority"] = priority

            if updates:
                try:
                    api.patch(f"/tasks/{task['id']}", updates)
                    ok("Task updated.")
                except Exception as e:
                    err(f"Failed: {e}")
            else:
                info("No changes made.")

        elif choice == "delete":
            try:
                tasks = api.get("/tasks/")
            except Exception as e:
                err(f"Failed: {e}")
                continue

            if not tasks:
                ok("No tasks.")
                continue

            print()
            for i, t in enumerate(tasks, 1):
                print_task(t, i)
            print()

            idx = prompt_int("Task number to delete", required=True)
            if not idx or idx < 1 or idx > len(tasks):
                warn("Invalid number.")
                continue

            task = tasks[idx - 1]
            if confirm(f"Delete '{task['title']}'?"):
                try:
                    api.delete(f"/tasks/{task['id']}")
                    ok("Task deleted.")
                except Exception as e:
                    err(f"Failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Projects
# ─────────────────────────────────────────────────────────────────────────────
def module_projects(api: CharlieAPI):
    while True:
        header("PROJECTS")

        choice = menu("Project actions", {
            "list": "List all projects",
            "add": "Create new project",
            "tasks": "View project tasks",
            "complete": "Mark project as completed",
        })

        if choice is None:
            return

        elif choice == "list":
            try:
                projects = api.get("/projects/")
                print()
                if not projects:
                    ok("No projects yet.")
                else:
                    for i, p in enumerate(projects, 1):
                        print_project(p, i)
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "add":
            print()
            name = prompt("Project name")
            description = prompt_optional("Description")
            outcome = prompt_optional("Desired outcome")

            data = {"name": name}
            if description: data["description"] = description
            if outcome: data["desired_outcome"] = outcome

            try:
                project = api.post("/projects/", data)
                ok(f"Project created (ID: {project['id']})")
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "tasks":
            try:
                projects = api.get("/projects/")
                if not projects:
                    ok("No projects.")
                    continue
                print()
                for i, p in enumerate(projects, 1):
                    print_project(p, i)
                print()
                idx = prompt_int("Project number", required=True)
                if not idx or idx < 1 or idx > len(projects):
                    warn("Invalid number.")
                    continue
                project = projects[idx - 1]
                tasks = api.get("/tasks/", {"project_id": project["id"]})
                print()
                print(bold(f"  Tasks for: {project['name']}"))
                divider()
                if not tasks:
                    ok("No tasks in this project.")
                else:
                    for i, t in enumerate(tasks, 1):
                        print_task(t, i)
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "complete":
            try:
                projects = api.get("/projects/", {"status": "active"})
                if not projects:
                    ok("No active projects.")
                    continue
                print()
                for i, p in enumerate(projects, 1):
                    print_project(p, i)
                print()
                idx = prompt_int("Project number to complete", required=True)
                if not idx or idx < 1 or idx > len(projects):
                    warn("Invalid number.")
                    continue
                project = projects[idx - 1]
                if confirm(f"Mark '{project['name']}' as completed?"):
                    api.patch(f"/projects/{project['id']}", {"status": "completed"})
                    ok("Project marked as completed.")
            except Exception as e:
                err(f"Failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Thinking Engine
# ─────────────────────────────────────────────────────────────────────────────
def module_thinking(api: CharlieAPI):
    while True:
        header("THINKING ENGINE — System 2")
        print(c(C.GRAY, "  Structured reasoning: decisions, risks, problem breakdowns."))

        choice = menu("Thinking actions", {
            "list": "View all thinking logs",
            "decision": "New Decision Log",
            "risk": "New Risk Analysis",
            "problem": "New Problem Breakdown",
            "view": "View a thinking log",
        })

        if choice is None:
            return

        elif choice == "list":
            try:
                logs = api.get("/decision-logs/")
                print()
                if not logs:
                    ok("No thinking logs yet.")
                else:
                    for i, d in enumerate(logs, 1):
                        print_decision(d, i)
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice in ("decision", "risk", "problem"):
            log_type = {
                "decision": "decision",
                "risk": "risk_analysis",
                "problem": "problem_breakdown"
            }[choice]

            print()
            print(bold(f"  New {choice.replace('_', ' ').title()}"))
            divider()

            title = prompt("Title")
            context = prompt_optional("Context / Background")

            data = {"title": title, "log_type": log_type}
            if context: data["context"] = context

            if choice == "decision":
                print()
                print(c(C.GRAY, "  Describe the options you are considering (one per line, blank to finish):"))
                options = []
                while True:
                    opt = input(f"  {c(C.CYAN, 'Option')}: ").strip()
                    if not opt:
                        break
                    options.append(opt)
                if options:
                    data["options"] = options

                decision = prompt_optional("Your decision")
                rationale = prompt_optional("Rationale")
                expected = prompt_optional("Expected outcome")
                if decision: data["decision"] = decision
                if rationale: data["rationale"] = rationale
                if expected: data["expected_outcome"] = expected

            elif choice == "risk":
                risks = prompt_optional("Identified risks")
                mitigations = prompt_optional("Mitigations")
                if risks: data["risks"] = risks
                if mitigations: data["mitigations"] = mitigations

            elif choice == "problem":
                problem = prompt_optional("Problem statement")
                hypotheses = prompt_optional("Hypotheses")
                if problem: data["problem_statement"] = problem
                if hypotheses: data["hypotheses"] = hypotheses

            try:
                log = api.post("/decision-logs/", data)
                ok(f"Thinking log created (ID: {log['id']})")
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "view":
            try:
                logs = api.get("/decision-logs/")
                if not logs:
                    ok("No logs.")
                    continue
                print()
                for i, d in enumerate(logs, 1):
                    print_decision(d, i)
                print()
                idx = prompt_int("Log number to view", required=True)
                if not idx or idx < 1 or idx > len(logs):
                    warn("Invalid number.")
                    continue
                log = logs[idx - 1]
                d = api.get(f"/decision-logs/{log['id']}")
                print()
                print(bold(f"  {d['title']}"))
                divider()
                fields = [
                    ("Type", d.get("log_type")),
                    ("Context", d.get("context")),
                    ("Options", "\n    ".join(d.get("options") or [])),
                    ("Decision", d.get("decision")),
                    ("Rationale", d.get("rationale")),
                    ("Expected outcome", d.get("expected_outcome")),
                    ("Risks", d.get("risks")),
                    ("Mitigations", d.get("mitigations")),
                    ("Problem statement", d.get("problem_statement")),
                    ("Hypotheses", d.get("hypotheses")),
                    ("Created", fmt_date(d.get("created_at"))),
                ]
                for label, val in fields:
                    if val:
                        print(f"  {c(C.CYAN, label+':')}")
                        print(f"    {val}")
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Knowledge (Notes)
# ─────────────────────────────────────────────────────────────────────────────
def module_knowledge(api: CharlieAPI):
    while True:
        header("KNOWLEDGE — Second Brain (PARA)")

        choice = menu("Knowledge actions", {
            "list": "List notes",
            "add": "Create new note",
            "view": "View a note",
            "search": "Search notes",
        })

        if choice is None:
            return

        elif choice == "list":
            cat = prompt_choice(
                "Filter by category",
                ["all", "projects", "areas", "resources", "archive"],
                "all"
            )
            params = {} if cat == "all" else {"category": cat}
            try:
                notes = api.get("/notes/", params)
                print()
                if not notes:
                    ok("No notes found.")
                else:
                    for i, n in enumerate(notes, 1):
                        print_note(n, i)
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "add":
            print()
            title = prompt("Note title")
            category = prompt_choice(
                "PARA category",
                ["projects", "areas", "resources", "archive"],
                "resources"
            )
            print(c(C.GRAY, "  Enter note content (type END on a new line to finish):"))
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            content = "\n".join(lines)
            tags_raw = prompt_optional("Tags (comma-separated)")
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

            data = {
                "title": title,
                "category": category,
                "content": content,
                "tags": tags,
            }

            try:
                note = api.post("/notes/", data)
                ok(f"Note created (ID: {note['id']})")
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "view":
            try:
                notes = api.get("/notes/")
                if not notes:
                    ok("No notes.")
                    continue
                print()
                for i, n in enumerate(notes, 1):
                    print_note(n, i)
                print()
                idx = prompt_int("Note number to view", required=True)
                if not idx or idx < 1 or idx > len(notes):
                    warn("Invalid number.")
                    continue
                note = api.get(f"/notes/{notes[idx-1]['id']}")
                print()
                print(bold(f"  {note['title']}"))
                print(c(C.CYAN, f"  Category: {note.get('category', '')}"))
                if note.get("tags"):
                    print(c(C.GRAY, f"  Tags: {', '.join(note['tags'])}"))
                divider()
                print(note.get("content", ""))
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

        elif choice == "search":
            query = prompt("Search term")
            try:
                notes = api.get("/notes/", {"search": query})
                print()
                if not notes:
                    ok("No results.")
                else:
                    for i, n in enumerate(notes, 1):
                        print_note(n, i)
                input(c(C.GRAY, "\n  Press Enter..."))
            except Exception as e:
                err(f"Failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Module: Weekly Review
# ─────────────────────────────────────────────────────────────────────────────
def module_review(api: CharlieAPI):
    header("WEEKLY REVIEW — Feedback System")

    try:
        data = api.get("/reviews/weekly")
    except Exception as e:
        err(f"Could not load review data: {e}")
        input(c(C.GRAY, "\n  Press Enter..."))
        return

    print()
    print(bold("  📊 This Week's Metrics"))
    divider()

    metrics = [
        ("Inbox pending",        data.get("inbox_pending", 0),       C.YELLOW),
        ("Tasks completed",      data.get("tasks_completed", 0),     C.GREEN),
        ("Next actions",         data.get("next_actions", 0),        C.CYAN),
        ("Active projects",      data.get("active_projects", 0),     C.BLUE),
        ("Decisions logged",     data.get("decisions_logged", 0),    C.CYAN),
        ("Notes created",        data.get("notes_created", 0),       C.CYAN),
    ]

    for label, val, color in metrics:
        bar = "█" * min(int(val), 20) if isinstance(val, int) else ""
        print(f"  {label:<25} {c(color, str(val))}  {c(C.GRAY, bar)}")

    if data.get("estimation_accuracy") is not None:
        acc = data["estimation_accuracy"]
        color = C.GREEN if acc >= 80 else C.YELLOW if acc >= 60 else C.RED
        print(f"  {'Estimation accuracy':<25} {c(color, f'{acc:.0f}%')}")

    print()
    print(bold("  ✅ Weekly Review Checklist"))
    divider()
    checklist = [
        "Process all inbox items to zero",
        "Review all active projects — is each moving forward?",
        "Review Next Actions list — still relevant?",
        "Review Waiting For list — follow up if needed",
        "Review Someday/Maybe — promote or delete",
        "Review calendar for the coming week",
        "Identify the 3 most important outcomes for next week",
        "Capture any open loops still in your head",
    ]
    for item in checklist:
        done = confirm(f"  {item}")
        if done:
            ok(item)
        else:
            warn(f"Pending: {item}")

    print()
    ok("Weekly review complete.")
    input(c(C.GRAY, "\n  Press Enter..."))

# ─────────────────────────────────────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────────────────────────────────────
def main_menu(api: CharlieAPI):
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print()
        print(c(C.BLUE, "  ╔══════════════════════════════════════════════════════╗"))
        print(c(C.BLUE, "  ║") + c(C.BOLD, "   🧠  Charlie — Cognitive Operating System         ") + c(C.BLUE, "║"))
        print(c(C.BLUE, "  ╚══════════════════════════════════════════════════════╝"))
        print()

        # Quick stats
        try:
            inbox = api.get("/inbox/", {"status": "pending"})
            tasks = api.get("/tasks/", {"status": "next"})
            inbox_count = len(inbox)
            task_count = len(tasks)
            print(f"  {c(C.YELLOW, f'📥 Inbox: {inbox_count}')}   {c(C.GREEN, f'✅ Next: {task_count}')}")
        except Exception:
            pass

        choice = menu("Main Menu", {
            "capture": "⚡  Quick Capture  — add to inbox instantly",
            "inbox":   "📥  Inbox          — clarify and process",
            "tasks":   "✅  Tasks          — next actions & done",
            "projects":"📁  Projects        — manage projects",
            "thinking":"🧠  Thinking        — decisions & analysis",
            "knowledge":"📚  Knowledge       — notes & second brain",
            "review":  "📊  Weekly Review   — feedback & metrics",
        })

        if choice is None:
            print()
            print(c(C.GRAY, "  Goodbye. Keep thinking clearly."))
            print()
            sys.exit(0)

        elif choice == "capture":
            module_capture(api)
        elif choice == "inbox":
            module_inbox(api)
        elif choice == "tasks":
            module_tasks(api)
        elif choice == "projects":
            module_projects(api)
        elif choice == "thinking":
            module_thinking(api)
        elif choice == "knowledge":
            module_knowledge(api)
        elif choice == "review":
            module_review(api)

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Charlie CLI")
    parser.add_argument("--api", default=DEFAULT_API, help="Backend API URL")
    parser.add_argument("--check", action="store_true", help="Check API connectivity and exit")
    args = parser.parse_args()

    api = CharlieAPI(args.api)

    # Check connectivity
    print()
    print(c(C.BLUE, "  🧠  Charlie CLI"))
    print(c(C.GRAY, f"  Connecting to {args.api}..."))

    if not api.health():
        warn(f"Backend not reachable at {args.api}")
        print()
        print(c(C.GRAY, "  Start the backend first:"))
        print(c(C.CYAN, "    bash start-local.sh start"))
        print(c(C.GRAY, "  Or run in backend-only mode:"))
        print(c(C.CYAN, "    cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8085"))
        print()
        if args.check:
            sys.exit(1)
        if not confirm("Backend is not running. Continue anyway?"):
            sys.exit(1)
    else:
        ok(f"Connected to {args.api}")

    if args.check:
        sys.exit(0)

    try:
        main_menu(api)
    except KeyboardInterrupt:
        print()
        print(c(C.GRAY, "\n  Interrupted. Goodbye."))
        print()
        sys.exit(0)

if __name__ == "__main__":
    main()
