# workshop-glossary-bootstrap tests

Four cases for the skill-creator loop, in `evals.json`: the plan turn, the turn after the plan is confirmed, which
mines the first area and proposes its first group, the turn after the user answers that group, and the same answer
in a project whose glossary is a `CONTEXT.md` in its own format. Not a `claude plugin eval` suite.

- `fixtures/make_fixture.sh <fixture> <dir>` builds toolshed, a tool library's app with three areas: catalog, members
  and loans. Loans uses the other two, so a core-first order puts it last. The code calls a tool `Item` while every
  page says "tool", and a 2025-03-14 commit replaced deleting tools with retiring them; its message is the only place
  that says why. `.blueprints` is ignored.
  - `bare`: no glossary and no decision records.
  - `proposed`: `bare` after the turn that proposed the catalog's first group, with the working file from
    `fixtures/proposed-bootstrap.md`.
  - `context`: `bare` with a committed `CONTEXT.md` (Tool, Deposit, a Condition the code contradicts, Member), after
    the turn that proposed the catalog's first group for it, with `fixtures/context-bootstrap.md`.
- Cases 2 to 4 give the earlier turns as "The conversation so far"; the working-file fixtures hold the same proposal.
- Each run is a subagent in the fixture repo, set up as in workshop-forge's tests: no Skill tool, the always-loaded skills
  read from files, the case's prompt as the user's message. Where a skill says to load workshop-glossary with the Skill
  tool, the run reads its file, so "loaded" means its SKILL.md was read. The configs:
  - `with_skill`: a snapshot of the skills in `<workspace>/snap-<n>/skills/`.
  - `without_skill`: the same snapshot without workshop-glossary-bootstrap, whose frontmatter description is all the run
    gets of it.
- `grade.py <iteration-dir>` runs the scripted checks, with the helpers of `../workshop-forge/grade.py`, and merges
  `judgement.json`, the checks graded by reading the reply. Runs are collected with `../workshop-forge/collect.py`.
- `test_grade.py` checks `grade.py` itself on runs built from the fixtures, such as a members' proposal with no
  `_In the code_` line: `python3 -m unittest discover -s evals/workshop-glossary-bootstrap`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
