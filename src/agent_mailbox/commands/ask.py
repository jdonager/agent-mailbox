from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.commands._common import emit, get_settings, get_storage
from agent_mailbox.events import build_question_event


def command(
    context: typer.Context,
    from_agent: Annotated[str, typer.Option("--from-agent")],
    to_agent: Annotated[str, typer.Option("--to-agent")],
    thread: Annotated[str, typer.Option("--thread")],
    subject: Annotated[str, typer.Option("--subject")],
    question: Annotated[str, typer.Option("--question")],
    repo: Annotated[str, typer.Option("--repo")],
    branch: Annotated[str | None, typer.Option("--branch")] = None,
    commit: Annotated[str | None, typer.Option("--commit")] = None,
    namespace: Annotated[str | None, typer.Option("--namespace", help="Thread namespace; defaults to --repo value")] = None,
    ttl: Annotated[int | None, typer.Option("--ttl", help="TTL in seconds; omit for no expiration")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    settings = get_settings(context)
    storage = get_storage(context)
    effective_ttl = ttl if ttl is not None else settings.default_question_ttl_seconds
    event = build_question_event(
        thread_id=thread,
        from_agent=from_agent,
        to_agent=to_agent,
        subject=subject,
        question=question,
        repo=repo,
        ttl_seconds=effective_ttl,
        branch=branch,
        commit=commit,
        namespace=namespace,
    )
    storage.write_event(event)
    emit(event.model_dump(by_alias=True, mode="json", exclude_none=True), as_json=as_json)
