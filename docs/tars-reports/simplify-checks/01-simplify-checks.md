# TARS Blueprint Record: simplify's checks in the coding rules: simplify-checks

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
Claude Code's bundled `/simplify` skill reviews a finished diff for reuse, simpler code, wasted work and fixes at
the right depth, then applies its fixes. TARS's coding rules already asked for reuse, for removing what a change
orphaned and for fixing a bug at its cause, but for nothing about state that can be derived, copy-paste with a small
change, deep nesting or wasted work. This pipeline adds those checks to the coding rules, in TARS's own words, so the
agent writes code that way from the start in Claude Code and Codex, and adds a coding eval case that shows the
difference.

## Planning decisions
- simplify's checks become rules the agent follows while it writes, in the Write list of `sttp-software-coding`; no
  skill runs on a finished diff, in either tool.
  Why: what TARS lacked is simplify's checks, not another skill, and Codex was not to get a cleanup skill.
  Rules out: a TARS cleanup skill; a reread of the diff before the report; only pointing to `/simplify`.
  Known cost: no second look at a finished diff by agents that did not write it, and nothing catches a helper
  written twice in two iterations of a pipeline.
- No text of simplify goes into the repository; README's Credits names it as the source of the ideas, with no text
  adapted.
  Why: Claude Code is "All rights reserved", and TARS is MIT.
  Rules out: copying simplify's text, or Anthropic's Apache 2.0 code-simplifier agent, which rewrites code on its
  own after every edit and carries one company's JavaScript conventions.
- Every missing check goes in: simpler code (no state that can be derived, copy-paste with a small change made into
  one, deep nesting flattened), no wasted work (no repeated computation or I/O, independent steps not run one after
  another, nothing slow added to startup or a hot path), and no long-lived closure that keeps a large scope alive.
  Why: these are the parts of simplify nothing in TARS asked for.
  Rules out: a rule to rework a shared mechanism instead of adding a special case to it; TARS raises that as a
  question, since a change to a shared mechanism is a design decision the user takes.
- The new rules are checked by a seventh coding eval case whose obvious first draft wastes work, failing with the
  old rules and passing with the new, and by the old and the new rules on all seven cases.
  Why: the only way to see the rules change what the agent writes, and that the other cases got no worse.
  Rules out: running the existing cases only; adding the rules on reading alone.

## Not in this task
- A review skill for finished diffs, in either tool. Why: the checks are wanted as rules followed while writing.
- Any copy of simplify's text, or of the code-simplifier agent. Why: Claude Code's license allows no copy into an
  MIT repository, and code-simplifier rewrites code on its own after every edit.
- How workshop-forge's end of a pipeline runs `/simplify`, which applies its fixes in one go rather than one
  iteration per accepted finding. Why: left as it is; picking it there is the developer's call.
- A rule to rework a shared mechanism instead of adding a special case to it. Why: TARS raises that as a question,
  since a change to a shared mechanism is a design decision the user takes.
- The other work left for later when the repository went public: iterations that add code the end of a pipeline
  removes anyway, iterations split in a way the user does not expect, a loose match in the workshop-craft eval's
  grader, and the order of Codex's install steps in README. Why: each is a task of its own.

## What was built
- A seventh coding eval case, `parallel-fetches`, in `evals/sttp-software-coding/`: the agent adds an async
  dashboard next to a sibling that awaits its two requests one after the other; the checks want the dashboard's two
  independent requests to run at the same time, the card built through the existing helper, the sibling left as it
  is, and a new test.
- The grader's helper that finds the tests of a run also sees `async def` tests.
- Four lines in the Write list of `sttp-software-coding`: no wasted work (nothing computed or fetched twice, no
  query or file read inside a loop, independent steps run together, no slow work on startup or a hot path); no state
  that can be derived, copy-paste with a small change written once, deep nesting turned into early returns; a
  long-lived closure that would keep large values alive replaced by a small class or struct; and a fourth line that
  keeps the three to the code the change writes.
