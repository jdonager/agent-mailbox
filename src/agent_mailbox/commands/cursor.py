from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.commands._common import emit, get_storage


def command(
    context: typer.Context,
    for_agent: Annotated[str, typer.Option("--for-agent")],
    clear: Annotated[bool, typer.Option("--clear")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    storage = get_storage(context)

    if clear:
        path = storage.cursor_path(for_agent)
        storage.clear_cursor(for_agent)
        if as_json:
            emit({"agent": for_agent, "cursor": None, "cleared": True}, as_json=as_json)
            return
        typer.echo(f"Cleared cursor for {for_agent}")
        typer.echo(f"Path: {path}")
        return

    cursor = storage.load_cursor(for_agent)
    payload = {
        "agent": for_agent,
        "cursor": cursor.model_dump(mode="json") if cursor else None,
        "path": str(storage.cursor_path(for_agent)),
    }
    if as_json:
        emit(payload, as_json=as_json)
        return

    if cursor is None:
        typer.echo(f"No cursor set for {for_agent}")
        typer.echo(f"Path: {storage.cursor_path(for_agent)}")
        return

    typer.echo(f"Cursor for {for_agent}")
    typer.echo(f"Last seen: {cursor.last_seen_created_at} · {cursor.last_seen_event_id}")
    typer.echo(f"Updated:   {cursor.updated_at}")
    typer.echo(f"Path:      {storage.cursor_path(for_agent)}")
