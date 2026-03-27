from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

EventType = Literal["question", "claim", "answer", "close"]
ThreadState = Literal["open", "claimed", "answered", "closed", "expired"]


class Participant(BaseModel):
    agent: str
    repo: str | None = None
    branch: str | None = None
    commit: str | None = None


class EvidenceRef(BaseModel):
    path: str
    lines: str | None = None


class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: EventType
    thread_id: str
    namespace: str | None = None
    from_participant: Participant = Field(alias="from")
    to: Participant | None = None
    created_at: str
    ttl_seconds: int | None = None
    schema_version: int = 1
    body: dict[str, Any]
    in_reply_to: str | None = None

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, value: str) -> str:
        if len(value) > 80:
            raise ValueError("thread_id must be 80 characters or fewer")
        if "/" in value or "\\" in value:
            raise ValueError("thread_id must not contain path separators (/ or \\)")
        return value

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", value):
            raise ValueError(
                "namespace must contain only alphanumeric characters, dots, hyphens, and underscores"
            )
        if len(value) > 80:
            raise ValueError("namespace must be 80 characters or fewer")
        return value

    def created_datetime(self) -> datetime:
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    def expires_at(self) -> datetime | None:
        if self.ttl_seconds is None:
            return None
        return self.created_datetime() + timedelta(seconds=self.ttl_seconds)

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.ttl_seconds is None:
            return False
        reference = now or datetime.now(UTC)
        return self.expires_at() <= reference


class ThreadView(BaseModel):
    thread_id: str
    namespace: str | None = None
    state: ThreadState
    question_id: str
    to_agent: str | None = None
    subject: str | None = None
    events: list[Event]


class CursorState(BaseModel):
    agent: str
    last_seen_created_at: str
    last_seen_event_id: str
    updated_at: str
