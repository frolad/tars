# sttp-software-engineering tests

Five cases for the skill-creator loop, in `evals.json`: a question that must get an answer and no change
(`question-no-change`), a near-fit type to reuse (`near-fit-reuse`), a bug that already existed, to list and
not fix (`pre-existing-bug`), a broken `make check` to go around, flag first and leave to the user
(`broken-check`), and the first case's question again, whose reply must name files as VS Code links
(`file-links`). Not a `claude plugin eval` suite: that one is the `prompt.md` cases in `evals/`.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in: `stage-for-commit` (used by
  `question-no-change` and `file-links`), `near-fit-reuse`, `pre-existing-bug`, `broken-check`. Every fixture has a staged `README.md` change,
  which the graders check stays the only staged file. The script also holds the coding and testing skills'
  cases (`new-write-path`, `prove-test-catches-bug`, `refactor-first`, `new-seam`), because it grew through
  those workspaces.
- Each run is a subagent told it is the coding assistant for the fixture repo, to read skill files and follow
  them, to work only inside the repo, and to return its final reply to the user:
  - `with_skill`: `skills/sttp/SKILL.md`, then snapshots of `sttp-software-engineering`,
    `sttp-software-coding` and `sttp-software-testing`;
  - `without_skill`: the same without `sttp-software-engineering`.

  The snapshots were copies of `skills/` taken when the workspace was set up (2026-09-30).
- `collect.py` saves a finished run from its transcript; the reply goes to `outputs/report.md`, where `grade.py`
  reads it. `grade.py <iteration-dir>` picks the grader from each run's
  `eval_metadata.json` (`eval_name`), writes `grading.json`, `outputs/diff.patch` and `outputs/git-status.txt`.
  It also holds the coding and testing graders, for the same reason as the fixture script.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`.
Iteration 1 (one run per configuration): with_skill 4/4, 9/9, 9/9; without_skill 4/4, 7/9, 6/9. The difference
is the report: explicit reused and new lines, what it affects, numbered findings.
`file-links` (2026-10-26, one run each, against the skill files of that day instead of the snapshots): with_skill
3/3, without_skill 0/3. Without the skill the reply named `app/pages.py:3` as plain inline code.
