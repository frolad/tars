# workshop-forge tests

Fourteen cases for the skill-creator loop, in `evals.json`: `/workshop-forge` alone picking and running the first
iteration, a decision in the mini grill, "continue", a breaking point, a reorganization, several fixes at the
default size, starting from a session without a blueprint, whose record file keeps out a customer's name and a home
path from the session, research started from a session outside git, the end of a pipeline, whose record file says
built, a "continue" that leaves two things for a later iteration, which must reach the
blueprint's files and not only the report, since the chat is gone after a compaction, a broken test helper
the iteration must go around, flag first and offer to fix as an iteration of its own, a "continue" whose decision
and trap must reach the pipeline's file of the TARS Blueprint Record in the same turn, the end of a task's only
pipeline, which sets that file's State from built to done, and the answer to a mini grill's question on a blueprint
whose knowledge gives every decision a question number, which the new decision and the code comment must not copy.
Not a `claude plugin eval` suite: that one is the `prompt.md` cases next to this folder.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in, by real commits, so its tests pass at
  HEAD. `base` is the reports repo with no blueprint and `.blueprints` not ignored by git. `ready`, `access-done`,
  `wrong-fact`, `inline-csv`, `csv-done` and `pipeline-done` ignore `.blueprints` and hold workshop-craft's finished
  blueprint `.blueprints/finance-exports/` (three pipelines: CSV downloads, PDF downloads, download links) at the
  state the code is in. In `pipeline-done` every iteration of pipeline 1 is done, its `iterations.md` has a
  `Base:` line, and the last two iterations are left uncommitted, with a test that compares the amounts of each
  CSV with its page, the check the scope's drift risk names. `broken-helper` is `csv-done` plus a
  `sample_sales()` in `tests/helpers.py` whose data file was renamed without it, which the next iteration's line
  names. `record` is `access-done` plus pipeline 1's file of the task's TARS Blueprint Record,
  `docs/tars-reports/finance-exports/01-csv-downloads.md`, committed. `region-done` is another task,
  started from a session: a region filter on the monthly report whose one pipeline, `.blueprints/region-filter/`, has
  every iteration done and committed, with its record file, `docs/tars-reports/region-filter/01-region-filter.md`,
  committed and saying built. `tagged` is `access-done` with a question number after every decision of the
  blueprint's knowledge, as real blueprints have them: "Decided by the user on 2026-09-30 (Q3).". workshop-craft's
  are Q1 to Q11 in file order, and pipeline 1's knowledge also holds the answers to the mini grill of Access,
  iteration 1.1, Q1 and Q2 of the forge session the case's conversation shows.
  `research` is a folder outside git with a `notes.md`.
- Each run is a subagent working in the fixture repo, told not to use the Skill tool, to read
  `skills/sttp/SKILL.md`, `skills/sttp-software-engineering/SKILL.md`, `skills/workshop-grill/SKILL.md`,
  `skills/sttp-software-coding/SKILL.md` and `skills/sttp-software-testing/SKILL.md` (as the hooks would load
  them), and to answer the case's prompt as the user's message. A case with `session_skills` also gives the run
  that list as the skills the session shows, since the run cannot call the Skill tool. The configs differ in what
  the user's `/workshop-forge` brings:
  - `with_skill`: a snapshot in `<workspace>/workshop-forge-snapshot/`, holding `workshop-forge/` and `workshop-craft/` side by
    side so that workshop-forge's `../workshop-craft/formats/` resolves. The run reads
    `workshop-forge-snapshot/workshop-forge/SKILL.md` and follows it; where it says to load a skill with the Skill tool, it
    reads that skill's file instead.
  - `without_body`: only workshop-forge's frontmatter description, given in the prompt as what `/workshop-forge` does. The run
    reads no workshop-forge or workshop-craft file.
  - an older workshop-forge, when a change is tested against the version before it: that version's snapshot, read like
    `with_skill`, in a config named `without_<change>` so that it sorts after `with_skill`.
- `collect.py` saves a finished run from its transcript. `grade.py <iteration-dir>` runs the scripted checks and
  merges `judgement.json`, the checks graded by reading the reply. The scripted checks rebuild a fresh fixture
  for comparison, run `python3 -m unittest` in the run's repo, call its CSV views and access rule, and read the
  red step from the test runs in `events.json`. Compared with the fixture, the TARS Blueprint Record's files, under
  `docs/tars-reports/<name>/` for a blueprint `.blueprints/<name>/`, count neither as changed files nor as changed
  code; `record_files` holds that rule for the craft and glossary graders too.
- `test_grade.py` checks `grade.py` itself on runs built from the fixtures, such as a reply that asks for the
  commit with "Before the review, commit ...": `python3 -m unittest discover -s evals/workshop-forge`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
