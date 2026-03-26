from __future__ import annotations

from typing import Annotated

import typer

from agent_mailbox.adapters import AdapterTool, render_prompt
from agent_mailbox.commands._common import get_storage
from agent_mailbox.threads import build_inbox


def command(
    context: typer.Context,
    tool: Annotated[AdapterTool, typer.Option("--tool")],
    agent: Annotated[str, typer.Option("--agent")],
) -> None:
    storage = get_storage(context)
    threads = build_inbox(storage.list_events(), agent)
    typer.echo(render_prompt(tool, agent, threads), nl=False)
