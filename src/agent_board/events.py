from __future__ import annotations

from datetime import UTC, datetime, timedelta

import ulid

from agent_board.models import Event, EvidenceRef, Participant


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def format_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def generate_event_id() -> str:
    return ulid.new().str


def parse_evidence_refs(values: list[str]) -> list[EvidenceRef]:
    evidence_refs: list[EvidenceRef] = []
    for value in values:
        if ":" in value:
            path, lines = value.rsplit(":", 1)
            evidence_refs.append(EvidenceRef(path=path, lines=lines))
        else:
            evidence_refs.append(EvidenceRef(path=value))
    return evidence_refs


def build_question_event(
    *,
    thread_id: str,
    from_agent: str,
    to_agent: str,
    subject: str,
    question: str,
    repo: str,
    ttl_seconds: int,
    branch: str | None = None,
    commit: str | None = None,
    to_repo: str | None = None,
) -> Event:
    if len(subject) > 120:
        raise ValueError("subject must be 120 characters or fewer")
    created_at = utc_now()
    return Event.model_validate(
        {
            "id": generate_event_id(),
            "type": "question",
            "thread_id": thread_id,
            "from": Participant(
                agent=from_agent,
                repo=repo,
                branch=branch,
                commit=commit,
            ).model_dump(),
            "to": Participant(agent=to_agent, repo=to_repo).model_dump(exclude_none=True),
            "created_at": format_timestamp(created_at),
            "ttl_seconds": ttl_seconds,
            "body": {
                "subject": subject,
                "question": question,
                "expected_answer_format": ["summary", "evidence", "confidence"],
                "priority": "normal",
                "refs": [],
                "constraints": {
                    "needs_file_refs": True,
                },
            },
        }
    )


def build_claim_event(
    *,
    thread_id: str,
    in_reply_to: str,
    from_agent: str,
    repo: str,
    ttl_seconds: int,
    branch: str | None = None,
    commit: str | None = None,
    note: str | None = None,
) -> Event:
    created_at = utc_now()
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    return Event.model_validate(
        {
            "id": generate_event_id(),
            "type": "claim",
            "thread_id": thread_id,
            "in_reply_to": in_reply_to,
            "from": Participant(
                agent=from_agent,
                repo=repo,
                branch=branch,
                commit=commit,
            ).model_dump(exclude_none=True),
            "created_at": format_timestamp(created_at),
            "ttl_seconds": ttl_seconds,
            "body": {
                "claim_expires_at": format_timestamp(expires_at),
                "note": note,
            },
        }
    )


def build_answer_event(
    *,
    thread_id: str,
    in_reply_to: str,
    from_agent: str,
    repo: str,
    summary: str,
    evidence: list[str],
    confidence: str,
    ttl_seconds: int,
    branch: str | None = None,
    commit: str | None = None,
    stale_risk: str = "low",
) -> Event:
    created_at = utc_now()
    return Event.model_validate(
        {
            "id": generate_event_id(),
            "type": "answer",
            "thread_id": thread_id,
            "in_reply_to": in_reply_to,
            "from": Participant(
                agent=from_agent,
                repo=repo,
                branch=branch,
                commit=commit,
            ).model_dump(exclude_none=True),
            "created_at": format_timestamp(created_at),
            "ttl_seconds": ttl_seconds,
            "body": {
                "summary": summary,
                "evidence": [item.model_dump() for item in parse_evidence_refs(evidence)],
                "confidence": confidence,
                "stale_risk": stale_risk,
                "followups": [],
            },
        }
    )


def build_close_event(
    *,
    thread_id: str,
    in_reply_to: str,
    from_agent: str,
    repo: str,
    resolution: str,
    ttl_seconds: int,
    branch: str | None = None,
    commit: str | None = None,
    note: str | None = None,
) -> Event:
    created_at = utc_now()
    return Event.model_validate(
        {
            "id": generate_event_id(),
            "type": "close",
            "thread_id": thread_id,
            "in_reply_to": in_reply_to,
            "from": Participant(
                agent=from_agent,
                repo=repo,
                branch=branch,
                commit=commit,
            ).model_dump(exclude_none=True),
            "created_at": format_timestamp(created_at),
            "ttl_seconds": ttl_seconds,
            "body": {
                "resolution": resolution,
                "note": note,
            },
        }
    )
