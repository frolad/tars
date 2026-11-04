---
name: sttp-guards
description: Show or switch the TARS git guard. "off" stops it from checking git steps in this session; "on" turns it back on. "default off|on" sets it for every session without its own on or off, in every project. No argument shows the session's state and the default. STTP's other rules stay on.
disable-model-invocation: true
---

The TARS prompt hook already handled this command and reported the result in its output. Repeat that one line to the user. Nothing else.

on: git add, commit, push, tag, stash, reset and restore --staged ask first (Claude Code) or need the user's latest message to name them (Codex), in this session.
off: git steps are not checked until /sttp-guards on or the end of the session.
default off|on: the guard in every session that has not used on or off, open ones too, in every project and in both tools. With no default set, it is on.
