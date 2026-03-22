# agent-board

A local-only, lightweight mailbox for cross-repo agent handoff.

`agent-board` is a filesystem-backed event board that lets separate agent sessions ask targeted questions, claim responsibility, post answers, and close threads. It is designed for the case where you are working across multiple repos under one org umbrella and need a minimal, inspectable way for one agent session to request specific information from another.

## Install

For cross-repo use, install the CLI once with `uv` so any repo or hook can call `agent-board` directly:

```bash
uv tool install --editable /absolute/path/to/agent-board
```

For local development in this repo:

```bash
uv sync --extra dev
```

## Local setup

From a fresh clone:

```bash
git clone <your-repo-url>
cd agent-board
uv sync --extra dev
uv tool install --editable .
```

Optional environment variables:

- `AGENT_BOARD_ROOT` to override the default board location of `~/.agent-board`
- `AGENT_BOARD_AGENT` for wrapper scripts that need a participant identity

For normal local usage across multiple repos, set a shared mailbox location once:

```bash
export AGENT_BOARD_ROOT="$HOME/.agent-board"
```

There is no daemon or background server to start. `agent-board` reads and writes mailbox state directly on disk when you run commands.

## Quickstart

Ask a question from one agent:

```bash
agent-board ask \
  --from-agent codex-repo-a \
  --to-agent claude-repo-b \
  --thread repo-b-jwt-kid-validation \
  --subject "JWT kid validation path" \
  --question "How does repo-b validate rotated JWT kid values?" \
  --repo repo-a
```

Check the inbox for the target agent:

```bash
agent-board inbox --for-agent claude-repo-b --json
agent-board inbox --for-agent claude-repo-b --mark-seen --json
```

Inspect or clear the cursor for an agent:

```bash
agent-board cursor --for-agent claude-repo-b --json
agent-board cursor --for-agent claude-repo-b --clear --json
```

Claim, answer, and close the thread:

```bash
agent-board claim --thread repo-b-jwt-kid-validation --from-agent claude-repo-b --repo repo-b
agent-board answer --thread repo-b-jwt-kid-validation --from-agent claude-repo-b --repo repo-b \
  --summary "Validation occurs in middleware/auth.ts via keyResolver()." \
  --evidence middleware/auth.ts:44-91 \
  --confidence high
agent-board close --thread repo-b-jwt-kid-validation --from-agent codex-repo-a --repo repo-a \
  --resolution accepted
```

Render agent-friendly mailbox context for hooks, skills, or AGENTS files:

```bash
agent-board prompt --tool claude --agent claude-repo-b
agent-board prompt --tool codex --agent codex-repo-a
```

Print a ready-made two-terminal walkthrough:

```bash
agent-board demo
```

## Smoke test

Use two terminals or just run these commands in sequence to confirm local behavior:

```bash
agent-board ask \
  --from-agent codex-repo-a \
  --to-agent claude-repo-b \
  --thread smoke-test \
  --subject "Smoke test" \
  --question "Can you see this thread?" \
  --repo repo-a

agent-board inbox --for-agent claude-repo-b --mark-seen --json

agent-board claim --thread smoke-test --from-agent claude-repo-b --repo repo-b

agent-board answer \
  --thread smoke-test \
  --from-agent claude-repo-b \
  --repo repo-b \
  --summary "Yes, the thread is visible locally." \
  --evidence README.md:1-20 \
  --confidence high

agent-board thread --thread smoke-test --json

agent-board close \
  --thread smoke-test \
  --from-agent codex-repo-a \
  --repo repo-a \
  --resolution accepted
```

## End-to-end demo

If you want a clearer cross-repo walkthrough, use two terminals and two repo directories:

```bash
# Terminal 1
cd /path/to/repo-a
agent-board ask \
  --from-agent codex-repo-a \
  --to-agent claude-repo-b \
  --thread cross-repo-demo \
  --subject "Cross-repo question" \
  --question "Where is the relevant logic?" \
  --repo repo-a

# Terminal 2
cd /path/to/repo-b
agent-board inbox --for-agent claude-repo-b --mark-seen --json
agent-board claim --thread cross-repo-demo --from-agent claude-repo-b --repo repo-b
agent-board answer \
  --thread cross-repo-demo \
  --from-agent claude-repo-b \
  --repo repo-b \
  --summary "The logic lives in src/example.py." \
  --evidence src/example.py:10-42 \
  --confidence high

# Terminal 1
cd /path/to/repo-a
agent-board thread --thread cross-repo-demo --json
agent-board close \
  --thread cross-repo-demo \
  --from-agent codex-repo-a \
  --repo repo-a \
  --resolution accepted
```

To print a version of that walkthrough from the CLI:

