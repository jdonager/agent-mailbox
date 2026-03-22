from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agent_board.cli import app

runner = CliRunner()


def read_events(board_root: Path) -> list[dict[str, object]]:
    events_dir = board_root / "events"
    return [
        json.loads(path.read_text())
        for path in sorted(events_dir.rglob("*.json"))
    ]


def test_ask_persists_question_event() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

        result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "ask",
                "--from-agent",
                "codex-repo-a",
                "--to-agent",
                "claude-repo-b",
                "--thread",
                "repo-b-jwt-kid-validation",
                "--subject",
                "JWT kid validation path",
                "--question",
                "How does repo-b validate rotated JWT kid values?",
                "--repo",
                "repo-a",
                "--branch",
                "feature/token-rotation",
                "--commit",
                "abc1234",
                "--json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["type"] == "question"
        events = read_events(board_root)
        assert len(events) == 1
        body = events[0]["body"]
        assert isinstance(body, dict)
        assert body["subject"] == "JWT kid validation path"


def test_thread_lifecycle_transitions_from_open_to_closed() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"
        thread_id = "repo-b-jwt-kid-validation"

        ask_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "ask",
                "--from-agent",
                "codex-repo-a",
                "--to-agent",
                "claude-repo-b",
                "--thread",
                thread_id,
                "--subject",
                "JWT kid validation path",
                "--question",
                "How does repo-b validate rotated JWT kid values?",
                "--repo",
                "repo-a",
                "--json",
            ],
        )
        assert ask_result.exit_code == 0

        thread_result = runner.invoke(
            app,
            ["--board-root", str(board_root), "thread", "--thread", thread_id, "--json"],
        )
        assert json.loads(thread_result.stdout)["state"] == "open"

        claim_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "claim",
                "--thread",
                thread_id,
                "--from-agent",
                "claude-repo-b",
                "--repo",
                "repo-b",
                "--json",
            ],
        )
        assert claim_result.exit_code == 0

        thread_result = runner.invoke(
            app,
            ["--board-root", str(board_root), "thread", "--thread", thread_id, "--json"],
        )
        assert json.loads(thread_result.stdout)["state"] == "claimed"

        answer_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "answer",
                "--thread",
                thread_id,
                "--from-agent",
                "claude-repo-b",
                "--repo",
                "repo-b",
                "--summary",
                "Validation occurs in middleware/auth.ts via keyResolver().",
                "--evidence",
                "middleware/auth.ts:44-91",
                "--confidence",
                "high",
                "--json",
            ],
        )
        assert answer_result.exit_code == 0

        thread_result = runner.invoke(
            app,
            ["--board-root", str(board_root), "thread", "--thread", thread_id, "--json"],
        )
        assert json.loads(thread_result.stdout)["state"] == "answered"

        close_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "close",
                "--thread",
                thread_id,
                "--from-agent",
                "codex-repo-a",
                "--repo",
                "repo-a",
                "--resolution",
                "accepted",
                "--json",
            ],
        )
        assert close_result.exit_code == 0

        thread_result = runner.invoke(
            app,
            ["--board-root", str(board_root), "thread", "--thread", thread_id, "--json"],
        )
        assert json.loads(thread_result.stdout)["state"] == "closed"


def test_inbox_returns_only_active_questions_for_target_agent() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

        first_question = [
            "--board-root",
            str(board_root),
            "ask",
            "--from-agent",
            "codex-repo-a",
            "--to-agent",
            "claude-repo-b",
            "--thread",
            "repo-b-config-question",
            "--subject",
            "Config lookup",
            "--question",
            "Where is config resolved?",
            "--repo",
            "repo-a",
        ]
        second_question = [
            "--board-root",
            str(board_root),
            "ask",
            "--from-agent",
            "codex-repo-a",
            "--to-agent",
            "claude-repo-c",
            "--thread",
            "repo-c-schema-question",
            "--subject",
            "Schema lookup",
            "--question",
            "Where is schema resolved?",
            "--repo",
            "repo-a",
        ]

        assert runner.invoke(app, first_question).exit_code == 0
        assert runner.invoke(app, second_question).exit_code == 0

        inbox_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "inbox",
                "--for-agent",
                "claude-repo-b",
                "--json",
            ],
        )

        assert inbox_result.exit_code == 0
        payload = json.loads(inbox_result.stdout)
        assert len(payload["threads"]) == 1
        assert payload["threads"][0]["thread_id"] == "repo-b-config-question"
