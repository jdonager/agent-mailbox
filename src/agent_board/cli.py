from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agent_board.commands import answer, ask, claim, close, cursor, gc, inbox, prompt, thread
from agent_board.config import load_settings

app = typer.Typer(no_args_is_help=True, help="Filesystem-backed local mailbox for agent handoff.")


@app.callback()
def main(
    context: typer.Context,
    board_root: Annotated[Path | None, typer.Option(help="Override the board root path.")] = None,
) -> None:
    context.obj = load_settings(board_root)

app.command("ask")(ask.command)
app.command("inbox")(inbox.command)
app.command("claim")(claim.command)
app.command("answer")(answer.command)
app.command("close")(close.command)
app.command("cursor")(cursor.command)
app.command("thread")(thread.command)
app.command("gc")(gc.command)
app.command("prompt")(prompt.command)
