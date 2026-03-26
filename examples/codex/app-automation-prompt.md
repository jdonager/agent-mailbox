Check whether `agent-mailbox` has any open threads for `codex-repo-a`.

1. Run `agent-mailbox prompt --tool codex --agent codex-repo-a`.
2. If there are no open threads, end with `No agent-mailbox work`.
3. If there are open threads, summarize each thread ID, subject, and state.
4. Do not modify repository files unless I explicitly ask.
