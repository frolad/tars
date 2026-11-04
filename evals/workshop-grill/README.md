# workshop-grill tests

Five cases for the skill-creator loop, in `evals.json`: the first round of a full grill, "explain" and "idk"
answers, light mode with nothing to ask, light mode with one decision, and a round in the middle of workshop-craft
that re-reads the approved checks (plain terms: titles by subject, what goes wrong, no bare labels). Not a `claude plugin eval` suite: that
one is the `prompt.md` cases next to this folder.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in (`base`, `light-clear`,
  `light-decision`, `self-check`).
- Each run is a subagent told to read `skills/sttp/SKILL.md`, `skills/sttp-software-engineering/SKILL.md` and
  the skill under test (a snapshot of `skills/workshop-grill/`, or the baseline: Matt Pocock's upstream
  `grilling`), not to use the Skill tool, and to answer the case's prompt in the fixture repo. Subagents have no
  question tool (AskUserQuestion), so the cases test the text form of a round; the tool's form is checked only in a
  real session.
- `collect.py` saves a finished run from its transcript. `grade.py <iteration-dir>` runs the scripted checks
  and merges `judgement.json`, the checks graded by reading the reply.
- `test_grade.py` checks `grade.py` itself on runs built from the fixtures, such as a question titled with one
  word, or a run that lists a skill's folder: `python3 -m unittest discover -s evals/workshop-grill`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`.
