# workshop-forge tests

Twenty-nine cases for the skill-creator loop, in `evals.json`: `/workshop-forge` alone picking and running the first
iteration, a decision in the mini grill, "continue", a breaking point, a reorganization, whose report must suggest no
QA, several fixes at the default size, starting from a session without a blueprint, whose record file keeps out a
customer's name and a home path from the session, research started from a session outside git, the end of a pipeline,
which offers the hardening phase's three picks, a cleanup, the code review and QA, recommended, QA only, or no
hardening, and waits for the user's pick, with no code review run and no review skill asked for yet, and whose record
file says built, a "continue" that leaves two things for a later iteration, which must reach the blueprint's files
and not only the report, since the chat is gone after a compaction, a broken test helper the iteration must go
around, flag first and offer to fix as an iteration of its own, a "continue" whose decision and trap must reach the
pipeline's file of the TARS Blueprint Record in the same turn, the end of a task's only pipeline after the code
review alone, asked for in the user's own words, which sets that file's State from built to done and starts no QA,
the answer to a mini grill's question on a blueprint whose knowledge gives every decision a question number, which
the new decision and the code comment must not copy, a "continue" whose iteration moves the last caller of an old
store, after which the next iteration must be the delete of that store, on its own, though the plan has it in a
cleanup at the end, a "continue" whose iteration, as planned, has the intake write each sale to both the old store
and the new one, while the move of the old store's last reader is blocked: before any code, the reply must propose
not to build that write, the earlier cleanup instead, and say what stops working and until when, for the user to
confirm, the same "continue" with the user keeping that write: the iteration builds it without asking again, and its
report must say that a later iteration removes that code, name the iteration, and say which tests go with it, and the
same "continue" in a repo where a job the plan never mentions still reads the old store: before any code, the reply
must name that job and ask the user what to do with it, and four on the name and the place of an iteration added to a
plan that is running: a fix the user asks for in the work of the iteration just finished, before the next planned
one, which must be named after the finished one, 3.1.a, in a row right after it, work the next planned iteration
needs first, which must split that iteration, its row kept with the status SPLIT and its parts, 3.1.a and 3.1.b, in
the rows under it, a second find inside an iteration already split, which must split the part not started the same
way, 3.1.b.a and 3.1.b.b, and the last part of a split iteration that is a release point, after which the reply must
say that the other pipeline can start, with the lines that name the release point left as written. In each of the
four, the names of the status table must read in order from top to bottom, and no row the plan had may get another
name. Six cases on the hardening phase and the QA suggested after an iteration follow: both picked, the code review
then QA, in a session with no cleanup skill, after which the reply starts the code review as before, with the commit
suggestion, the range from the Base commit and the review skills listed with no recommendation, and says QA comes
after the code review's fixes; QA next after those fixes, in a session that lists two QA skills, one of them the
repository's own skill on starting the app and signing in, whose description does not say QA: both listed, with no
recommendation, and the agent's own QA offered as one more pick; QA only picked in a session with no QA skill, where
the reply offers the agent's own QA and says what it checks; the agent's own QA run on an app the run can start,
where the change shows on the monthly page and in its JSON and the page's link to its JSON drops the region, a
finding the run must put to the user, unfixed; and a code review's four findings, one wrong about the code and two
about code the pipeline did not change, which must be checked in the code, the wrong one shown with what the code
says, and the two older ones asked about in one question for the group; and a "continue" whose iteration makes the
monthly page's JSON link keep the region, a change no test sees as a user would, after which the report must suggest
a small QA of it in the running app and leave it for the user to ask for. The last case is the end of a pipeline in a
session whose cleanup skill has another name, tidy-diff, and no simplify: the hardening offer must recommend a
cleanup with it, then the code review, then QA, or those two with why QA is left out, since the offer is built from
the kinds of skills, not their names.
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
  `store-intake-next` builds on the workshop-craft fixture `store-approved`, by calling its script: sales kept in a
  JSON-lines file store, partway through their move to SQLite, `.blueprints/sales-sqlite/`. The pages, the jobs and
  the admin correction use SQLite; the intake, the next iteration, is the file store's last caller; and the plan
  has a sales list by month before the cleanup that deletes the file store.
  `store-export-waits` is the same repo at an earlier state of that move: the pages and the backup use SQLite, the
  accounting export still reads the file, its move blocked until a colleague's branch is merged, and the next
  iteration, as planned, has the intake write each sale to SQLite and to the file. Two cases run on it.
  `store-missed-caller` is `store-export-waits` plus one commit, made after the plan: `jobs/stock_alert.py`, a job
  that reads the sales from the file store and that the blueprint never mentions.
  `writer-moved` and `access-split` hold plans with names of the lettered form. `writer-moved` is `inline-csv` after
  its sales list iteration was split: 3.1 is SPLIT, its part 3.1.a, the CSV writer moved out of the monthly view, is
  done and committed, and its part 3.1.b, the sales list CSV, is next; the moved writer still writes the monthly
  report's header and columns only. `access-split` is `ready` after its first iteration, the release point for
  pipeline 2, was split: 1.1 is SPLIT, its part 1.1.a, the finance role, is done and committed, and its part 1.1.b,
  the access rule, is next.
  `region-served` is `region-done` whose app runs on a local port: `serve.py`, committed before the pipeline's Base,
  serves the monthly page, its JSON and the admin sales list from a few sales, after a sign-in at `/login?as=<role>`,
  takes a free port and prints its address, and logs every request to `serve.log`, which git ignores; the end of the
  pipeline waits on the user's pick of the hardening phase. `region-fixed` is `region-served` after the hardening's
  code review: its one fix, a region typed with spaces around it, is done and committed, and QA is next.
  `region-link-next` is `region-served` with two more iterations planned: the page's JSON link that keeps the region,
  next, and the region in the page's heading; its record says in progress.
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
  for comparison, run `python3 -m unittest` in the run's repo, call its CSV views and access rule, post a sale to
  the store repo's intake, or read the requests the served app logged, and read the red step from the test runs in `events.json`. Compared with the fixture,
  the TARS Blueprint Record's files, under `docs/tars-reports/<name>/` for a blueprint `.blueprints/<name>/`, count
  neither as changed files nor as changed code, and neither does the served app's `serve.log`; `record_files` holds that rule for the craft and glossary graders
  too.
- `test_grade.py` checks `grade.py` itself on runs built from the fixtures, such as a reply that asks for the
  commit with "Before the review, commit ...": `python3 -m unittest discover -s evals/workshop-forge`.

Results go in a workspace outside the repo, `<workspace>/iteration-N/eval-<id>-<name>/<config>/run-N/`, with the
fixture repo in `run-N/repo/`.
