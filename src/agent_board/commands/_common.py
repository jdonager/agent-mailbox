from __future__ import annotations

import json

import typer
from rich.console import Console

from agent_board.config import Settings
from agent_board.storage import BoardStorage

console = Console()


def get_settings(context: typer.Context) -> Settings:
    settings = context.obj
    if not isinstance(settings, Settings):
        raise typer.Exit(code=1)
    return settings


def get_storage(context: typer.Context) -> BoardStorage:
    settings = get_settings(context)
    return BoardStorage(
        settings.board_root,
        max_event_size_bytes=settings.max_event_size_bytes,
    )


def emit(payload: object, *, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return
    if isinstance(payload, str):
        console.print(payload)
        return
    console.print_json(json.dumps(payload))
