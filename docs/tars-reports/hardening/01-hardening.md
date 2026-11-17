# TARS Blueprint Record: QA and code review at the end of a forge pipeline: hardening

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
When a workshop-forge pipeline ended, TARS checked the Done when items, merged the glossary and guided the developer
to a code review whose findings became iterations; nothing in TARS checked the running software. In real sessions the
developer found the bugs the agent missed by running the app: in places that share the changed code, such as a second
menu, a second user, another content state or the page with its neighbours, and after changes made since the last
check, such as a fix, a refactor, a review fix or a merge. This pipeline makes room for QA in workshop-forge without
teaching TARS any project's specifics: a hardening phase at the end of a pipeline, in which the developer picks code
review then QA, code review only, QA only or no hardening, with the findings of both put to the developer as
decisions that become iterations; and, after an iteration whose change is significant, a small QA of that change
suggested when it would help. Eval cases show the difference.

## Planning decisions
- TARS knows QA exists and makes room for it, in a few sentences of workshop-forge; how to check a given app lives in
  that project's own skill.
  Why: TARS runs in any repository, and facts of one project or one machine do not hold in another.
  Rules out: QA rules, browser tools, ports, accounts and any project's facts in TARS text; a new TARS skill for
  hardening or for QA.
- At the end of a pipeline the developer picks the hardening the pipeline gets.
  Why: whether a pipeline needs it is the developer's call.
  Rules out: a code review or QA that starts without the developer's pick; QA before the code review as an offered
  order.
- The code review stays as workshop-forge runs it: the review skills the session has, listed with no recommendation.
  Why: developers use different review tools, in Claude Code and in Codex.
  Rules out: a TARS review skill; a recommended review tool.
- QA skills are found and offered the way review skills are: the repository's own and the user's own, listed with no
  recommendation. The agent's own QA is told one thing: build the checks from the whole change since the pipeline's
  first commit, every place that shows what changed, in the ways its users reach it, and report what was checked and
  what was not.
  Why: the agent checked the place it changed and missed the places that share it.
  Rules out: a list of QA rules in TARS.
- QA runs after the code review's fixes are built, and after QA's own fixes are built, the checks they touch run
  again.
  Why: a check made before a fix is out of date; a cleanup fix from a code review once broke every copy of a page,
  found only by a later browser pass.
  Rules out: QA run once, like the code review.
- The findings of code review and of QA go through the mini grill workshop-forge runs before each iteration: the
  agent checks each one in the code before it reaches the developer, each one that holds is a decision with a
  recommendation, and each fix taken is an iteration. Code review findings about code the pipeline did not change are
  shown together, marked as not related to it, with one question for the group: fix the ones the developer names,
  postpone them, or leave them as they are.
  Why: wrong review claims were passed on unchecked, and the developer wants to see which findings the change
  brought in.
  Rules out: findings fixed without the developer's pick; one question per older finding; older findings hidden.
- QA means checking the running software the way its users reach it: pages in a browser, API calls, an MCP server's
  tools. Tests and reading code are not QA.
  Why: software is reached in different ways, and each is where its users meet a bug.
  Rules out: QA that means the browser only.
- The rules are checked by new eval cases that fail with the text before this task and pass with the new text, and
  by the workshop-forge cases that reach a changed rule, old text against new, scoring no lower.
  Why: the only way to see the rules change what the agent does and break nothing else.
  Rules out: adding the rules on reading alone.

## Not in this task
- A project's own QA skill, such as the one for the project whose sessions started this task. Why: each project
  writes its own, in its own repository.
- The code review step itself: the commit suggestion, the range from the pipeline's first commit, the review skills
  with no recommendation, the review run once. Why: it works and stays as it is.
- QA outside workshop-forge: the rules every session loads get no QA line. Why: a project's own QA skill covers its
  other sessions.
- Hardening for work that is not code, such as research or a design. Why: its own check stays as it is.
- workshop-craft's steps, the hook and the mod. Why: they stay as they are; the mod shows no hardening state.
- The changelog entry and the version bump. Why: done at the next release.

## What was built
- workshop-forge's end of the pipeline has a hardening phase, in `skills/workshop-forge/SKILL.md`. After the Done
  when check and the glossary merge, the agent says what a cleanup, a code review and QA are, builds the picks from
  the kinds of skills the session lists at that moment, offers three picks, every kind it has in the order cleanup,
  code review, QA, recommended, QA only, or no hardening, and waits; an answer in other words is taken as said. Names such as
  Claude Code's simplify are only examples, and a skill of a new kind that checks or improves the change is offered as
  a step of its own. A cleanup's changes are an iteration of their own, reviewed before the code review. A code review runs as before: the commit
  suggestion, the range from the pipeline's first commit and the review skills listed with no recommendation. QA
  starts once the fixes taken from the code review are built. The agent lists the QA skills the session has the same
  way, counting any skill that checks the running software or tells how to start it and sign in, whatever its
  description says, with its own QA as one more pick after them, and alone when there is none. Its own QA is built
  from the whole change since the pipeline's first commit, every place that shows it, the way its users reach it,
  with a report of what was checked and what was not. After QA's fixes are built, the checks they touch run again.
- The findings of the code review and of QA go through the mini grill, in `skills/workshop-forge/SKILL.md`. The agent
  checks each one in the code, and a QA finding in the running software too, before the developer sees it. A finding
  that does not hold is shown with what the code says and asks nothing; each one that holds is a decision of its own
  with a recommendation, and each fix taken is an iteration. Findings about code the pipeline did not change are
  shown apart, marked as not related, with one question for the group: fix the ones named, postpone them, or leave
  them as they are; the code review's and QA's each get their own question.
