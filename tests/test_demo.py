from __future__ import annotations

from typer.testing import CliRunner

from agent_board.cli import app

runner = CliRunner()


def test_demo_command_prints_two_terminal_walkthrough() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            [
                "demo",
                "--repo-a-path",
                "/tmp/repo-a",
                "--repo-b-path",
                "/tmp/repo-b",
                "--agent-a",
                "codex-repo-a",
                "--agent-b",
                "claude-repo-b",
                "--thread",
                "demo-thread",
            ],
        )

        assert result.exit_code == 0
        assert "Terminal 1" in result.stdout
        assert "Terminal 2" in result.stdout
        assert "cd /tmp/repo-a" in result.stdout
        assert "cd /tmp/repo-b" in result.stdout
        assert "agent-board ask" in result.stdout
        assert "agent-board inbox --for-agent claude-repo-b --mark-seen --json" in result.stdout
        assert "agent-board claim --thread demo-thread" in result.stdout
        assert "agent-board answer" in result.stdout
        assert "agent-board close --thread demo-thread" in result.stdout
