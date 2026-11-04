# TARS Blueprint Record: TARS 0.7: the release

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
TARS goes from 0.5.4 to 0.7 before its repository is made public, so that people who install it from the marketplace
meet fewer surprises: it is checked on native Windows, macOS and the desktop app, the gaps earlier tasks left are
fixed, and the tests run on every push. This pipeline is the whole task: CI, the fixes, the Windows checks, the eval graders, and the README, changelog and versions of the release.

## Planning decisions
- Today's names become the 0.7 names, with no review first.
  Why: a rename before 0.7 would move files users already have, as the `sttps` to `tars` rename moved `~/.sttps`.
  Rules out: renaming commands, phrases, settings files or blueprint files before 0.7.
- 0.7 supports the terminal on Linux, WSL, native Windows and macOS, the desktop app, and Codex CLI. macOS is checked
  by CI only.
  Why: native Windows and the desktop app had never been checked; the hook tests run the hook the way the tools do,
  which covers macOS without a Mac.
  Rules out: listing a platform as not checked; a real session on a Mac as a check of 0.7.
- Every native Windows check runs in one Windows 11 VM in Docker, set up from `tests/windows/`: Claude Code, Codex
  and the desktop app.
  Why: Windows containers have no desktop, and anyone can rerun the checks from the repository.
  Rules out: checks on a developer's own Windows setup; Codex on Windows left to WSL.
  Known cost: CI cannot run the VM, since it needs KVM.
- Session notes in `~/.tars` untouched for 30 days are deleted at session start.
  Why: it works the same in Claude Code and Codex with no new hook; a lost note only turns STTP, the guard or the
  status line's pipeline back on, and only for sessions resumed after a month.
  Rules out: a shorter limit; a session-end hook.
- CI runs the hook tests and the mod tests on Linux, Windows and macOS on every push and pull request.
  Why: a release should not rely on someone remembering to run the tests.
  Rules out: the evals in CI, since they call a model.
- Changes from 0.7.0 on go into `CHANGELOG.md` at the repository's root and into a GitHub release per version.
  Why: the marketplace shows only a version number.
  Rules out: git log as the only record of changes; a changelog for the versions before 0.7.0.
- The mod goes to 0.7.0 with the plugin, from 0.1.10.
  Why: it is checked on Windows and in the desktop app in this task too, and one version story is simpler for users.
  Rules out: the mod keeping its own version numbers.

## Not in this task
- Making the repository public: the license file, the `preparations/` folder, a README for strangers, the git
  history. Why: a task of its own after 0.7.
- Pushing the tag and creating the GitHub release. Why: the developer's steps; this task writes their text.
- The evals in CI. Why: they call a model and stay run by hand.
- A real session on a Mac. Why: there is no Mac to run one; CI covers macOS.

## What was built
- A GitHub Actions workflow, `.github/workflows/tests.yml`, runs on every push and pull request: the hook tests on
  Linux, macOS and Windows with the newest Python, and on Linux with Python 3.9 too; and the mod tests on Linux,
  macOS and Windows, with Claude Code installed from its `latest` channel and no login.
- Every session start, in Claude Code and in Codex, deletes the per-session notes in `~/.tars` (`paused-<session>`,
  `guards-off-<session>`, `forge-<session>`) untouched for 30 days; the settings files `mode`, `questions` and
  `guards-default` stay (`hooks/sttp.py`).
- A subagent's turn start no longer redraws the mod's status line; the main thread's turn start still does
  (`mods/tars-mod/hooks/tars-mod.js`).
- `/tars-doctor` says when a session goes on from a conversation that Claude Code's move line does not name: the
  notes such a session had before a move or a copy (the pause, the git guard switch, the pipeline) did not come
  along (`hooks/sttp.py`).
- The hook and the mod keep their notes in the same folder on every system: `~/.tars` under `HOME` when it is set,
  else under the user's profile folder, which is all a Windows terminal sets. Before, the mod's commands on native
  Windows wrote into an `undefined\.tars` folder inside the project, where the hook never looked.
- `tests/windows/` sets up a Windows 11 VM in Docker for the checks CI cannot run: real sessions in Claude Code,
  Codex and the desktop app on native Windows. Its README gives the steps, the messages to send and what each one
  should show.
- The README's Install section tells Windows users that a fresh Windows has only the Microsoft Store's `python3`
  shortcut, on which every hook fails, and how to get a real one from python.org's install manager.
- The sttp-enforce grader grades a run whose `brewlog/cli.py` no longer parses, failing the checks that read the
  code, instead of stopping the whole grading pass; `evals/sttp-enforce/test_grade.py` checks it with no model.
- The glossary-bootstrap grader's check that the members' proposal names Account in its `_In the code_` lines fails
  when the reply shows no such line, instead of passing on an empty list; `test_grade.py` next to it checks both
  cases that use it.
- The grill grader takes a one-word question title such as "Totals" as naming its subject; a label alone such as
  "Done when 4" still fails. `test_grade.py` next to it checks both.
- workshop-glossary's check that a reply in a project without a glossary says nothing about one no longer counts the
  run's own folder in the reply's file links, which the test workspaces name after the skill.
- workshop-grill's check that no other skill was loaded counts only reads of a `SKILL.md`, not a listing of a
  skill's folder or a line of a command's output.
- workshop-forge's test 9, the end of a pipeline, has in its sample project the test its scope's drift risk names,
  each CSV's amounts against its page, so a run reaches the commit and the review instead of stopping at that risk.
