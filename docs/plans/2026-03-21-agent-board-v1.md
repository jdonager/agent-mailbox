# Agent Mailbox V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a minimal Python CLI that stores append-only JSON events for cross-repo questions, claims, answers, and closes.

**Architecture:** The CLI writes and reads event files under a configurable board root, derives thread state from the event log, and exposes a small command surface for human and machine use. Pydantic models validate event payloads, while the storage layer owns atomic writes and event discovery.

**Tech Stack:** Python 3.11+, Typer, Pydantic, Rich, ULID, pytest

---

### Task 1: Project Skeleton

**Files:**
- Create: `src/agent_mailbox/__init__.py`
- Create: `src/agent_mailbox/cli.py`
- Create: `src/agent_mailbox/config.py`
- Create: `src/agent_mailbox/models.py`
- Create: `src/agent_mailbox/storage.py`
- Create: `src/agent_mailbox/events.py`
- Create: `src/agent_mailbox/threads.py`
- Create: `tests/test_cli_flow.py`
- Create: `.gitignore`

**Step 1: Write the failing tests**

Add tests that prove:
- `ask` creates a persisted `question` event.
- `claim`, `answer`, and `close` drive thread state transitions.
- `inbox` only returns active work for the addressed agent.

**Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli_flow.py -q`
Expected: FAIL because the package and CLI modules do not exist yet.

**Step 3: Write the minimal implementation**

Implement:
- a configurable board root
- event models and builders
- atomic file writes
- thread state derivation
- Typer commands for `ask`, `inbox`, `claim`, `answer`, `close`, and `thread`

**Step 4: Run the focused tests**

Run: `uv run pytest tests/test_cli_flow.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: scaffold agent-mailbox v1 cli"
```

### Task 2: Verification and Polish

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `tests/test_models.py`

**Step 1: Write the failing tests**

Add tests for:
- event expiry logic
- filename generation stability
- validation constraints that matter for the v1 contract

**Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_models.py -q`
Expected: FAIL due to missing validation behavior.

**Step 3: Write the minimal implementation**

Tighten validation and align the docs with the implemented command behavior.

**Step 4: Run the full test suite**

Run: `uv run pytest -q`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "test: cover agent-mailbox event validation"
```
