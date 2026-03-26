<p align="center">
  <img src="assets/mailbox_delivery.png" alt="Agent Mailbox" width="400">
</p>

# agent-mailbox

Targeted knowledge transfer between agent sessions — so one session doesn't have to rediscover what another already knows.

Each agent session builds deep context as it works: codebase understanding, bug investigations, design decisions, integration discoveries. That context is trapped in the session that earned it. When a different agent session — working a different repo, a different problem — needs that knowledge, it shouldn't have to spelunk through unfamiliar code and re-derive what's already known.

`agent-mailbox` is a local, filesystem-backed mailbox that lets agent sessions ask targeted questions, claim responsibility, post evidence-backed answers, and close threads. No redundant exploration, no context loss across session boundaries.

## Install

```bash
uv tool install --editable /path/to/agent-mailbox
```

For development:

```bash
uv sync --extra dev
```

No daemon or background server — `agent-mailbox` reads and writes directly on disk.

## How it works

Each agent/session combination is a participant. The unit isn't "agent" — it's "agent + session context."

1. `codex-repo-a` hits a question about behavior in `repo-b` — it could dig in, but another session already knows
2. `codex-repo-a` posts a targeted question to `claude-repo-b`
3. `claude-repo-b` — already deep in that codebase — claims the thread, answers with file paths and line ranges
4. `codex-repo-a` reads the answer and closes the thread — minutes instead of a fresh investigation

## Quickstart

```bash
# Ask a question
agent-mailbox ask \
  --from-agent codex-repo-a --to-agent claude-repo-b \
  --thread repo-b-auth-question \
  --subject "JWT validation path" \
  --question "How does repo-b validate rotated JWT kid values?" \
  --repo repo-a

# Check inbox
agent-mailbox inbox --for-agent claude-repo-b --json

# Claim, answer, close
agent-mailbox claim --thread repo-b-auth-question --from-agent claude-repo-b --repo repo-b
agent-mailbox answer --thread repo-b-auth-question --from-agent claude-repo-b --repo repo-b \
  --summary "Validation occurs in middleware/auth.ts via keyResolver()." \
  --evidence middleware/auth.ts:44-91 --confidence high
agent-mailbox close --thread repo-b-auth-question --from-agent codex-repo-a --repo repo-a \
  --resolution accepted
```

## CLI reference

All commands support `--json` for machine-readable output.

| Command | Purpose | Key flags |
|---------|---------|-----------|
| `ask` | Post a question | `--from-agent`, `--to-agent`, `--thread`, `--subject`, `--question`, `--repo`, `--ttl` |
| `inbox` | List active questions (summaries) | `--for-agent`, `--mark-seen`, `--unread-only` |
| `thread` | Show full thread with all events | `--thread`, `--for-agent`, `--mark-seen` |
| `claim` | Claim a thread before investigating | `--thread`, `--from-agent`, `--repo`, `--ttl` |
| `answer` | Post an answer with evidence | `--thread`, `--from-agent`, `--repo`, `--summary`, `--evidence`, `--confidence`, `--ttl` |
| `close` | Close a completed thread | `--thread`, `--from-agent`, `--repo`, `--resolution`, `--ttl` |
| `cursor` | View or clear cursor state | `--for-agent`, `--clear` |
| `prompt` | Render mailbox context for agent hooks | `--tool`, `--agent` |
| `gc` | Archive expired/closed threads | `--dry-run`, `--prune` |
| `demo` | Print a two-terminal walkthrough | `--repo-a-path`, `--repo-b-path` |

Use `inbox` to list threads, `thread` to read full event bodies. `inbox` shows summaries only.

## Tool integration

### Claude Code

Add a session-start hook to inject mailbox context automatically:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "AGENT_MAILBOX_AGENT=claude-repo-b agent-mailbox-adapter-claude-session-start"
          }
        ]
      }
    ]
  }
}
```

See `examples/claude/` and `docs/skill-examples.md` for skill authoring guidance.

### Codex

Add mailbox usage rules to `AGENTS.md` and use `agent-mailbox prompt --tool codex --agent <id>` for context. See `examples/codex/` for examples.

## Configuration

Optional environment variables:

- `AGENT_MAILBOX_ROOT` — override the default `~/.agent-mailbox` data directory
- `AGENT_MAILBOX_AGENT` — set participant identity for wrapper scripts

See `~/.agent-mailbox/config.json` for archive and size limit settings. Events do not expire by default; use `--ttl <seconds>` on any command to set a per-event TTL, or configure global defaults in `config.json`.

## Design

- **Local only** — filesystem-backed, no network, no daemon
- **Append-only events** — atomic writes, human-inspectable JSON files in `~/.agent-mailbox/events/`
- **Derived state** — thread status (open/claimed/answered/closed/expired) computed from events
- **Optional TTL** — events never expire by default; agents set `--ttl` per-event when expiration makes sense
- **Cursor tracking** — per-agent read state powers unread detection

For event schemas, thread lifecycle rules, and architecture details, see [`docs/architecture.md`](docs/architecture.md).

## License

MIT
