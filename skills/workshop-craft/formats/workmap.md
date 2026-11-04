# 03-workmap.md

The pipelines, what each does, what each waits for, and the order. Only with more than one pipeline. The agent
proposes it; the user corrects and confirms it.

```
# Work map: <task>

## Pipelines

1. Pipeline 1: <name> (pipelines/01-<name>/)
   <a few sentences on what it does>
   Waits for: nothing.
2. Pipeline 2: <name> (pipelines/02-<name>/)
   <a few sentences>
   Waits for: pipeline 1, <Category>, iteration 1.1 (release point).
   Hands over: <what pipeline 2 receives when that iteration is done>.
3. Pipeline 3: <name> (pipelines/03-<name>/)
   <a few sentences>
   Waits for: pipeline 1 to finish.

## Order (derived from the waits above)

Wave 1: pipeline 1.
Wave 2: pipeline 2, once pipeline 1, <Category>, iteration 1.1 is done; pipeline 3, once pipeline 1 is finished.
Critical path: <the chain that sets the end date>.
```

- Waits for is either a whole pipeline or one iteration of another pipeline. The second is a release point: one
  pipeline releases another while it is still running.
- Each release point has a Hands over line.
- The work map owns the waits. The releasing pipeline's `iterations.md` repeats the edge in its header
  (`Releases:`), so finishing that iteration tells the user which pipeline can start.
- When a release-point iteration splits or is dropped, the edge is updated in the same turn.
- A wave is a set of pipelines that can run at the same time. Waves and the critical path are derived from the
  waits, rewritten whenever a wait changes, and never edited by hand.
- Structural changes are logged in the scope's Changes, not here.