- A line in README's Credits: the three lines take their checks from Claude Code's bundled `simplify` skill, and no
  text is adapted.

## Build decisions
- The wasted-work rule holds where the code next to the change does it the slow way: the new code does not copy that
  shape, and the old code stays as it is, named in one line.
  Why: otherwise the rules to match a sibling's shape and the existing style win, as the eval runs before the change
  showed; the grill would catch it only inside workshop-forge, and only if the agent noticed.
  Rules out: asking before new code differs from its sibling; letting the sibling's shape win.
- The new lines are for the code the change writes, and never on their own a reason to change existing code: where
  meeting one would take that, the report names the cost in one line. Whether existing code is reused or needs a
  refactor first stays with the rules that were there before.
  Why: everywhere else in the rules existing code stays and its problem is named, as for dead code and the slow
  sibling; without this, the wasted-work and copy-paste lines together left a refactor of existing code as the only
  way to add a small write method. The choice between reuse and a refactor was already made right by the older
  rules, so the new lines leave it to them.
  Rules out: counting only waste that grows with the data, an exception shaped by the one failing case; treating
  the refactor question as the right answer for a small write method; ranking reuse as it is above a refactor.
- The eval case for the new rules asks for an async dashboard next to a sibling that awaits its two requests one
  after the other; it wants the new function's two independent requests to run at the same time, the card built
  through the existing helper, and the sibling left as it is.
  Why: agents still write independent awaits in turn by habit, and copying a sibling's shape is what the engineering
  rules ask for; the sibling check guards against rework beyond the request.
  Rules out: a case about one query per row.
- The review at the end of the pipeline covered the skills and the plugin code, and its findings were left unfixed.
  Why: the developer judged them minor; they are under Known issues.
  Rules out: fixing the eval grader; rewording the new lines after the review.

## Tried and dropped
- An eval case whose obvious draft runs a query per order through an existing per-order helper. Dropped because:
  with the old rules the agent already wrote one JOIN and said why, so the case showed no difference.
- A copy-paste line that made merging a copy with existing code a refactor to ask about. Dropped because: with the
  rule against fetching twice, it left the agent no plain way to add a small write method, and it stopped to ask.
- A line telling the agent to reuse existing code as it is, and to rework it only when it could not be reused.
  Dropped because: the agent reused an export by decoding its output instead of asking for the refactor first.

## Traps
- The coding eval runs are subagents of the session; in the default STTP mode the hook sends subagents no rules, so
  a run follows only the rule files its prompt names. In `full` mode the hook's own rules would mix with the
  snapshot's.
- With the rules before this task, the agent sees that two independent awaits could run together and still keeps
  the sibling's one-after-the-other shape, naming the faster way only as skipped: the engineering rule to match a
  sibling's shape and the coding rule to match the existing style win over a waste no rule names.
- The order of the coding rules matters: a new line that ranks reuse above the refactor rule makes the agent find
  odd reuses, such as decoding another function's output, instead of asking for the refactor first.

## Known issues
- With these rules, an agent adding a small method next to one that already loads the data and checks access may
  copy those lines, the access check included, instead of calling that method and reading twice. The report names
  the copy, and the eval case passes it; a later change to the original check misses the copy.
- "Independent steps run together" does not exclude steps that share a database session, connection or
  transaction: one SQLAlchemy `AsyncSession` cannot run two queries at once, and the agent may try.
- The closure line says a closure keeps every variable of its call. Most languages keep only the variables the
  closure uses, and JavaScript also those any other closure of the same call uses; an agent taking the line
  literally may turn a harmless closure into a class.
- The engineering rule to give new code its sibling's helpers and shape, no more complex, still pulls against the
  wasted-work line's clause for a slow sibling; in the eval case the coding rule wins.
- The engineering, testing and workshop-forge evals load the coding rules and have not run with these lines.