- After an iteration whose change is significant, when checking it in the running software would show what the tests
  cannot, such as a page as its users see it, the iteration's report says plainly that the agent suggests a small QA
  and what it would check, on its own line right before the question to continue, in
  `skills/workshop-forge/SKILL.md`. When the developer's reply asks for it, the iteration just finished goes on with
  the QA and the fixes for what it finds, and reports again; the next iteration does not start. A plain "continue"
  runs the planned iteration.
- The record's format names the hardening phase in its State and lists QA findings not fixed next to the code
  review's in Known issues (`skills/workshop-craft/formats/record.md`); the README says that a pipeline ends with the
  hardening phase and its four picks, and that a step with a significant change may get a small QA suggested.
- Nine workshop-forge eval cases on the hardening phase and the QA suggestion, in `evals/workshop-forge/`: the end of
  a pipeline, which must offer the three picks and wait; the code review step after the pick of code review then QA,
  which must still suggest the commit, give the range and list the review skills with no recommendation; a task whose
  developer asked for the code review alone, which must end without QA; QA next after the code review's fixes, in a session
  with two QA skills, one of them the repository's own skill on starting the app and signing in, whose description
  does not say QA, where both must be listed with the agent's own QA after them; QA only picked in a session with no
  QA skill, where the agent's own QA must be offered, not run; the agent's own QA run on an app the run can start,
  whose monthly page links to its JSON without the region asked for; a code review's findings, one wrong and two
  about code the pipeline did not change; and an iteration that makes the monthly page's JSON link keep the region,
  whose report must suggest a small QA and leave it for the developer to ask for. The case on a pure move also checks
  that its report suggests none, and one more case lists a cleanup skill under another name than simplify, which the
  offer must recommend before the code review. Each new case fails at least one check with the text before this task
  and passes every check with the new text, two runs each; the cases that reach a changed rule score 127 of 128
  checks with the new text against 123 with the old.
- The workshop-forge eval repo can now run as an app: a fixture whose `serve.py` serves the monthly page, its JSON and
  the admin sales list on a free local port after a sign-in, and logs each request, which the grader reads to see
  what a QA run checked (`evals/workshop-forge/fixtures/make_fixture.sh`).

## Build decisions
- The eval case on the code review step after the pick is held to scoring no lower with the new text, not to failing
  with the text before this task.
  Why: that step does not change, so its checks pass with either text, and no other case checks it.
  Rules out: dropping the case; sharpening it until the old text fails it.
- The eval cases on the QA skills list and on the agent's own QA run fail with the text before this task in at least
  one of their runs, not in each.
  Why: an agent with the old text sometimes lists QA skills like review skills and checks every place in a small app
  on its own; the new text has to do both every time.
  Rules out: harder fixtures made only so the old text fails.
- The agent's own QA is one more pick after the QA skills the session lists, and the only one when there is none.
  Why: the developer wants the choice even where a project has its own QA skill.
  Rules out: the agent's own QA held back while a QA skill exists.
- QA's findings about code the pipeline did not change get a group question of their own, built like the code
  review's.
  Why: QA meets old bugs too, and the developer answers each source's older findings once.
  Rules out: one group for the older findings of both; QA's older findings put one by one.
- The hardening offer is built from the kinds of skills the session lists, not from their names, with a cleanup
  such as Claude Code's simplify recommended before the code review and QA.
  Why: skills are added and renamed, and a rule stuck on today's names would miss a new one.
  Rules out: skill names in the rule; a cleanup applied with no stop before the code review.
- Three picks in the hardening offer: every kind the session has, recommended; QA only; or no hardening.
  Why: the other combinations are rarely wanted, and an answer in other words still gets them.
  Rules out: every combination of kinds as a pick of its own.
- With no QA skill in the session and no way the agent can see to start the software, such as an app that lives
  outside the repository, the agent may leave QA out of the recommended pick and say why.
  Why: a QA that can only call the code the way the tests do shows nothing the tests do not.
  Rules out: QA always in the recommended pick, with the agent asking how to start the software.

## Tried and dropped
- Every workshop-forge case run old text against new. Dropped because: the new text changed the end of the pipeline
  and the report after an iteration, and a case that stops before any report reads the same rules as before; a few
  report cases stand for the others.
- The agent's own QA offered only when the session lists no QA skill. Dropped because: the developer wants it
  offered next to the QA skills too.
- A question when a pipeline that changes what users see starts, asked before any code of its first iteration, on
  whether and how the running software is checked after each iteration, with the answer kept in the pipeline's plan
  and the check run after every iteration. Dropped because: a question at every pipeline's start and a check after
  every iteration cost more than they bring; a small QA suggested after a significant iteration keeps the gain.
- Four picks in the hardening offer: code review then QA, code review only, QA only, or no hardening. Dropped
  because: with a cleanup added the list would grow with every kind; three picks cover what is wanted.

## Known issues
- No hardening ran on this pipeline's own change, by the developer's choice: no cleanup, no code review and no QA.
- The new end of the pipeline never ran in a real session with the plugin loaded: the eval runs read the skill files
  directly and leave out the Skill tool and the hooks.
- Unchecked in Codex: whether its session lists the developer's own skills next to the repository's, which decides
  whether a QA skill of the developer's own is offered there.
