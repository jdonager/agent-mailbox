from __future__ import annotations

from agent_board import __main__
from agent_board.cli import app
from agent_board.commands import answer, ask, claim, close, cursor, demo, gc, inbox, prompt, thread


def test_cli_modules_are_importable_and_registered() -> None:
    assert ask.command.__name__ == "command"
    assert inbox.command.__name__ == "command"
    assert claim.command.__name__ == "command"
    assert answer.command.__name__ == "command"
    assert close.command.__name__ == "command"
    assert thread.command.__name__ == "command"
    assert prompt.command.__name__ == "command"
    assert cursor.command.__name__ == "command"
    assert demo.command.__name__ == "command"
    assert gc.command.__name__ == "command"
    assert callable(__main__.main)

    command_names = {command.name for command in app.registered_commands}
    assert command_names == {
        "answer",
        "ask",
        "claim",
        "close",
        "cursor",
        "demo",
        "gc",
        "inbox",
        "prompt",
        "thread",
    }
