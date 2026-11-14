# pipelines/<n>-<name>/iterations.md

The state of one pipeline. Not every iteration can be listed at the start: iterations split once work on them
starts, and some produce more iterations. The Current line is the way back in after a compaction.

```
# Pipeline 1: <name>

Goal: <what this pipeline achieves>
Done when: scope 2, 3.
Iteration size: <in words>. Suggested by workshop-craft, confirmed by the user on <date>.
Releases: pipeline 2, when <Category>, iteration 1.1 is done.
Base: <commit>, HEAD when the first iteration started.

## Current

<Category>, iteration 1.2: <state, and what it waits for, if anything>.

## Status

| Category         | #   | Title           | Status   |
|------------------|-----|-----------------|----------|
| <Category>       | 1.1 | <a few words>   | DONE     |
| <Category>       | 1.2 | <a few words>   | CURRENT  |
| <Next category>  | 2.1 | <a few words>   | PLANNED  |
| <Next category>  | 2.2 | <a few words>   | BLOCKED  |
| <Next category>  | 2.3 | <a few words>   | WONT-DO  |

## Blockers

- Blocker 1, blocks <Next category>, iteration 2.2: <question>. Open.

## Not yet clear

- <work that cannot be stated sharply yet>

## Iterations

### <Category>
- Iteration 1.1: <behaviour in one line> (<main file>).
- Iteration 1.2: <behaviour>.

### <Next category>
- Iteration 2.1: <behaviour>.
- Iteration 2.2, spawned by iteration 1.2: <behaviour>.
- Iteration 2.3: <behaviour>. Won't do: <reason>. Decided by the user on <date>.
```

- Header: the goal; Done when, pointing to the scope's numbers (in a pipeline workshop-forge started without a scope,
  checkable lines instead); the iteration size; `Releases:` only when this pipeline releases another; `Base:`
  only for code, written by workshop-forge when the first iteration starts, so the review at the end covers every commit
  made since. `Record: off`, in a pipeline without a scope when the developer turns the record off (`layout.md`), is a
  paragraph of its own after the header lines, with a blank line before it.
- Status: one row per iteration, in the order of the lines below, with its category, its number, a title of a few
  words and its status. The status lives in this table only; a row changes in the turn its status does. A pipeline
  without categories keeps the Category column and leaves its cells empty.
- Blockers: each names the iteration it blocks, whose status is BLOCKED while it is open. A resolved blocker becomes
  a fact or decision in the pipeline's `knowledge.md` and is deleted here, and the iteration goes back to PLANNED or
  CURRENT. The section appears only while a blocker is open.
- Not yet clear: work workshop-craft could not state sharply. workshop-forge turns it into iterations when it gets there.
- Iterations are grouped under category headings in planned order. A pipeline without categories lists its
  iterations directly.
- Iterations are numbered within their category, after the category's number: 1.1, 1.2, then 2.1 in the second
  category. Categories are numbered in planned order; the number shows only in the iteration numbers, not in the
  heading or the Category column. A pipeline without categories numbers its iterations 1, 2, 3. A category found
  while working, and each category a split one is replaced by, takes the next free category number and is placed
  where it runs.
- An iteration added after the plan was written goes where it runs, row and line, under a name that reads in order
  there, and a name is never reused or changed. The table then reads top to bottom in the order the work runs, and
  every earlier mention of a name still points at its iteration. Its name, by the first of these that fits:
  - Work that an iteration not DONE needs first splits that iteration. Its row keeps its name, with the status
    SPLIT, and its parts are the rows right under it, lettered in the order they run: 3.1.a, the new work, then
    3.1.b, what 3.1 was planned to do. A part is split the same way: 3.1.b.a, then 3.1.b.b.
  - At the end of its category: the next whole number, 3.3 after 3.2.
  - Between two rows of its category: the name of the row above it with the next letter, whichever iteration's
    work it fixes. 3.1.a after 3.1, 3.1.b after 3.1.a, and 3.1.a.a between 3.1.a and a 3.1.b that exists. Where no
    such name reads in order, between 3.1 and a 3.1.a not DONE, the row below is split.
- Statuses, uppercase, one per row:
  - DONE: built and approved.
  - CURRENT: running now, from its mini grill to its report.
  - NEXT: the one to run next, set between iterations by workshop-forge; CURRENT once its mini grill starts. One row
    at most: when the next iteration changes, the old one goes back to PLANNED.
  - PLANNED: not started; a suggestion, not grilled yet.
  - BLOCKED: an open blocker under Blockers names it.
  - SKIPPED: left for later; it is in `postponed.md`, and its line says so.
  - WONT-DO: dropped for good; its line gives the reason, who decided and when, so it is not proposed again.
  - REVERTED: done, then undone by a cleanup iteration; its line says which one, why, who decided and when.
  - SPLIT: replaced by its parts, the rows right under it; its line names them. It is done when all its parts are,
    so a line that names it, such as `Releases:` or another pipeline's wait, stays as written.
- `split from` marks an iteration that came out of a split; `spawned by` one that came out of another
  iteration's work.
- An iteration's line carries no status: its behaviour, its `split from` or `spawned by`, and the reason of a SKIPPED,
  WONT-DO, REVERTED or SPLIT. A DONE line is one line naming the main file. The diff, the tests and the commit are in
  git.
- Iteration size: workshop-craft suggests it, the user confirms it, and the user can change it at any moment. A change
  is written here and logged in the scope's Changes.
