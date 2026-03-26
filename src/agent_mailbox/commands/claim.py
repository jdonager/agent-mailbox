from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.commands._common import emit, get_settings, get_storage
from agent_mailbox.events import build_claim_event
from agent_mailbox.threads import latest_question


def command(
    context: typer.Context,
    thread: Annotated[str, typer.Option("--thread")],
    from_agent: Annotated[str, typer.Option("--from-agent")],
    repo: Annotated[str, typer.Option("--repo")],
    branch: Annotated[str | None, typer.Option("--branch")] = None,
    commit: Annotated[str | None, typer.Option("--commit")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    settings = get_settings(context)
    storage = get_storage(context)
    thread_events = storage.list_thread_events(thread)
    question = latest_question(thread_events)
    event = build_claim_event(
        thread_id=thread,
        in_reply_to=question.id,
        from_agent=from_agent,
        repo=repo,
        ttl_seconds=settings.default_claim_ttl_seconds,
        branch=branch,
        commit=commit,
        note=note,
    )
    storage.write_event(event)
    emit(event.model_dump(by_alias=True, mode="json", exclude_none=True), as_json=as_json)
