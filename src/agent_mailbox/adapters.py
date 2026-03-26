from __future__ import annotations

from typing import Literal

from agent_mailbox.models import ThreadView

AdapterTool = Literal["claude", "codex"]


def render_prompt(tool: AdapterTool, agent: str, threads: list[ThreadView]) -> str:
    intro = _render_intro(tool, agent)
    if not threads:
        return (
            f"{intro}\n\n"
            f"No open agent-mailbox threads are currently addressed to {agent}.\n"
            "If you need cross-repo information, ask a targeted question with:\n"
            f"agent-mailbox ask --from-agent {agent} --to-agent <target-agent> --thread <thread-id> "
            '--subject "<subject>" --question "<question>" --repo <repo>\n'
        )

    thread_lines = [
        f"- {thread.thread_id}: {thread.subject or '(no subject)'} [{thread.state}]"
        for thread in threads
    ]
    first_thread = threads[0]
    next_steps = [
        "If you are taking one of these threads, claim it before investigating:",
        f"agent-mailbox claim --thread {first_thread.thread_id} --from-agent {agent} --repo <repo>",
        "When you have an answer, respond with evidence:",
        (
            "agent-mailbox answer "
            f"--thread {first_thread.thread_id} --from-agent {agent} --repo <repo> "
            '--summary "<summary>" --evidence <path:lines> --confidence high'
        ),
    ]
    return f"{intro}\n\n" + "\n".join(thread_lines + [""] + next_steps) + "\n"


def _render_intro(tool: AdapterTool, agent: str) -> str:
    if tool == "claude":
        return (
            f"Agent-board inbox for {agent}.\n"
            "Use this as ephemeral cross-repo coordination context, not as durable project policy."
        )
    return (
        f"Agent-board context for {agent}.\n"
        "Check assigned mailbox threads before planning cross-repo work."
    )
