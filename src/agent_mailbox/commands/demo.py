from __future__ import annotations

from typing import Annotated

import typer


def command(
    repo_a_path: Annotated[str, typer.Option("--repo-a-path")] = "<repo-a-path>",
    repo_b_path: Annotated[str, typer.Option("--repo-b-path")] = "<repo-b-path>",
    agent_a: Annotated[str, typer.Option("--agent-a")] = "codex-repo-a",
    agent_b: Annotated[str, typer.Option("--agent-b")] = "claude-repo-b",
    repo_a_name: Annotated[str, typer.Option("--repo-a-name")] = "repo-a",
    repo_b_name: Annotated[str, typer.Option("--repo-b-name")] = "repo-b",
    thread: Annotated[str, typer.Option("--thread")] = "demo-thread",
) -> None:
    lines = [
        "agent-mailbox end-to-end demo",
        "",
        "Terminal 1",
        f"cd {repo_a_path}",
        (
            "agent-mailbox ask "
            f"--from-agent {agent_a} --to-agent {agent_b} --thread {thread} "
            '--subject "Cross-repo question" '
            '--question "Where is the relevant logic?" '
            f"--repo {repo_a_name}"
        ),
        "",
        "Terminal 2",
        f"cd {repo_b_path}",
        f"agent-mailbox inbox --for-agent {agent_b} --mark-seen --json",
        f"agent-mailbox claim --thread {thread} --from-agent {agent_b} --repo {repo_b_name}",
        (
            "agent-mailbox answer "
            f"--thread {thread} --from-agent {agent_b} --repo {repo_b_name} "
            '--summary "The logic lives in src/example.py." '
            "--evidence src/example.py:10-42 "
            "--confidence high"
        ),
        "",
        "Terminal 1",
        f"cd {repo_a_path}",
        f"agent-mailbox thread --thread {thread} --json",
        (
            f"agent-mailbox close --thread {thread} --from-agent {agent_a} "
            f"--repo {repo_a_name} --resolution accepted"
        ),
    ]
    typer.echo("\n".join(lines))
