---
name: workshop-questions
description: Show or set how workshop-grill asks its questions. "dialog" uses the harness's question dialog when it has one (default); "transcript" asks them as text in the session's transcript. No argument shows the current form. Persistent across sessions, shared between Claude Code and Codex.
---

The TARS prompt hook already handled this command and reported the result in its output. Repeat that one line to the user. Nothing else.

dialog: grill rounds go through the question dialog (AskUserQuestion in Claude Code) when there is one. Default.
transcript: grill rounds are asked as text in the transcript: in workshop-craft, in workshop-forge's mini grill and in /workshop-grill.
