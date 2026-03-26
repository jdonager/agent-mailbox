from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.commands._common import emit, get_settings, get_storage
from agent_mailbox.events import build_answer_event
from agent_mailbox.threads import latest_question


def command(
    context: typer.Context,
    thread: Annotated[str, typer.Option("--thread")],
    from_agent: Annotated[str, typer.Option("--from-agent")],
    repo: Annotated[str, typer.Option("--repo")],
    summary: Annotated[str, typer.Option("--summary")],
    evidence: Annotated[list[str] | None, typer.Option("--evidence")] = None,
    confidence: Annotated[str, typer.Option("--confidence")] = "medium",
    branch: Annotated[str | None, typer.Option("--branch")] = None,
    commit: Annotated[str | None, typer.Option("--commit")] = None,
    ttl: Annotated[int | None, typer.Option("--ttl", help="TTL in seconds; omit for no expiration")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    settings = get_settings(context)
    storage = get_storage(context)
    thread_events = storage.list_thread_events(thread)
    question = latest_question(thread_events)
    effective_ttl = ttl if ttl is not None else settings.default_answer_ttl_seconds
    event = build_answer_event(
        thread_id=thread,
        in_reply_to=question.id,
        from_agent=from_agent,
        repo=repo,
        summary=summary,
        evidence=evidence or [],
        confidence=confidence,
        ttl_seconds=effective_ttl,
        branch=branch,
        commit=commit,
    )
    storage.write_event(event)
    emit(event.model_dump(by_alias=True, mode="json", exclude_none=True), as_json=as_json)
