from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agent_board.cli import app

runner = CliRunner()


def test_inbox_marks_seen_and_tracks_unread() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

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
                "repo-b-one",
                "--subject",
                "First question",
                "--question",
                "How does repo-b do x?",
                "--repo",
                "repo-a",
            ],
        )
        assert ask_result.exit_code == 0

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
        assert payload["threads"][0]["unread"] is True
        assert payload["cursor"] is None

        mark_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "inbox",
                "--for-agent",
                "claude-repo-b",
                "--mark-seen",
                "--json",
            ],
        )
        assert mark_result.exit_code == 0
        payload = json.loads(mark_result.stdout)
        assert payload["cursor"] is not None
        assert payload["threads"][0]["unread"] is True

        second_inbox = runner.invoke(
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
        assert second_inbox.exit_code == 0
        payload = json.loads(second_inbox.stdout)
        assert payload["threads"][0]["unread"] is False

        second_ask = runner.invoke(
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
                "repo-b-two",
                "--subject",
                "Second question",
                "--question",
                "How does repo-b do y?",
                "--repo",
                "repo-a",
            ],
        )
        assert second_ask.exit_code == 0

        third_inbox = runner.invoke(
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
        assert third_inbox.exit_code == 0
        payload = json.loads(third_inbox.stdout)
        unread_threads = {item["thread_id"] for item in payload["threads"] if item["unread"]}
        assert unread_threads == {"repo-b-two"}


def test_cursor_command_reports_and_clears_cursor() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

        assert runner.invoke(
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
                "repo-b-one",
                "--subject",
                "First question",
                "--question",
                "How does repo-b do x?",
                "--repo",
                "repo-a",
            ],
        ).exit_code == 0

        assert runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "inbox",
                "--for-agent",
                "claude-repo-b",
                "--mark-seen",
            ],
        ).exit_code == 0

        cursor_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "cursor",
                "--for-agent",
                "claude-repo-b",
                "--json",
            ],
        )
        assert cursor_result.exit_code == 0
        payload = json.loads(cursor_result.stdout)
        assert payload["cursor"] is not None
        assert payload["agent"] == "claude-repo-b"

        clear_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "cursor",
                "--for-agent",
                "claude-repo-b",
                "--clear",
                "--json",
            ],
        )
        assert clear_result.exit_code == 0
        payload = json.loads(clear_result.stdout)
        assert payload["cleared"] is True
        assert payload["cursor"] is None


def test_cursor_human_output_is_readable() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

        empty_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "cursor",
                "--for-agent",
                "claude-repo-b",
            ],
        )
        assert empty_result.exit_code == 0
        assert "No cursor set for claude-repo-b" in empty_result.stdout

        assert runner.invoke(
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
                "repo-b-one",
                "--subject",
                "First question",
                "--question",
                "How does repo-b do x?",
                "--repo",
                "repo-a",
            ],
        ).exit_code == 0

        assert runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "inbox",
                "--for-agent",
                "claude-repo-b",
                "--mark-seen",
            ],
        ).exit_code == 0

        cursor_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "cursor",
                "--for-agent",
                "claude-repo-b",
            ],
        )
        assert cursor_result.exit_code == 0
        assert "Cursor for claude-repo-b" in cursor_result.stdout
        assert "Last seen:" in cursor_result.stdout
        assert "Path:" in cursor_result.stdout

        clear_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "cursor",
                "--for-agent",
                "claude-repo-b",
                "--clear",
            ],
        )
        assert clear_result.exit_code == 0
        assert "Cleared cursor for claude-repo-b" in clear_result.stdout
