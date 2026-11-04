# sttp-software-testing tests

Three cases for the skill-creator loop, in `evals.json`: a new write path (`rename_note`, red first, one
slice at a time), proving a test catches a bug (the double-counted discount in `total()`, with the user's
unstaged work and staged `README.md` left alone), and a new seam (retry in `fetch_rates()`, where a test needs
a fake: ask before editing). Not a `claude plugin eval` suite: that one is the `prompt.md` cases next to this
folder.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in, in the state the user left it
  (one reviewed change staged; for the cart case, unstaged work in `cart.py` and `shipping.py`). It also has
  the coding skill's cases, `stage-for-commit` and `refactor-first`, which `grade.py` still grades.
- Each run is a subagent told to read the skill files below, to work only in the fixture repo, to run tests
  with `python3 -m unittest`, and to return its final reply to the user:
  - `with_skill`: `skills/sttp/SKILL.md`, a snapshot of `skills/sttp-software-coding/` after Edit 3 (its
    test-writing lines moved out) and a snapshot of `skills/sttp-software-testing/` (`new-coding`,
    `new-testing`, copied from the repo on 2026-09-30).
  - `old_skill`, the baseline: `skills/sttp/SKILL.md` and the coding skill before Edit 3, with its own test
    lines and the "ask before editing" refactor line (`old-coding`, the coding workspace's `skill-iter4`).
- `collect.py` saves a finished run from its transcript; the reply goes to `outputs/report.md`, where `grade.py`
  reads it. `grade.py <iteration-dir>` grades every run from the repo, the reply and
  `events.json`, and writes `grading.json`, `outputs/diff.patch` and `outputs/git-status.txt`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, each
run with `eval_metadata.json` (`eval_name` picks the grader).
