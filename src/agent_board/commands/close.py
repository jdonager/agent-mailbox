from __future__ import annotations

from typing import Annotated

import typer

from agent_board.commands._common import emit, get_settings, get_storage
from agent_board.events import build_close_event
from agent_board.threads import latest_answer, latest_question


def command(
    context: typer.Context,
    thread: Annotated[str, typer.Option("--thread")],
    from_agent: Annotated[str, typer.Option("--from-agent")],
    repo: Annotated[str, typer.Option("--repo")],
    resolution: Annotated[str, typer.Option("--resolution")],
    branch: Annotated[str | None, typer.Option("--branch")] = None,
    commit: Annotated[str | None, typer.Option("--commit")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    settings = get_settings(context)
    storage = get_storage(context)
    thread_events = storage.list_thread_events(thread)
    answer_event = latest_answer(thread_events)
    question = latest_question(thread_events)
    event = build_close_event(
        thread_id=thread,
        in_reply_to=answer_event.id if answer_event else question.id,
        from_agent=from_agent,
        repo=repo,
        resolution=resolution,
        ttl_seconds=settings.default_close_ttl_seconds,
        branch=branch,
        commit=commit,
        note=note,
    )
    storage.write_event(event)
    emit(event.model_dump(by_alias=True, mode="json", exclude_none=True), as_json=as_json)
