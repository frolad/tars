# Changelog

Changes from 0.7.0 on. Each version's section is also its GitHub release's text.

## 0.7.0

The first public version of TARS and of its optional mod, tars-mod, after 0.5.4 and 0.1.10.

### Platforms

- Native Windows: Claude Code and Codex CLI, checked in real sessions on Windows 11.
- The Claude desktop app, checked on Windows 11, with the mod's status line and pipeline pane.
- macOS, through the hook and mod tests that CI runs.

### Changes

- Session notes in `~/.tars` (the `paused-`, `guards-off-` and `forge-` files) are deleted at session start once
  untouched for 30 days, in Claude Code and Codex. Before, they were never deleted. The settings files stay.
- `/tars-doctor` says when a session goes on from a conversation TARS could not trace, such as a move to the
  background that Claude Code did not record: the session's pause, git guard switch and pipeline did not come along.
- The mod no longer redraws its status line when a subagent's turn starts.
- On Windows, the hooks and the mod keep their notes in the same folder: `HOME` when it is set, else your profile
  folder. Before, with no `HOME`, as in a normal Windows terminal, the mod wrote its notes to a folder named
  `undefined\.tars` inside the project, and the hooks never saw them.
- The README tells Windows users how to get a real `python3`: a fresh Windows has only the Microsoft Store's
  shortcut, on which every hook fails.

### For contributors

- CI runs on every push and pull request: the hook tests on Linux, macOS and Windows with the newest Python, and on
  Linux with Python 3.9 too, and the mod tests on all three with Claude Code's latest release.
- `tests/windows/` sets up a Windows 11 VM in Docker for the checks CI cannot run: real sessions in Claude Code,
  Codex and the desktop app. Its README has the steps and what each check should show.
- The skill tests' graders for sttp-enforce, workshop-glossary-bootstrap, workshop-grill, workshop-glossary and
  workshop-forge no longer fail a run for reasons outside the skill. Each fixed grader has a `test_grade.py` next to
  it that checks the grader with no model.
