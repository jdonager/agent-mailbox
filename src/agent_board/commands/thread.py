from __future__ import annotations

from typing import Annotated

import typer

from agent_board.commands._common import emit, get_storage
from agent_board.threads import build_thread_view


def command(
    context: typer.Context,
    thread: Annotated[str, typer.Option("--thread")],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    storage = get_storage(context)
    thread_events = storage.list_thread_events(thread)
    view = build_thread_view(thread_events)
    payload = {
        "thread_id": view.thread_id,
        "state": view.state,
        "subject": view.subject,
        "question_id": view.question_id,
        "events": [
            event.model_dump(by_alias=True, mode="json", exclude_none=True)
            for event in view.events
        ],
    }
    emit(payload, as_json=as_json)
