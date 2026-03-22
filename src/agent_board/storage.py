from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_board.models import CursorState, Event


@dataclass(slots=True)
class StoredEvent:
    event: Event
    path: Path


class BoardStorage:
    def __init__(self, board_root: Path, *, max_event_size_bytes: int = 32768) -> None:
        self.board_root = board_root
        self.max_event_size_bytes = max_event_size_bytes

    def events_root(self, *, archived: bool = False) -> Path:
        return self.board_root / "archive" / "events" if archived else self.board_root / "events"

    def ensure_layout(self) -> None:
        for path in (
            self.events_root(),
            self.board_root / "cursors",
            self.board_root / "attachments",
            self.board_root / "state" / "threads",
            self.board_root / "logs",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def event_path(self, event: Event, *, archived: bool = False) -> Path:
        created_at = event.created_at.replace(":", "-")
        date_part = event.created_at.split("T", 1)[0]
        filename = f"{created_at}__{event.id}__{event.type}__{event.thread_id}.json"
        return self.events_root(archived=archived) / date_part / filename

    def _write_json_atomic(self, destination: Path, encoded: bytes) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_suffix(".tmp")
        with temp_path.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(destination)
        return destination

    def write_event(self, event: Event, *, archived: bool = False) -> Path:
        self.ensure_layout()
        destination = self.event_path(event, archived=archived)

        payload = json.dumps(
            event.model_dump(by_alias=True, mode="json", exclude_none=True),
            indent=2,
            sort_keys=True,
        )
        encoded = payload.encode("utf-8")
        if len(encoded) > self.max_event_size_bytes:
            raise ValueError("event exceeds configured maximum size")
        return self._write_json_atomic(destination, encoded)

    def cursor_path(self, agent: str) -> Path:
        return self.board_root / "cursors" / f"{agent}.json"

    def load_cursor(self, agent: str) -> CursorState | None:
        path = self.cursor_path(agent)
        if not path.exists():
            return None
        return CursorState.model_validate_json(path.read_text())

    def save_cursor(self, cursor: CursorState) -> Path:
        self.ensure_layout()
        destination = self.cursor_path(cursor.agent)
        payload = json.dumps(cursor.model_dump(mode="json"), indent=2, sort_keys=True)
        encoded = payload.encode("utf-8")
        return self._write_json_atomic(destination, encoded)

    def clear_cursor(self, agent: str) -> None:
        self.cursor_path(agent).unlink(missing_ok=True)

    def update_cursor(self, agent: str, event: Event | None) -> CursorState | None:
        if event is None:
            return self.load_cursor(agent)

        existing = self.load_cursor(agent)
        candidate = CursorState(
            agent=agent,
            last_seen_created_at=event.created_at,
            last_seen_event_id=event.id,
            updated_at=event.created_at,
        )
        if existing is not None:
            existing_key = (existing.last_seen_created_at, existing.last_seen_event_id)
            candidate_key = (candidate.last_seen_created_at, candidate.last_seen_event_id)
            if candidate_key <= existing_key:
                return existing
        self.save_cursor(candidate)
        return candidate

    def iter_event_paths(self, *, archived: bool = False) -> Iterable[Path]:
        root = self.events_root(archived=archived)
        if not root.exists():
            return []
        return sorted(root.rglob("*.json"))

    def list_stored_events(self, *, archived: bool = False) -> list[StoredEvent]:
        stored_events: list[StoredEvent] = []
        for path in self.iter_event_paths(archived=archived):
            stored_events.append(
                StoredEvent(event=Event.model_validate_json(path.read_text()), path=path)
            )
        return sorted(stored_events, key=lambda item: (item.event.created_at, item.event.id))

    def list_events(self, *, archived: bool = False) -> list[Event]:
        return [item.event for item in self.list_stored_events(archived=archived)]

    def list_thread_events(self, thread_id: str, *, archived: bool = False) -> list[Event]:
        return [
            event
            for event in self.list_events(archived=archived)
            if event.thread_id == thread_id
        ]

    def archive_stored_events(self, records: list[StoredEvent]) -> int:
        moved = 0
        for record in records:
            destination = self.event_path(record.event, archived=True)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                record.path.unlink(missing_ok=True)
            else:
                record.path.replace(destination)
            moved += 1
        return moved

    def prune_archived_events(self, older_than_days: int, *, now: datetime | None = None) -> int:
        reference = now or datetime.now(UTC)
        cutoff = reference - timedelta(days=older_than_days)
        removed = 0
        for record in self.list_stored_events(archived=True):
            if record.event.created_datetime() < cutoff:
                record.path.unlink(missing_ok=True)
                removed += 1
        self.remove_empty_dirs(self.events_root(archived=True))
        return removed

    def remove_empty_dirs(self, root: Path) -> None:
        if not root.exists():
            return
        for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
            try:
                path.rmdir()
            except OSError:
                continue