```bash
agent-board demo \
  --repo-a-path /path/to/repo-a \
  --repo-b-path /path/to/repo-b \
  --agent-a codex-repo-a \
  --agent-b claude-repo-b \
  --thread cross-repo-demo
```

## Goals

- local only
- lightweight and inspectable
- safe by default
- easy to script from any tool
- no network required
- no daemon required for v1
- resilient to concurrent use

## Non-goals

- rich chat UI
- workflow orchestration platform
- background job system
- long-term knowledge base
- automatic code execution
- complex auth or permissions

## Mental model

Each repo/agent session is a participant.

Example flow:

1. `codex-repo-a` asks a question about behavior in `repo-b`
2. `claude-repo-b` reads the question and claims it
3. `claude-repo-b` posts an answer with file references
4. `codex-repo-a` reads the answer and closes the thread

The board is for **ephemeral cross-repo handoff**, not durable repo instructions. Durable guidance should live in repo docs such as `AGENTS.md` or equivalent.

## v1 architecture

The source of truth is an append-only set of JSON event files on disk.

### Why event files

Compared with a single shared JSON file:

- safer concurrent writes
- simpler atomic writes
- easier debugging and manual inspection

Compared with SQLite:

- lower setup cost
- easier shell integration
- enough for early usage

## Filesystem layout

```text
~/.agent-board/
  events/
    2026-03-20/
      2026-03-20T15-42-11Z__01JQ...__question__repo-b-jwt-kid-validation.json
      2026-03-20T15-43-00Z__01JQ...__claim__repo-b-jwt-kid-validation.json
      2026-03-20T15-46-30Z__01JQ...__answer__repo-b-jwt-kid-validation.json
      2026-03-20T15-48-10Z__01JQ...__close__repo-b-jwt-kid-validation.json
  archive/
    events/
  cursors/
    codex-repo-a.cursor
    claude-repo-b.cursor
  attachments/
  state/
    threads/
  logs/
  config.json
```

### Notes

- `events/` is the source of truth
- `archive/events/` stores threads moved out of the active board by `gc`
- `cursors/` tracks what each participant has seen and powers inbox unread state
- `attachments/` is optional and can be skipped in v1
- `state/threads/` may be used for cached derived state later, but not as authoritative data

## Event model

Everything is an event.

### v1 event types

- `question`
- `claim`
- `answer`
- `close`

Possible future event types:

- `cancel`
- `note`

## Base event envelope

```json
{
  "id": "01JQZP7W8Y4YJ4M7J6T4X2N8W2",
  "type": "question",
  "thread_id": "repo-b-jwt-kid-validation",
  "from": {
    "agent": "codex-repo-a",
    "repo": "repo-a",
    "branch": "feature/token-rotation",
    "commit": "abc1234"
  },
  "to": {
    "agent": "claude-repo-b",
    "repo": "repo-b"
  },
  "created_at": "2026-03-20T15:42:11Z",
  "ttl_seconds": 1800,
  "schema_version": 1,
  "body": {}
}
```

## Event shapes

### question

```json
{
  "id": "01...",
  "type": "question",
  "thread_id": "repo-b-jwt-kid-validation",
  "from": {
    "agent": "codex-repo-a",
    "repo": "repo-a",
    "branch": "feature/token-rotation",
    "commit": "abc1234"
  },
  "to": {
    "agent": "claude-repo-b",
    "repo": "repo-b"
  },
  "created_at": "2026-03-20T15:42:11Z",
  "ttl_seconds": 1800,
  "schema_version": 1,
  "body": {
    "subject": "JWT kid validation path",
    "question": "How does repo-b validate rotated JWT kid values?",
    "expected_answer_format": ["summary", "file_paths", "confidence"],
    "priority": "normal",
    "refs": [
      {
        "repo": "repo-a",
        "path": "services/auth/rotate.ts"
      }
    ],
    "constraints": {
      "max_answer_lines": 20,
      "needs_file_refs": true
    }
  }
}
```

### claim

```json
{
  "id": "01...",
  "type": "claim",
  "thread_id": "repo-b-jwt-kid-validation",
  "in_reply_to": "01...question",
  "from": {
    "agent": "claude-repo-b",
    "repo": "repo-b",
    "branch": "main",
    "commit": "def5678"
  },
  "created_at": "2026-03-20T15:43:00Z",
  "ttl_seconds": 600,
  "schema_version": 1,
  "body": {
    "claim_expires_at": "2026-03-20T15:53:00Z",
    "note": "Investigating auth middleware and JWKS config."
  }
}
```

### answer

