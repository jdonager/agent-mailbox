from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from agent_board.events import build_question_event
from agent_board.models import Event
from agent_board.storage import BoardStorage


def test_event_expiry_uses_created_at_plus_ttl_seconds() -> None:
    event = Event.model_validate(
        {
            "id": "01TESTEVENT",
            "type": "question",
            "thread_id": "repo-b-jwt-kid-validation",
            "from": {"agent": "codex-repo-a", "repo": "repo-a"},
            "to": {"agent": "claude-repo-b", "repo": "repo-b"},
            "created_at": "2026-03-21T13:00:00Z",
            "ttl_seconds": 60,
            "schema_version": 1,
            "body": {"subject": "Question", "question": "Where?"},
        }
    )

    assert event.is_expired(datetime(2026, 3, 21, 13, 1, 0, tzinfo=UTC)) is True
    assert event.is_expired(datetime(2026, 3, 21, 13, 0, 59, tzinfo=UTC)) is False


def test_storage_filename_contains_timestamp_type_and_thread_id() -> None:
    storage = BoardStorage(Path("/tmp/agent-board-test"))
    event = Event.model_validate(
        {
            "id": "01TESTEVENT",
            "type": "question",
            "thread_id": "repo-b-jwt-kid-validation",
            "from": {"agent": "codex-repo-a", "repo": "repo-a"},
            "to": {"agent": "claude-repo-b", "repo": "repo-b"},
            "created_at": "2026-03-21T13:00:00Z",
            "ttl_seconds": 60,
            "schema_version": 1,
            "body": {"subject": "Question", "question": "Where?"},
        }
    )

    path = storage.event_path(event)

    assert path.name == (
        "2026-03-21T13-00-00Z__01TESTEVENT__question__repo-b-jwt-kid-validation.json"
    )


def test_question_subject_must_be_120_chars_or_less() -> None:
    with pytest.raises(ValueError):
        build_question_event(
            thread_id="repo-b-jwt-kid-validation",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="x" * 121,
            question="How does repo-b validate rotated JWT kid values?",
            repo="repo-a",
            ttl_seconds=1800,
        )


def test_thread_id_must_be_80_chars_or_less() -> None:
    with pytest.raises(ValueError):
        build_question_event(
            thread_id="x" * 81,
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="JWT kid validation path",
            question="How does repo-b validate rotated JWT kid values?",
            repo="repo-a",
            ttl_seconds=1800,
        )