- workshop-forge's check that the reply suggests a commit also takes one asked for as an instruction ("Before the
  review, commit the pipeline's work"); a "Commit point:" line still does not count. `test_grade.py` next to the
  grader checks both ways.
- The README lists the platforms checked for 0.7, with their versions.
- `CHANGELOG.md` at the repository's root has a 0.7.0 section, written to be pasted as the GitHub release's text:
  the platforms, the changes users notice, and a short part for contributors.
- The plugin, for Claude Code and for Codex, and the mod are at version 0.7.0 in their manifests.

## Build decisions
- CI runs the hook tests on the newest Python on every system, plus Python 3.9 on Linux.
  Why: the hook calls whatever `python3` the user has, and on a Mac without Homebrew that is Apple's 3.9; the hook
  uses only the standard library, so a break on an old Python shows on Linux as well.
  Rules out: the newest Python only; every Python version on every system.
- CI installs Claude Code from the `latest` channel to run the mod tests.
  Why: it is the default channel, which most users run, so a Claude Code release that breaks the mod shows at the
  next push.
  Rules out: the `stable` channel; a pinned version.
  Known cost: a CI run can go red from a Claude Code release with no change in TARS.
- Windows joins CI only once the hook tests and the mod tests pass there.
  Why: a CI run should never be red for a known cause.
  Rules out: a Windows job that fails, or one allowed to fail, until the fixes.
- A session that goes on from a conversation no move line names is told so only by `/tars-doctor`.
  Why: the hook cannot tell it from a session resumed under its own id after its scratchpad was cleared, so a line
  in every such session would sometimes be a false alarm; one shown on request costs nothing.
  Rules out: a line in the session at its first hook call; leaving it out of 0.7.
  Known cost: a session resumed after its scratchpad was cleared gets the note too, though it lost nothing.
- The notes live under `HOME` when it is set, else under the user's profile folder, for the hook and the mod alike.
  Why: the two can never split, whatever a user sets, and the hook tests, which give each test its own `HOME`, stay
  apart on Windows too.
  Rules out: the profile folder on Windows whatever `HOME` says; a fix in the mod alone.
- The hook commands call `python3` on every system; on Windows the README asks for a real one.
  Why: a fallback to `python` and `py` would run a hook that fails for another reason again under the next name.
  Rules out: a fallback in the hook commands.
  Known cost: a Windows user without a real `python3` gets failing hooks until they read the README.
- Each grader fix comes with a `test_grade.py` next to its grader, run by hand with no model, not in CI.
  Why: a later change to a grader can be checked again, without a model run.
  Rules out: grader fixes with no kept test; grader tests in CI, whose fixtures need bash and git on every system.
  Known cost: files in `evals/` that only a manual run checks.
- The changelog's 0.7.0 section lists the changes users notice first, then a short part for contributors.
  Rules out: a release text with users' changes only.
- workshop-craft's test 4 is not run again: its last run, on the same test and skill, passed in all four runs. The
  failure once noted for it was on an earlier version of the test, which was rewritten since.
  Rules out: a new run of the test in this task.
- workshop-forge's test 9 is fixed in its sample project, not in its expectations: the project gets the test its
  scope's drift risk names, one that compares the amounts of each CSV with its page.
  Why: the scope stays as written, and the case also checks that the end of the pipeline finds a risk that is
  covered.
  Rules out: taking the risk out of the sample scope; a test that accepts a stop at the risk.
- workshop-glossary's case 6 ignores only the run's own folder when it looks for talk of a glossary.
  Why: a path the reply mentions in prose, such as `docs/GLOSSARY.md`, is still talk of a glossary.
  Rules out: ignoring every path or link in the reply.

## Tried and dropped
- A promise that the commands and phrases, the settings files in `~/.tars` (`mode`, `questions`, `guards-default`),
  the `.blueprints/` layout and its file formats, the record folder `docs/tars-reports/`, and the mod's command and
  its `/config` switches stay as they are until the next major version, with the skills' wording and the
  per-session notes not covered. Dropped because: the release came out as 0.7.0, and a 0.x version makes no such
  promise.

## Traps
- Python on Windows ignores `HOME` for `~` and reads only `USERPROFILE`, and Claude Code gives a mod no `HOME` when
  the terminal has none; code that builds a home path from either alone splits from the other on Windows.
- On Windows, Claude Code's mod test kit turns the paths a mod asks for into Windows paths before a test's fake file
  system sees them: `/home/u/.tars/mode` arrives as `C:\home\u\.tars\mode`. A fake keyed by `/` paths finds nothing.
- `claude plugin test` needs no login, so CI runs the mod tests with no stored key.
- A note carried over to a session moved to the background keeps the original note's time, so its 30 days count
  from the last write under the old session.
- A session moved to the background (`/bg`) goes on under a new id, in a new transcript that starts with a copy of
  the old conversation since its last compaction: each message keeps its id from the old transcript, with the new
  session's id written in. Only the old transcript's last lines name the new session (a `continued-in` line, which
  Claude Code does not document); nothing in the new transcript names the old one.

## Known issues
- The `/tars-doctor` note rests on one move recorded with Claude Code 2.1.295: that a moved session's transcript
  holds the conversation it goes on from by its first hook call. Unchecked on later versions.

## Postponed
- The empty `sttp-carried-<session>` files the hook leaves in Claude Code's plugin data folder, one per session that
  called it without a scratchpad, are never deleted. Why: the 30-day cleanup covers only `~/.tars`, as planned.
