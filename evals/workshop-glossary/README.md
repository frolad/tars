# workshop-glossary tests

Seven cases for the skill-creator loop, in `evals.json`: the merge at the end of a pipeline, workshop-craft aligning a
task with the glossary, a workshop-forge iteration that meets a glossary entry it contradicts, `/workshop-glossary` asked to
add a term the glossary already covers, the turn after the user approves the merge's entries, and two cases in a
project with no glossary: the end of a pipeline, which skips the merge, and workshop-craft on a task whose word the code
names differently. Not a `claude plugin eval` suite.

- `fixtures/make_fixture.sh <fixture> <dir>` builds workshop-forge's reports repo (`../workshop-forge/fixtures/`) and commits
  `docs/GLOSSARY.md` and one ADR in `docs/adrs/` on top. The glossary says a finance user sees the reports of their
  own region only; the task gives finance every region. `merge` is workshop-forge's `pipeline-done` plus the drift test
  its scope's Risks name, so every check is met, and a Terms section in `00-knowledge.md`: terms of pipeline 1
  (built), 2 and 3 (not built), and a change to the glossary's Finance user. `merge-asked` is `merge` after the turn
  that proposed the merge: an ADR the pipeline supersedes, the decision naming it, and Current waiting on the user.
  `iteration` is `csv-done`, with no Terms. `craft` and `direct` are `ready`. `merge-bare` and `craft-bare` are
  `merge` and `craft` with no `docs/`, and `merge-bare`'s Finance user has no Changes the glossary line.
- Each run is a subagent in the fixture repo, set up as in workshop-forge's tests: no Skill tool, the always-loaded
  skills read from files, the case's prompt as the user's message. Where a skill says to load another with the
  Skill tool, the run reads that skill's file, so "loaded" means its SKILL.md was read. The configs:
  - `with_skill`: a snapshot in `<workspace>/snap-<n>/skills/` of workshop-craft, workshop-forge, workshop-glossary and
    sttp-software-engineering, read in place of the repo's.
  - `without_glossary`: the snapshot taken before the glossary, `<workspace>/snap-pre/skills/`, with no
    workshop-glossary. In case 4 the run gets only workshop-glossary's frontmatter description, as what `/workshop-glossary`
    does.
  - `old_skill`: the snapshot taken before a rework, with workshop-glossary, such as `<workspace>/snap-4pre/skills/`
    before the glossary became optional.
- `grade.py <iteration-dir>` runs the scripted checks, with the helpers of `../workshop-forge/grade.py`, and merges
  `judgement.json`, the checks graded by reading the reply. Its checks of `docs/` and of the files outside
  `.blueprints` let the TARS Blueprint Record through: the files under `docs/tars-reports/<name>/` for a blueprint `.blueprints/<name>/`. Runs are collected with `../workshop-forge/collect.py`.
- `test_grade.py` checks `grade.py` itself on runs built from the fixtures, such as a reply whose file links
  point into a folder named `workshop-glossary`: `python3 -m unittest discover -s evals/workshop-glossary`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
