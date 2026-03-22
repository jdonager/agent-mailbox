from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from agent_board.cli import app
from agent_board.config import load_settings
from agent_board.events import build_close_event, build_question_event
from agent_board.storage import BoardStorage

runner = CliRunner()


def write_config(board_root: Path) -> None:
    config_path = board_root / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "board_root": str(board_root),
                "archive_closed_after_days": 7,
                "archive_expired_after_days": 3,
                "prune_archived_after_days": 30,
            }
        ),
        encoding="utf-8",
    )


def test_gc_archives_closed_and_expired_threads() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        write_config(board_root)
        settings = load_settings(board_root)
        storage = BoardStorage(
            settings.board_root,
            max_event_size_bytes=settings.max_event_size_bytes,
        )

        old = (
            datetime.now(UTC) - timedelta(days=10)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        closed_question = build_question_event(
            thread_id="closed-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Old closed",
            question="Question",
            repo="repo-a",
            ttl_seconds=settings.default_question_ttl_seconds,
        ).model_copy(update={"created_at": old})
        storage.write_event(closed_question)
        closed_close = build_close_event(
            thread_id="closed-thread",
            in_reply_to=closed_question.id,
            from_agent="codex-repo-a",
            repo="repo-a",
            resolution="accepted",
            ttl_seconds=settings.default_close_ttl_seconds,
        ).model_copy(update={"created_at": old})
        storage.write_event(closed_close)

        expired_question = build_question_event(
            thread_id="expired-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Old expired",
            question="Question",
            repo="repo-a",
            ttl_seconds=60,
        ).model_copy(update={"created_at": old})
        storage.write_event(expired_question)

        active_question = build_question_event(
            thread_id="active-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Recent active",
            question="Question",
            repo="repo-a",
            ttl_seconds=settings.default_answer_ttl_seconds,
        )
        storage.write_event(active_question)

        result = runner.invoke(
            app,
            ["--board-root", str(board_root), "gc", "--json"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        archived_threads = {item["thread_id"] for item in payload["archived_threads"]}
        assert archived_threads == {"closed-thread", "expired-thread"}
        assert payload["archived_event_count"] == 3
        assert payload["prune_after_days"] == 30

        active_events = storage.list_events()
        assert {event.thread_id for event in active_events} == {"active-thread"}

        archived_events = storage.list_events(archived=True)
        assert {event.thread_id for event in archived_events} == {"closed-thread", "expired-thread"}


def test_gc_dry_run_does_not_move_files() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        write_config(board_root)
        settings = load_settings(board_root)
        storage = BoardStorage(
            settings.board_root,
            max_event_size_bytes=settings.max_event_size_bytes,
        )

        old = (
            datetime.now(UTC) - timedelta(days=10)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        expired_question = build_question_event(
            thread_id="expired-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Old expired",
            question="Question",
            repo="repo-a",
            ttl_seconds=60,
        ).model_copy(update={"created_at": old})
        storage.write_event(expired_question)

        result = runner.invoke(
            app,
            ["--board-root", str(board_root), "gc", "--dry-run", "--json"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["dry_run"] is True
        assert payload["archived_event_count"] == 0
        assert {event.thread_id for event in storage.list_events()} == {"expired-thread"}
        assert storage.list_events(archived=True) == []


def test_gc_prunes_old_archived_events() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        write_config(board_root)
        settings = load_settings(board_root)
        storage = BoardStorage(
            settings.board_root,
            max_event_size_bytes=settings.max_event_size_bytes,
        )

        archived_old = (
            datetime.now(UTC) - timedelta(days=40)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        archived_question = build_question_event(
            thread_id="archived-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Archived question",
            question="Question",
            repo="repo-a",
            ttl_seconds=60,
        ).model_copy(update={"created_at": archived_old})
        storage.write_event(archived_question, archived=True)

        result = runner.invoke(
            app,
            ["--board-root", str(board_root), "gc", "--prune", "--json"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["pruned_event_count"] == 1
        assert storage.list_events(archived=True) == []


def test_gc_human_output_is_readable() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        write_config(board_root)
        settings = load_settings(board_root)
        storage = BoardStorage(
            settings.board_root,
            max_event_size_bytes=settings.max_event_size_bytes,
        )

        old = (
            datetime.now(UTC) - timedelta(days=10)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        expired_question = build_question_event(
            thread_id="expired-thread",
            from_agent="codex-repo-a",
            to_agent="claude-repo-b",
            subject="Old expired",
            question="Question",
            repo="repo-a",
            ttl_seconds=60,
        ).model_copy(update={"created_at": old})
        storage.write_event(expired_question)

        result = runner.invoke(
            app,
            ["--board-root", str(board_root), "gc", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "agent-board gc" in result.stdout
        assert "expired-thread" in result.stdout
        assert "Dry run only" in result.stdout
