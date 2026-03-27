from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_mailbox.cli import app
from agent_mailbox.events import build_question_event
from agent_mailbox.models import Event
from agent_mailbox.threads import build_inbox

runner = CliRunner()


# --- Model validation ---


def test_thread_id_rejects_forward_slash() -> None:
    with pytest.raises(ValueError, match="path separators"):
        Event.model_validate(
            {
                "id": "01TEST",
                "type": "question",
                "thread_id": "repo-a/bad-id",
                "from": {"agent": "a", "repo": "r"},
                "created_at": "2026-03-21T13:00:00Z",
                "body": {"subject": "s", "question": "q"},
            }
        )


def test_thread_id_rejects_backslash() -> None:
    with pytest.raises(ValueError, match="path separators"):
        Event.model_validate(
            {
                "id": "01TEST",
                "type": "question",
                "thread_id": "repo-a\\bad-id",
                "from": {"agent": "a", "repo": "r"},
                "created_at": "2026-03-21T13:00:00Z",
                "body": {"subject": "s", "question": "q"},
            }
        )


def test_namespace_validation_rejects_invalid_chars() -> None:
    with pytest.raises(ValueError, match="namespace"):
        Event.model_validate(
            {
                "id": "01TEST",
                "type": "question",
                "thread_id": "valid-id",
                "namespace": "bad namespace!",
                "from": {"agent": "a", "repo": "r"},
                "created_at": "2026-03-21T13:00:00Z",
                "body": {"subject": "s", "question": "q"},
            }
        )


def test_namespace_validation_accepts_valid_names() -> None:
    event = Event.model_validate(
        {
            "id": "01TEST",
            "type": "question",
            "thread_id": "valid-id",
            "namespace": "whitedoor-schema",
            "from": {"agent": "a", "repo": "r"},
            "created_at": "2026-03-21T13:00:00Z",
            "body": {"subject": "s", "question": "q"},
        }
    )
    assert event.namespace == "whitedoor-schema"


def test_namespace_allows_none() -> None:
    event = Event.model_validate(
        {
            "id": "01TEST",
            "type": "question",
            "thread_id": "valid-id",
            "from": {"agent": "a", "repo": "r"},
            "created_at": "2026-03-21T13:00:00Z",
            "body": {"subject": "s", "question": "q"},
        }
    )
    assert event.namespace is None


# --- Event builders ---


def test_question_event_defaults_namespace_to_repo() -> None:
    event = build_question_event(
        thread_id="reload-validation",
        from_agent="agent-a",
        to_agent="agent-b",
        subject="Test",
        question="Does it work?",
        repo="whitedoor-schema",
    )
    assert event.namespace == "whitedoor-schema"


def test_question_event_explicit_namespace_overrides_repo() -> None:
    event = build_question_event(
        thread_id="reload-validation",
        from_agent="agent-a",
        to_agent="agent-b",
        subject="Test",
        question="Does it work?",
        repo="whitedoor-schema",
        namespace="custom-ns",
    )
    assert event.namespace == "custom-ns"


# --- Inbox filtering ---


def test_inbox_filters_by_namespace() -> None:
    events = [
        build_question_event(
            thread_id="reload-validation",
            from_agent="agent-a",
            to_agent="agent-b",
            subject="Schema reload",
            question="How?",
            repo="whitedoor-schema",
        ),
        build_question_event(
            thread_id="auth-flow",
            from_agent="agent-a",
            to_agent="agent-b",
            subject="Auth flow",
            question="Where?",
            repo="hermes-editor",
        ),
    ]
    all_threads = build_inbox(events, "agent-b")
    assert len(all_threads) == 2

    schema_threads = build_inbox(events, "agent-b", namespace="whitedoor-schema")
    assert len(schema_threads) == 1
    assert schema_threads[0].thread_id == "reload-validation"
    assert schema_threads[0].namespace == "whitedoor-schema"

    editor_threads = build_inbox(events, "agent-b", namespace="hermes-editor")
    assert len(editor_threads) == 1
    assert editor_threads[0].thread_id == "auth-flow"


def test_inbox_namespace_none_returns_all() -> None:
    events = [
        build_question_event(
            thread_id="t1",
            from_agent="a",
            to_agent="b",
            subject="S1",
            question="Q1",
            repo="repo-x",
        ),
        build_question_event(
            thread_id="t2",
            from_agent="a",
            to_agent="b",
            subject="S2",
            question="Q2",
            repo="repo-y",
        ),
    ]
    threads = build_inbox(events, "b", namespace=None)
    assert len(threads) == 2


# --- CLI integration ---


def test_ask_cli_sets_namespace_from_repo() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        result = runner.invoke(
            app,
            [
                "--board-root", str(board_root),
                "ask",
                "--from-agent", "agent-a",
                "--to-agent", "agent-b",
                "--thread", "reload-validation",
                "--subject", "Schema reload",
                "--question", "How does it work?",
                "--repo", "whitedoor-schema",
                "--json",
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["namespace"] == "whitedoor-schema"


def test_ask_cli_explicit_namespace() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        result = runner.invoke(
            app,
            [
                "--board-root", str(board_root),
                "ask",
                "--from-agent", "agent-a",
                "--to-agent", "agent-b",
                "--thread", "reload-validation",
                "--subject", "Schema reload",
                "--question", "How does it work?",
                "--repo", "whitedoor-schema",
                "--namespace", "custom-ns",
                "--json",
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["namespace"] == "custom-ns"


def test_inbox_cli_namespace_filter() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        base = ["--board-root", str(board_root)]

        # Create two questions in different namespaces
        runner.invoke(app, [
            *base, "ask",
            "--from-agent", "a", "--to-agent", "b",
            "--thread", "t1", "--subject", "S1", "--question", "Q1",
            "--repo", "repo-x",
        ])
        runner.invoke(app, [
            *base, "ask",
            "--from-agent", "a", "--to-agent", "b",
            "--thread", "t2", "--subject", "S2", "--question", "Q2",
            "--repo", "repo-y",
        ])

        # No filter: both visible
        result = runner.invoke(app, [*base, "inbox", "--for-agent", "b", "--json"])
        assert len(json.loads(result.stdout)["threads"]) == 2

        # Filter by namespace
        result = runner.invoke(app, [
            *base, "inbox", "--for-agent", "b", "--namespace", "repo-x", "--json",
        ])
        threads = json.loads(result.stdout)["threads"]
        assert len(threads) == 1
        assert threads[0]["thread_id"] == "t1"
        assert threads[0]["namespace"] == "repo-x"


def test_thread_view_shows_namespace() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        base = ["--board-root", str(board_root)]

        runner.invoke(app, [
            *base, "ask",
            "--from-agent", "a", "--to-agent", "b",
            "--thread", "t1", "--subject", "S1", "--question", "Q1",
            "--repo", "my-repo",
        ])

        result = runner.invoke(app, [*base, "thread", "--thread", "t1", "--json"])
        payload = json.loads(result.stdout)
        assert payload["namespace"] == "my-repo"


def test_claim_inherits_namespace_from_question() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        base = ["--board-root", str(board_root)]

        runner.invoke(app, [
            *base, "ask",
            "--from-agent", "a", "--to-agent", "b",
            "--thread", "t1", "--subject", "S1", "--question", "Q1",
            "--repo", "my-repo", "--namespace", "custom-ns",
        ])

        result = runner.invoke(app, [
            *base, "claim",
            "--thread", "t1", "--from-agent", "b", "--repo", "other-repo",
            "--json",
        ])
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["namespace"] == "custom-ns"
