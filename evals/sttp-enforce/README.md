# sttp-enforce tests

Three cases for the skill-creator loop, in `evals.json`: the analysis of a whole repo, the turn after the user picks
items from it, and the same turn for a skill file alone. Not a `claude plugin eval` suite.

- `fixtures/make_fixture.sh bare <dir>` builds brewlog, a small CLI that logs homebrew batches. Its README and usage
  page are full of filler; the overwrite warning is stated three times; the code and the README say 400 days where the
  usage page says one year; `brewlog/cli.py` has comments that restate the code, banners, a docstring that repeats the
  signature, a why comment and a printed message to keep; `.claude/skills/release/SKILL.md` has rules to keep, one of
  them stated four times. The files sttp-enforce leaves out are there too: a generated page, a lock file, a license, a
  changelog and a test fixture whose first line a test reads. The tests pass.
- Cases 2 and 3 give the analysis turn as "The conversation so far", written by hand for the fixture.
- Each run is a subagent in the fixture repo, set up as in workshop-forge's tests: no Skill tool, the always-loaded skills
  read from files, the case's prompt as the user's message. The configs:
  - `with_skill`: a snapshot of the skills in `<workspace>/snap-<n>/skills/`.
  - `without_skill`: the same snapshot, with the frontmatter description of sttp-enforce all the run gets of it.
- `grade.py <iteration-dir>` runs the scripted checks, with the helpers of `../workshop-forge/grade.py`, and merges
  `judgement.json`, the checks graded by reading the reply. Runs are collected with `../workshop-forge/collect.py`.
- `test_grade.py` checks `grade.py` itself on runs built from the fixture, such as one whose `brewlog/cli.py` no
  longer parses: `python3 -m unittest discover -s evals/sttp-enforce`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
