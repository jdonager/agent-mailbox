from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Annotated

import typer

from agent_board.commands._common import emit, get_settings, get_storage
from agent_board.storage import StoredEvent
from agent_board.threads import derive_thread_state, thread_archive_reason


def command(
    context: typer.Context,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    prune: Annotated[bool, typer.Option("--prune")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    settings = get_settings(context)
    storage = get_storage(context)
    grouped: dict[str, list[StoredEvent]] = defaultdict(list)
    for record in storage.list_stored_events():
        grouped[record.event.thread_id].append(record)

    now = datetime.now(UTC)
    archive_plan: list[dict[str, object]] = []
    records_to_archive: list[StoredEvent] = []
    for thread_id, records in sorted(grouped.items()):
        events = [record.event for record in records]
        reason = thread_archive_reason(
            events,
            now=now,
            closed_after_days=settings.archive_closed_after_days,
            expired_after_days=settings.archive_expired_after_days,
        )
        if reason is None:
            continue
        archive_plan.append(
            {
                "thread_id": thread_id,
                "reason": reason,
                "state": derive_thread_state(events, now),
                "event_count": len(records),
                "latest_event_at": max(event.created_at for event in events),
            }
        )
        records_to_archive.extend(records)

    archived_count = 0
    if not dry_run and records_to_archive:
        archived_count = storage.archive_stored_events(records_to_archive)
        storage.remove_empty_dirs(storage.events_root())

    pruned_count = 0
    if prune and settings.prune_archived_after_days is not None:
        pruned_count = (
            0
            if dry_run
            else storage.prune_archived_events(settings.prune_archived_after_days, now=now)
        )

    payload = {
        "dry_run": dry_run,
        "archived_event_count": archived_count,
        "archived_threads": archive_plan,
        "pruned_event_count": pruned_count,
        "prune_enabled": prune,
        "prune_after_days": settings.prune_archived_after_days,
    }
    if as_json:
        emit(payload, as_json=as_json)
        return

    typer.echo("agent-board gc")
    if archive_plan:
        typer.echo(f"Threads to archive: {len(archive_plan)}")
        for item in archive_plan:
            typer.echo(
                f"- {item['thread_id']} [{item['state']}] reason={item['reason']} "
                f"events={item['event_count']} latest={item['latest_event_at']}"
            )
    else:
        typer.echo("No threads eligible for archival.")

    if dry_run:
        typer.echo("Dry run only; no files moved.")
    else:
        typer.echo(
            f"Archived {archived_count} event(s) across {len(archive_plan)} thread(s)."
        )

    if prune:
        if settings.prune_archived_after_days is None:
            typer.echo("Prune requested, but prune_archived_after_days is not configured.")
        elif dry_run:
            typer.echo(
                "Prune enabled; archived events older than "
                f"{settings.prune_archived_after_days} days would be removed."
            )
        else:
            typer.echo(f"Pruned {pruned_count} archived event(s).")
