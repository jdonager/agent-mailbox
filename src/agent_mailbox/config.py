from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    board_root: Path = Field(default_factory=lambda: Path("~/.agent-mailbox").expanduser())
    default_question_ttl_seconds: int | None = None
    default_claim_ttl_seconds: int | None = None
    default_answer_ttl_seconds: int | None = None
    default_close_ttl_seconds: int | None = None
    archive_closed_after_days: int = 7
    archive_expired_after_days: int = 3
    prune_archived_after_days: int | None = 30
    max_event_size_bytes: int = 32768


def load_settings(explicit_board_root: Path | None = None) -> Settings:
    env_board_root = os.getenv("AGENT_MAILBOX_ROOT")
    board_root = explicit_board_root or (
        Path(env_board_root).expanduser() if env_board_root else None
    )
    if board_root is None:
        return Settings()

    config_path = board_root / "config.json"
    if not config_path.exists():
        return Settings(board_root=board_root)

    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    config_data["board_root"] = str(board_root)
    return Settings.model_validate(config_data)
