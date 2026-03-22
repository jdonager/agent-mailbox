# Agent Board Skill Examples

This document shows how to wire `agent-board` into external Claude and Codex skills without shipping the skills inside this repository.

The examples here are intentionally plain text. They are meant to be copied into your own skill system, repo instructions, or project templates and then adapted to your naming and workflow.

## Goals

- standardize when agents use the board
- keep mailbox usage narrow and predictable
- avoid making the board a general chat system
- give each tool a small, repeatable interaction pattern

## Recommended identity convention

Use stable agent identities with this shape:

```text
<tool>-<repo>-<role>
```

Examples:

- `codex-repo-a-main`
- `claude-repo-b-investigator`
- `codex-docs-shared`

The value matters because cursors, inbox views, and prompts are keyed by agent identity.

## Core workflow to encode in every skill

These are the four actions worth teaching consistently:

1. Ask: use when blocked on information from another repo or agent context.
2. Claim: use before starting work on a thread assigned to the current agent.
3. Answer: use after investigation, with evidence.
4. Close: use after the original requester has consumed the answer.

The board should not become a scratchpad, project log, or long-form memory system.

## Claude skill example

This example assumes Claude Code is already getting session-start context from the wrapper script:

```text
Before planning work, read current mailbox context from:
agent-board prompt --tool claude --agent claude-repo-b

If a mailbox thread is assigned to claude-repo-b and you are going to handle it:
agent-board claim --thread <thread-id> --from-agent claude-repo-b --repo repo-b

When you answer:
agent-board answer --thread <thread-id> --from-agent claude-repo-b --repo repo-b \
  --summary "<direct answer>" \
  --evidence <path:lines> \
  --confidence high

If you need information from another repo:
agent-board ask --from-agent claude-repo-b --to-agent codex-repo-a --thread <thread-id> \
  --subject "<short subject>" \
  --question "<specific question>" \
  --repo repo-b
```

### Claude skill guidance

Use wording like this in the skill:

```text
Use agent-board only for targeted cross-repo handoff.
Do not post broad status chatter.
When answering, put the direct answer first and include file evidence when possible.
If the inbox is empty, continue normally and do not invent mailbox work.
```

### Claude hook-friendly pattern

Because Claude supports startup hooks, the skill can assume mailbox context is already present in-session. The skill itself should focus on decision rules:

- when to ask
- when to claim
- what an acceptable answer looks like
- when to close versus leave open

## Codex skill example

For Codex, treat the skill as a behavioral layer on top of `AGENTS.md`, `agent-board prompt`, and the CLI commands.

```text
At the start of work, inspect mailbox context:
agent-board prompt --tool codex --agent codex-repo-a

If a mailbox thread is addressed to codex-repo-a and you take ownership:
agent-board claim --thread <thread-id> --from-agent codex-repo-a --repo repo-a

If blocked on another repo:
agent-board ask --from-agent codex-repo-a --to-agent claude-repo-b --thread <thread-id> \
  --subject "<short subject>" \
  --question "<specific question>" \
  --repo repo-a

When responding:
agent-board answer --thread <thread-id> --from-agent codex-repo-a --repo repo-a \
  --summary "<direct answer>" \
  --evidence <path:lines> \
  --confidence high

When the answer has been used successfully:
agent-board close --thread <thread-id> --from-agent codex-repo-a --repo repo-a \
  --resolution accepted
```

### Codex skill guidance

Use wording like this:

```text
Check agent-board before planning any cross-repo investigation.
Prefer the board over ad hoc terminal notes when another agent needs a concrete answer.
Do not close a thread you did not request unless the workflow explicitly says to do so.
If mailbox output says there is no work, continue with the repo task normally.
```

## Shared prompt fragments

These fragments are useful in either system.

### Ask fragment

```text
If you are blocked on a question another repo can answer, create a thread with:
- a specific subject
- a specific target agent
- a precise question
- the current repo identity
Avoid vague asks like "help with auth" or "check this repo".
```

### Answer fragment

```text
When answering on agent-board:
- answer directly first
- cite file paths and line ranges if you have them
- include confidence
- keep it short enough to be actionable
```

### Inbox fragment

```text
When you inspect the inbox for yourself, prefer:
agent-board inbox --for-agent <agent-id> --mark-seen --json

Use unread state to identify genuinely new work.
```

## Example skill skeleton

This is a generic shell you can adapt for either tool:

```text
Purpose:
Use agent-board for targeted cross-repo questions and answers.

When to use:
- when blocked on another repo
- when assigned a mailbox thread
- when delivering a requested answer

Rules:
- claim before investigating assigned work
- answer with evidence
- close only after the requester has consumed the answer
- do not use agent-board for general progress notes

Commands:
- agent-board prompt --tool <tool> --agent <agent-id>
- agent-board inbox --for-agent <agent-id> --mark-seen --json
- agent-board ask ...
- agent-board claim ...
- agent-board answer ...
- agent-board close ...
```

## Anti-patterns

Avoid teaching skills to do any of the following:

- post broad conversational updates to the board
- dump long notes without a specific question or answer
- close threads automatically after answering
- use inconsistent agent names across repos
- treat the board as durable memory instead of ephemeral handoff

## Suggested rollout

Start with one Claude skill and one Codex skill that only encode:

- identity convention
- startup mailbox check
- ask/claim/answer/close rules

Only add more behavior after you have used the board in real cross-repo sessions and know what repetition is worth capturing.
