# workshop-craft tests

Ten cases for the skill-creator loop, in `evals.json`: the first round of a new task, a request that is several
tasks, the short path, writing the scope sections that have no question of their own, approving Out of scope and
proposing the split, writing the split and asking for the review, a task taken from the session, a research task
outside git, the user's OK to the review, and the answers to the first round, which bring the blueprint's first
files. Not a `claude plugin eval` suite: that one is the `prompt.md` cases next to this folder.

- `fixtures/make_fixture.sh <fixture> <dir>` builds the repo a case runs in. `base` is the reports repo with
  `.blueprints` not ignored by git; `ignored` is the same repo with `.blueprints` ignored and no blueprint yet.
  `scope-started`, `scope-approved`, `split-proposed` and `review` ignore `.blueprints` and hold
  `.blueprints/finance-exports/` as workshop-craft left it at that point of the case's conversation.
- Each run is a subagent working in the fixture repo, told not to use the Skill tool, to read
  `skills/sttp/SKILL.md`, `skills/sttp-software-engineering/SKILL.md` and `skills/workshop-grill/SKILL.md`, and to
  answer the case's prompt as the user's message. The two configs differ in what the user's `/workshop-craft` brings:
  - `with_skill`: a snapshot of `skills/workshop-craft/` in `<workspace>/workshop-craft-snapshot/`. The run reads its SKILL.md
    and follows it; where it says to load workshop-grill with the Skill tool, it reads that file instead.
  - `without_body`: only workshop-craft's frontmatter description, given in the prompt as what `/workshop-craft` does. The run
    reads no workshop-craft file.
- `collect.py` saves a finished run from its transcript. `grade.py <iteration-dir>` runs the scripted checks
  and merges `judgement.json`, the checks graded by reading the reply. Its check of the files outside `.blueprints`
  also fails on a TARS Blueprint Record, since workshop-craft writes none: the files under `docs/tars-reports/<name>/`
  for a blueprint `.blueprints/<name>/`, a rule it takes from `../workshop-forge/grade.py`. The name of the pipeline state file is
  `PIPELINE_FILE` in `grade.py`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
