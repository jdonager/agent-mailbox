from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from agent_mailbox.models import CursorState, Event, ThreadState, ThreadView


def _group_events_by_thread(events: Iterable[Event]) -> dict[str, list[Event]]:
    grouped: dict[str, list[Event]] = {}
    for event in events:
        grouped.setdefault(event.thread_id, []).append(event)
    return grouped


def derive_thread_state(events: list[Event], now: datetime | None = None) -> ThreadState:
    if not events:
        raise ValueError("thread has no events")

    reference = now or datetime.now(UTC)
    ordered = sorted(events, key=lambda event: (event.created_at, event.id))
    question = next(event for event in ordered if event.type == "question")

    if any(event.type == "close" and not event.is_expired(reference) for event in ordered):
        return "closed"
    if any(event.type == "answer" and not event.is_expired(reference) for event in ordered):
        return "answered"
    if any(event.type == "claim" and not event.is_expired(reference) for event in ordered):
        return "claimed"
    if question.is_expired(reference):
        return "expired"
    return "open"


def build_thread_view(events: list[Event], now: datetime | None = None) -> ThreadView:
    ordered = sorted(events, key=lambda event: (event.created_at, event.id))
    question = next(event for event in ordered if event.type == "question")
    return ThreadView(
        thread_id=question.thread_id,
        state=derive_thread_state(ordered, now),
        question_id=question.id,
        to_agent=question.to.agent if question.to else None,
        subject=question.body.get("subject"),
        events=ordered,
    )


def build_inbox(events: list[Event], agent: str, now: datetime | None = None) -> list[ThreadView]:
    inbox_threads: list[ThreadView] = []
    for thread_events in _group_events_by_thread(events).values():
        view = build_thread_view(thread_events, now)
        if view.to_agent != agent:
            continue
        if view.state in {"open", "claimed"}:
            inbox_threads.append(view)
    return sorted(inbox_threads, key=lambda view: view.thread_id)


def latest_question(events: list[Event]) -> Event:
    ordered = sorted(events, key=lambda item: (item.created_at, item.id))
    return next(event for event in ordered if event.type == "question")


def latest_answer(events: list[Event]) -> Event | None:
    ordered = sorted(events, key=lambda item: (item.created_at, item.id))
    answers = [event for event in ordered if event.type == "answer"]
    return answers[-1] if answers else None


def latest_close(events: list[Event]) -> Event | None:
    ordered = sorted(events, key=lambda item: (item.created_at, item.id))
    closes = [event for event in ordered if event.type == "close"]
    return closes[-1] if closes else None


def latest_event(events: list[Event]) -> Event:
    return sorted(events, key=lambda item: (item.created_at, item.id))[-1]


def is_thread_unread(thread: ThreadView, cursor: CursorState | None) -> bool:
    if cursor is None:
        return True
    event = latest_event(thread.events)
    return (event.created_at, event.id) > (cursor.last_seen_created_at, cursor.last_seen_event_id)


def thread_archive_reason(
    events: list[Event],
    *,
    now: datetime | None = None,
    closed_after_days: int,
    expired_after_days: int,
) -> str | None:
    reference = now or datetime.now(UTC)
    state = derive_thread_state(events, reference)

    if state == "closed":
        close_event = latest_close(events)
        if close_event and close_event.created_datetime() <= (
            reference - timedelta(days=closed_after_days)
        ):
            return "closed"

    if state == "expired":
        question = latest_question(events)
        if question.created_datetime() <= reference - timedelta(days=expired_after_days):
            return "expired"

    return None
