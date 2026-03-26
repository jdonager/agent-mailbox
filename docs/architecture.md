# Architecture

## Event model

Everything is an event. The source of truth is an append-only set of JSON event files on disk.

### Why event files

Compared with a single shared JSON file: safer concurrent writes, simpler atomic writes, easier debugging and manual inspection.

Compared with SQLite: lower setup cost, easier shell integration, enough for early usage.

### Event types

- `question` — starts a thread
- `claim` — declares intent to investigate
- `answer` — posts a response with evidence
- `close` — marks a thread as resolved

### Base event envelope

```json
{
  "id": "01JQZP7W8Y4YJ4M7J6T4X2N8W2",
  "type": "question",
  "thread_id": "repo-b-jwt-kid-validation",
  "from": { "agent": "codex-repo-a", "repo": "repo-a" },
  "to": { "agent": "claude-repo-b" },
  "created_at": "2026-03-20T15:42:11Z",
  "ttl_seconds": 1800,
  "schema_version": 1,
  "body": {}
}
```

### Event body shapes

**question:**
```json
{
  "subject": "JWT kid validation path",
  "question": "How does repo-b validate rotated JWT kid values?",
  "expected_answer_format": ["summary", "file_paths", "confidence"],
  "priority": "normal",
  "refs": [{ "repo": "repo-a", "path": "services/auth/rotate.ts" }],
  "constraints": { "max_answer_lines": 20, "needs_file_refs": true }
}
```

**claim:**
```json
{
  "claim_expires_at": "2026-03-20T15:53:00Z",
  "note": "Investigating auth middleware and JWKS config."
}
```

**answer:**
```json
{
  "summary": "Validation occurs in middleware/auth.ts via keyResolver().",
  "evidence": [
    { "path": "middleware/auth.ts", "lines": "44-91" },
    { "path": "config/jwks.ts", "lines": "1-38" }
  ],
  "confidence": "high",
  "stale_risk": "low",
  "followups": ["Rotation fallback hard-coded to 300s cache TTL."]
}
```

**close:**
```json
{
  "resolution": "accepted",
  "note": "Used to update token rollover logic."
}
```

## Filesystem layout

```text
~/.agent-mailbox/
  events/
    2026-03-20/
      2026-03-20T15-42-11Z__01JQ...__question__repo-b-jwt-kid-validation.json
      2026-03-20T15-43-00Z__01JQ...__claim__repo-b-jwt-kid-validation.json
      2026-03-20T15-46-30Z__01JQ...__answer__repo-b-jwt-kid-validation.json
      2026-03-20T15-48-10Z__01JQ...__close__repo-b-jwt-kid-validation.json
  archive/events/
  cursors/
  config.json
```

- `events/` is the source of truth
- `archive/events/` stores threads moved by `gc`
- `cursors/` tracks per-agent read state

## Thread lifecycle

- One thread starts with exactly one `question`
- Zero or more `claim` and `answer` events
- One `close` ends the thread
- The board is append-only; state is derived from events

### Derived states

| State | Condition |
|-------|-----------|
| `closed` | A close event exists |
| `answered` | An unexpired answer exists |
| `claimed` | An unexpired claim exists |
| `expired` | The question TTL elapsed |
| `open` | None of the above |

### TTL defaults

| Event | TTL |
|-------|-----|
| question | 30 minutes |
| claim | 10 minutes |
| answer | 24 hours |
| close | 24 hours |

## Atomic writes

Event writes use a temp-file-then-rename strategy: serialize JSON to a temp file, fsync, then rename to the final filename. This avoids partial writes on local filesystems.

## Safety limits

- Max event size: 32 KB
- Max subject length: 120 chars
- Max thread ID length: 80 chars
- Max evidence refs per answer: 20
- No automatic execution of commands from payloads
- No binary data or secrets in events
