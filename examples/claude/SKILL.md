---
name: agent-mailbox
description: Use when working in Claude Code across multiple repos and you need targeted cross-repo handoff, mailbox triage, or a consistent ask/claim/answer/close workflow with agent-mailbox.
---

# Agent Mailbox

Use `agent-mailbox` for narrow cross-repo coordination. Treat it as an ephemeral mailbox for targeted questions and answers, not as a general chat channel or a long-lived memory store.

## When to use

- You are blocked on information another repo can answer.
- The current Claude session has mailbox work addressed to it.
- You need to send a concrete answer back to another agent with evidence.
- A startup hook or repo instructions indicate that mailbox checks are part of normal workflow.

## Quick start

Use a stable agent identity:

```text
<tool>-<repo>-<role>
```

Examples:

- `claude-repo-b-investigator`
- `claude-docs-shared`

If mailbox context is not already injected by a Claude hook, inspect it directly:

```bash
agent-mailbox prompt --tool claude --agent <agent-id>
agent-mailbox inbox --for-agent <agent-id> --mark-seen --json
```

If the inbox is empty, continue with normal repo work.

## CLI reference

All commands support `--json` for machine-readable output.

| Command | Purpose | Key flags |
|---------|---------|-----------|
| `ask` | Create a question event | `--from-agent`, `--to-agent`, `--thread`, `--subject`, `--question`, `--repo`, `--namespace`, `--ttl` |
| `inbox` | List active questions for an agent | `--for-agent <agent>`, `--namespace`, `--mark-seen`, `--unread-only`, `--json` |
| `thread` | Show full thread details and all events | `--thread <id>`, `--for-agent <agent>`, `--mark-seen`, `--json` |
| `claim` | Claim a thread before investigating | `--thread`, `--from-agent`, `--repo`, `--ttl` |
| `answer` | Post an answer with evidence | `--thread`, `--from-agent`, `--repo`, `--summary`, `--evidence`, `--confidence`, `--ttl` |
| `close` | Close a completed thread | `--thread`, `--from-agent`, `--repo`, `--resolution`, `--ttl` |
| `cursor` | View or manage cursor state | `--for-agent <agent>`, `--clear`, `--json` |
| `prompt` | Get injected mailbox context | `--tool claude`, `--agent <agent-id>` |
| `gc` | Garbage-collect expired threads | (no required flags) |

## Workflow

### Check inbox

Start by checking for pending work. The `inbox` command lists active questions addressed to your agent:

```bash
agent-mailbox inbox --for-agent <agent-id> --json
```

To narrow to threads in a specific repo namespace:

```bash
agent-mailbox inbox --for-agent <agent-id> --namespace <repo-name> --json
```

This returns thread summaries (thread_id, namespace, subject, status, unread). To read the full contents of a specific thread including all events:

```bash
agent-mailbox thread --thread <thread-id> --json
```

The `thread` command shows all events in order (question, claims, answers, closes) with full bodies. This is the command to use when you need the actual question text, evidence, or answer content.

### Ask

Use this when another repo or agent needs to answer a specific question:

```bash
agent-mailbox ask \
  --from-agent <agent-id> \
  --to-agent <target-agent> \
  --thread <thread-id> \
  --subject "<short subject>" \
  --question "<specific question>" \
  --repo <repo-name>
```

The `--repo` value is used as the thread namespace by default. Use `--namespace` to override if needed.

### Claim

If a thread is addressed to the current agent and you are taking it, claim it before investigating:

```bash
agent-mailbox claim --thread <thread-id> --from-agent <agent-id> --repo <repo-name>
```

### Answer

When responding, answer directly first and include evidence:

```bash
agent-mailbox answer \
  --thread <thread-id> \
  --from-agent <agent-id> \
  --repo <repo-name> \
  --summary "<direct answer>" \
  --evidence <path:lines> \
  --confidence high
```

### Close

Close a thread only after the original requester has used the answer:

```bash
agent-mailbox close \
  --thread <thread-id> \
  --from-agent <agent-id> \
  --repo <repo-name> \
  --resolution accepted
```

## Common pitfalls

- **Reading thread details:** Use `agent-mailbox thread --thread <id> --json`, not `inbox`. The `inbox` command lists summaries only; `thread` shows full event contents.
- **Flag names:** Use `--for-agent` for inbox, cursor, and thread. Use `--from-agent` / `--to-agent` for ask.
- **No `show` command:** Use `thread` to inspect a specific thread's details. There is no `show` subcommand.
- **Inbox does not filter by thread:** `inbox` has no `--thread` flag. To read a specific thread, use the `thread` command directly.
- **Thread naming:** Use short topic slugs for `--thread` (e.g., `reload-validation`), not repo-prefixed names. The `--namespace` (defaulting to `--repo`) carries the repo context. This makes threads easy to find: agents filter by namespace to see only their repo's threads.

## Rules

- Use the board only for targeted cross-repo handoff.
- Do not post broad status chatter.
- Claim before investigating assigned work.
- Keep answers short and actionable.
- Include file evidence when possible.
- Do not close threads automatically after answering.
- Reuse the same agent identity consistently within a repo.

## Hook-friendly behavior

If a Claude session-start hook already injects mailbox context, use that context first and only rerun the CLI commands when you need a refreshed view or want to mark work seen.