```json
{
  "id": "01...",
  "type": "answer",
  "thread_id": "repo-b-jwt-kid-validation",
  "in_reply_to": "01...question",
  "from": {
    "agent": "claude-repo-b",
    "repo": "repo-b",
    "branch": "main",
    "commit": "def5678"
  },
  "created_at": "2026-03-20T15:46:30Z",
  "ttl_seconds": 86400,
  "schema_version": 1,
  "body": {
    "summary": "Validation occurs in middleware/auth.ts via keyResolver(), which reads JWKS config from config/jwks.ts.",
    "evidence": [
      {"path": "middleware/auth.ts", "lines": "44-91"},
      {"path": "config/jwks.ts", "lines": "1-38"}
    ],
    "confidence": "high",
    "stale_risk": "low",
    "followups": [
      "Rotation fallback appears hard-coded to cache TTL of 300s."
    ]
  }
}
```

### close

```json
{
  "id": "01...",
  "type": "close",
  "thread_id": "repo-b-jwt-kid-validation",
  "in_reply_to": "01...answer",
  "from": {
    "agent": "codex-repo-a",
    "repo": "repo-a",
    "branch": "feature/token-rotation",
    "commit": "abc1234"
  },
  "created_at": "2026-03-20T15:48:10Z",
  "ttl_seconds": 86400,
  "schema_version": 1,
  "body": {
    "resolution": "accepted",
    "note": "Used to update token rollover logic."
  }
}
```

## Thread rules

- one thread starts with exactly one `question`
- zero or more `claim` events are allowed
- zero or more `answer` events are allowed
- one `close` ends the thread
- latest non-expired claim is the active claim
- the board is append-only; state is derived from events

### Thread states

Derived state is computed from events:

- `open`
- `claimed`
- `answered`
- `closed`
- `expired`

Suggested resolution logic:

- if a close exists: `closed`
- else if a valid answer exists: `answered`
- else if an unexpired claim exists: `claimed`
- else if the question expired: `expired`
- else: `open`

## TTL defaults

Suggested v1 defaults:

- question: `1800` seconds
- claim: `600` seconds
- answer: `86400` seconds
- close: `86400` seconds

TTL keeps stale work from lingering indefinitely.

## CLI

Planned v1 commands:

```bash
agent-board ask
agent-board inbox
agent-board claim
agent-board answer
agent-board close
agent-board thread
agent-board cursor
agent-board demo
agent-board prompt
agent-board gc
```

All commands should support `--json` for machine-readable output.

### ask

Create a question event.

```bash
agent-board ask \
  --from codex-repo-a \
  --to claude-repo-b \
  --thread repo-b-jwt-kid-validation \
  --subject "JWT kid validation path" \
  --question "How does repo-b validate rotated JWT kid values?" \
  --repo repo-a \
  --branch feature/token-rotation \
  --commit abc1234
```

### inbox

Show active questions for a participant.

```bash
agent-board inbox --for claude-repo-b
```

Use `--mark-seen` to update the calling agent's cursor after rendering the current inbox. JSON output includes `unread` on each thread and the current `cursor`.

### claim

```bash
agent-board claim \
  --thread repo-b-jwt-kid-validation \
  --from claude-repo-b \
  --repo repo-b
```

### answer

```bash
agent-board answer \
  --thread repo-b-jwt-kid-validation \
  --from claude-repo-b \
  --summary "Validation occurs in middleware/auth.ts via keyResolver()" \
  --evidence middleware/auth.ts:44-91 \
  --evidence config/jwks.ts:1-38 \
  --confidence high
```

### close

```bash
agent-board close \
  --thread repo-b-jwt-kid-validation \
  --from codex-repo-a \
  --resolution accepted
```

### thread

```bash
agent-board thread --thread repo-b-jwt-kid-validation
```

### cursor

Inspect or clear a participant cursor.

```bash
agent-board cursor --for-agent claude-repo-b --json
agent-board cursor --for-agent claude-repo-b --clear --json
```

### demo

Print a two-terminal walkthrough you can adapt for your own repo paths and agent names.

```bash
agent-board demo
agent-board demo --repo-a-path /path/to/repo-a --repo-b-path /path/to/repo-b
```

### prompt

Render a plain-text mailbox summary tuned for an agent environment.

```bash
agent-board prompt --tool claude --agent claude-repo-b
agent-board prompt --tool codex --agent codex-repo-a
```

### gc

```bash
agent-board gc
agent-board gc --dry-run --json
agent-board gc --prune --json
```

`gc` archives closed threads older than `archive_closed_after_days` and expired threads older than `archive_expired_after_days`. Use `--dry-run` to preview the archive plan without moving files. Use `--prune` to also remove archived events older than `prune_archived_after_days`.

## Config

Example `config.json`:

```json
{
  "board_root": "~/.agent-board",
  "default_question_ttl_seconds": 1800,
  "default_claim_ttl_seconds": 600,
  "default_answer_ttl_seconds": 86400,
  "archive_closed_after_days": 7,
  "archive_expired_after_days": 3,
  "prune_archived_after_days": 30,
  "max_event_size_bytes": 32768
}
```

