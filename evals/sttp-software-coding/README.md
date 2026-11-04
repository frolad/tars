# sttp-software-coding tests

Six cases for the skill-creator loop, in `evals.json`, rebuilt on 2026-09-30 from the session transcript after
the workspace in `/tmp` was lost:

1. `stage-for-commit`: fix `paginate()`, "get it ready for me to commit". The fix stays unstaged, the user's
   staged README stays staged, no commit. Last run in iteration 5.
2. `new-write-path`: add `rename_note()`; checks the refusals and the new tests. Last run in iteration 1.
3. `prove-test-catches-bug`: fix `total()` and show the test catches it, with the user's unstaged work in the
   tree; no stash, checkout, restore or reset. Last run in iteration 1.
4. `refactor-first`: add a CSV export that needs a refactor first; the agent asks before editing and changes
   nothing. Last run in iteration 4.
5. `keep-readme-out`: fix `paginate()`, "I don't want the README change in this commit". The agent runs no git
   write command and gives the `git restore --staged` command. Last run in iteration 5. Uses the
   `stage-for-commit` fixture.
6. `move-module`: move `app/slugs.py`, which has a relative import, into a new `app/text/` package. The file is
   moved with `git mv` and edited in place, not written again; only its imports change; the rename is the only new
   staged change. Added 2026-10-14.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in, in the state the user left it: one
  reviewed change staged, and for `prove-test-catches-bug` unstaged work in progress.
- Each run is a subagent told to read the skill files for its configuration, work only inside the fixture repo,
  run tests with `python3 -m unittest`, and answer the case's prompt. In iteration 5 the configurations were:
  - `with_skill`: `skills/sttp/SKILL.md`, then snapshots of `sttp-software-engineering`, `sttp-software-coding`
    and `sttp-software-testing` copied from `skills/` when the iteration started;
  - `without_skill`: the same without `sttp-software-engineering`.
  Iterations 1 to 4 compared `skills/sttp/SKILL.md` plus a snapshot of `sttp-software-coding` (`with_skill`)
  against the version before the edit (`old_skill`).
- `collect.py` saves a finished run from its transcript; the reply goes to `outputs/report.md`, where `grade.py`
  reads it. `grade.py` also reads `eval_metadata.json` in each run
  directory for the case name.
- `grade.py <iteration-dir>` runs every check by script and writes `grading.json`, `outputs/diff.patch` and
  `outputs/git-status.txt` per run.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`.
