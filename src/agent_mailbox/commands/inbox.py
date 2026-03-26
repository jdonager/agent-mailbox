from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.commands._common import emit, get_storage
from agent_mailbox.threads import build_inbox, is_thread_unread, latest_event


def command(
    context: typer.Context,
    for_agent: Annotated[str, typer.Option("--for-agent")],
    mark_seen: Annotated[bool, typer.Option("--mark-seen")] = False,
    unread_only: Annotated[bool, typer.Option("--unread-only")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    storage = get_storage(context)
    threads = build_inbox(storage.list_events(), for_agent)
    cursor = storage.load_cursor(for_agent)
    payload_threads = [
        {
            "thread_id": thread.thread_id,
            "state": thread.state,
            "subject": thread.subject,
            "question_id": thread.question_id,
            "unread": is_thread_unread(thread, cursor),
        }
        for thread in threads
        if not unread_only or is_thread_unread(thread, cursor)
    ]
    latest_visible_event = None
    if threads:
        latest_visible_event = max(
            (latest_event(thread.events) for thread in threads),
            key=lambda event: (event.created_at, event.id),
        )
    updated_cursor = cursor
    if mark_seen:
        updated_cursor = storage.update_cursor(for_agent, latest_visible_event)
    payload = {
        "threads": payload_threads,
        "cursor": updated_cursor.model_dump(mode="json") if updated_cursor else None,
    }
    emit(payload, as_json=as_json)
