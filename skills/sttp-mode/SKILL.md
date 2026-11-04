---
name: sttp-mode
description: Show or set the STTP mode. "primary" applies STTP to the main thread only (default), "full" also to subagents. No argument shows the current mode. Persistent across sessions, shared between Claude Code and Codex.
---

The TARS prompt hook already handled this command and reported the result in its output. Repeat that one line to the user. Nothing else.

primary: STTP rules in the main thread only. Default.
full: rules also injected into every subagent; the coding rules fire inside subagents too.