## Safety rules

Hard limits for v1:

- max event size: 32 KB
- max subject length: 120 chars
- max thread id length: 80 chars
- max evidence refs per answer: 20

Disallowed in v1:

- automatic execution of commands from event payloads
- embedding binary data in JSON events
- storing secrets in event files
- direct patch transport as message content

## Polling model

The default compatibility strategy is polling.

A participant or wrapper script periodically runs:

```bash
agent-board inbox --for <agent> --json
```

That is deliberately simple and portable across tools and shells. File watching, local HTTP, or MCP wrappers can be added later.

## Recommended implementation

Use Python for v1.

Suggested stack:

- Python 3.11+
- `typer` for CLI
- `pydantic` for schema validation
- `rich` for terminal output
- `ulid-py` for sortable IDs
- `pytest` for tests
- `ruff` for linting
- `mypy` for type checking

## Adapter examples

The adapters in this repo are intentionally thin. They do not try to own the entire agent workflow. Their job is to expose mailbox context in a way that fits each tool’s documented integration surface.

If you want to author external Claude or Codex skills around `agent-board`, see `docs/skill-examples.md`.

### Claude Code

Claude Code has documented lifecycle hooks, including `SessionStart`, and command hooks can receive JSON on stdin and add plain-text context back to the session through successful stdout output. It also supports project-scoped hook config in `.claude/settings.json`.

Use the example hook config in `examples/claude/settings.json.example` together with the wrapper script in `scripts/agent-board-adapter-claude-session-start`.

Example:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "AGENT_BOARD_AGENT=claude-repo-b agent-board-adapter-claude-session-start"
          }
        ]
      }
    ]
  }
}
```

That setup injects a mailbox summary into the Claude session at startup. It is a good base for a future Claude skill or project rule that standardizes `ask`, `claim`, `answer`, and `close`.

### Codex CLI and Codex app

Codex’s documented integration surfaces are different. The stable primitives are repo instructions via `AGENTS.md`, non-interactive execution through `codex exec`, and app-level automations. There is not an equivalent documented lifecycle hook surface in the Codex CLI docs today.

For Codex, the recommended v1 pattern is:

1. Put mailbox usage rules in `AGENTS.md`
2. Use `agent-board prompt --tool codex --agent <agent-id>` to render current mailbox context
3. Use Codex app automations for recurring inbox checks if you want background polling

Example files:

- `examples/codex/AGENTS.md.example`
- `examples/codex/app-automation-prompt.md`
- `scripts/agent-board-adapter-codex-context`

Example `AGENTS.md` snippet:

```md
# Agent Board Workflow

- At session start, run `agent-board-adapter-codex-context codex-repo-a` and read the output before planning work.
- If you need cross-repo information, post a targeted question with `agent-board ask`.
- If a thread is assigned to `codex-repo-a`, claim it before investigating and answer with file paths and confidence.
- When you consume an answer successfully, close the thread with `agent-board close`.
```

## Suggested package layout

```text
agent-board/
  pyproject.toml
  README.md
  examples/
    claude/
    codex/
  scripts/
  src/
    agent_board/
      __init__.py
      __main__.py
      adapters.py
      cli.py
      config.py
      models.py
      storage.py
      events.py
      threads.py
      commands/
        __init__.py
        _common.py
        ask.py
        inbox.py
        claim.py
        answer.py
        close.py
        thread.py
        prompt.py
        gc.py
      utils/
        clock.py
        ids.py
        io.py
        validate.py
  tests/
    test_adapters.py
    test_ask.py
    test_claim.py
    test_answer.py
    test_thread_state.py
    test_concurrency.py
```

## Atomic write strategy

Event writes should be atomic:

1. serialize JSON to a temp file in the target directory
2. flush and fsync the temp file
3. rename the temp file to the final filename

This avoids partial writes and reduces concurrency hazards on normal local filesystems.

## Build order

1. Implement config, models, storage, `ask`, and `thread`
2. Add `inbox`, `claim`, and thread-state derivation
3. Add `answer` and `close`
4. Add `gc`, tests, and JSON output cleanup

## Acceptance criteria for v1

The board is useful when:

- two terminals can exchange a question and answer
- event writes are atomic
- inbox shows only active relevant work
- stale claims expire automatically in derived state
- answers can cite evidence
- a closed thread no longer appears in inbox
- humans can inspect raw files and understand what happened

## Practical advice

There are two common failure modes for a project like this:

1. it grows into an overbuilt platform
2. message quality is too loose

Keep the implementation small and the message contract strict.

In v1, the contract is the product.

## References

- Claude Code hooks reference: https://code.claude.com/docs/en/hooks
- OpenAI Codex docs home: https://developers.openai.com/codex
