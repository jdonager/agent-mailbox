from __future__ import annotations

from typing import Annotated

import typer

from agent_board.commands._common import emit, get_storage
from agent_board.threads import build_thread_view, is_thread_unread, latest_event


def command(
    context: typer.Context,
    thread: Annotated[str, typer.Option("--thread")],
    for_agent: Annotated[str | None, typer.Option("--for-agent")] = None,
    mark_seen: Annotated[bool, typer.Option("--mark-seen")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    storage = get_storage(context)
    thread_events = storage.list_thread_events(thread)
    view = build_thread_view(thread_events)

    cursor = storage.load_cursor(for_agent) if for_agent else None
    unread = is_thread_unread(view, cursor) if for_agent else None

    updated_cursor = cursor
    if mark_seen and for_agent and view.events:
        newest = latest_event(view.events)
        updated_cursor = storage.update_cursor(for_agent, newest)

    payload: dict[str, object] = {
        "thread_id": view.thread_id,
        "state": view.state,
        "subject": view.subject,
        "question_id": view.question_id,
        "events": [
            event.model_dump(by_alias=True, mode="json", exclude_none=True)
            for event in view.events
        ],
    }
    if for_agent is not None:
        payload["unread"] = unread
        payload["cursor"] = updated_cursor.model_dump(mode="json") if updated_cursor else None

    emit(payload, as_json=as_json)
