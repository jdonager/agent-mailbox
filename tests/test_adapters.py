from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agent_mailbox.cli import app

runner = CliRunner()


def test_claude_prompt_includes_active_thread_and_next_steps() -> None:
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
                "repo-b-config-question",
                "--subject",
                "Config lookup",
                "--question",
                "Where is config resolved?",
                "--repo",
                "repo-a",
            ],
        )
        assert ask_result.exit_code == 0

        prompt_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "prompt",
                "--tool",
                "claude",
                "--agent",
                "claude-repo-b",
            ],
        )

        assert prompt_result.exit_code == 0
        assert "Agent-board inbox for claude-repo-b" in prompt_result.stdout
        assert "repo-b-config-question" in prompt_result.stdout
        assert "agent-mailbox claim --thread repo-b-config-question" in prompt_result.stdout


def test_codex_prompt_handles_empty_inbox() -> None:
    with runner.isolated_filesystem():
        board_root = Path.cwd() / ".board"

        prompt_result = runner.invoke(
            app,
            [
                "--board-root",
                str(board_root),
                "prompt",
                "--tool",
                "codex",
                "--agent",
                "codex-repo-a",
            ],
        )

        assert prompt_result.exit_code == 0
        assert "No open agent-mailbox threads are currently addressed to codex-repo-a." in (
            prompt_result.stdout
        )
        assert "agent-mailbox ask" in prompt_result.stdout
