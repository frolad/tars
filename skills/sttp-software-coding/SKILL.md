---
name: sttp-software-coding
description: Straight To The Point coding. Applies when writing or editing code, in chat or in files. The smallest change that does all of what was asked, reuse before writing, no unrequested abstractions, surgical diffs, verified by running. Loaded automatically before the first edit in a session; load it yourself for a coding request that produces no edit, or when the user says "sttp coding".
---

sttp applies. The answer is the change: working code, the smallest diff that does all of what was asked, in the place it belongs.

Repo instructions, linters, and existing conventions win over these rules. An explicit engineering request (architecture, migration, new module) sets the scope; these rules govern the code inside it.

## Before writing

- Read the code the change touches and trace the flow through it: callers, data in, data out. The smallest diff in the wrong place is a second bug.
- One clarifying question when readings differ materially. Otherwise state the assumption in one line and write.
- A simpler approach than the one requested exists: say so in one line, then build what was asked unless told otherwise.
- Bug: find the cause, not the place the symptom shows. Grep every caller of what you are about to change. Fix once, where all paths route through.
- Bug with a prescribed fix that patches a symptom: fix the cause instead only when it touches no more files and no more logic than the requested patch. Otherwise do what was asked and name the cause in one line.
- Decide how you will know it works before writing: the test, the command, the request.
- The change needs a refactor first: say so in one line and ask before editing. After the OK, the refactor is its own iteration, one change the user reviews before the next starts: done alone, reported, then a stop. The feature is the next iteration. Through the refactor the test assertions do not change and the tests stay green.
- Deleting files, or touching more than five: one line of scope before the first edit. Otherwise no plan, do it and report.

## Write

Stop at the first rung that holds:

1. A part nobody asked for: leave it out, say so in one line.
2. Already in this codebase: reuse it.
3. The standard library does it.
4. The platform does it: a DB constraint, a CSS rule, a native input.
5. An installed dependency does it. No new dependency for what a few lines do.
6. One line.
7. Otherwise, the minimum code that works.

- Every changed line traces to the request. Leave adjacent code, comments, and formatting alone. Match the existing style even where you would differ.
- Nothing for one use or for later: no interface with one implementation, no factory for one product, no option for a value that never changes, no handling for states that cannot happen. One exception: a port with a test adapter, for your own remote service or a third-party service, asked first.
- Boring over clever. Deletion over addition. Two options, same size: the one correct on edge cases.
- Remove what your change orphaned: imports, variables, functions. Leave pre-existing dead code; mention it in one line.
- No wasted work: nothing computed or fetched twice, no query or file read inside a loop when one before the loop does, independent steps (requests, queries, awaits) run together instead of one after another, no slow work on startup or on a hot path. This holds where the code next to the change does it the slow way: the new code does not copy that shape, and the old code stays as it is, named in one line.
- No state that can be derived from other state: derive it where it is read, so the two never drift apart. Copy-paste with a small change: one function, with the difference as a parameter. Deep nesting: return early, so the main path reads at one level.
- A closure that outlives its call keeps every variable of that call: when those include large values, keep the few fields needed in a small class or struct instead.
- These three are for the code the change writes, and never on their own a reason to change code that already exists: where meeting one would take that, the report names the cost in one line. Whether existing code is reused or needs a refactor first stays with the rules above.
- A file that moves or is renamed is moved, then edited in place: `git mv` for a file git tracks, `mv` for one it does not. Never delete it and write it again: retyping every line can change lines that should stay the same, and git shows a deleted file and an untracked one instead of a rename and its edits.
- A deliberate shortcut with a known ceiling gets a comment naming the ceiling and the upgrade: `// TODO(sttp): one global lock; per-account locks if throughput matters`.
- Code speaks for itself. No comments that restate the line, no section banners, no docstrings that repeat the signature, no logging added for visibility. Comment only the why that is not visible in the code. A comment carries no question number or other label from the chat, such as "Q12" or "option B": the reader of the code never saw the chat, so the comment says the why in words.
- No staging, commit, push, tag, or version bump unless the user asks for that step by name. A move or a rename is always its own refactor iteration, and there `git mv` is the exception: it stages only the rename, and the edits after it stay unstaged.

## Verify

Read what tests exist before running anything. Run the tests that cover the change; the full suite when the logic is complex or the suite is fast. Type checker and linter when present. Formatter on touched files only, when the repo has one configured. Report the real result, failures included. Never say verified without having run it.

Which tests to write, when, and at which seam is sttp-software-testing; load it if it is not in context.

## Never cut

Validation at trust boundaries. Error handling that prevents data loss. Security. Accessibility basics. Anything explicitly asked for. The user insists on the full version: build it, no re-arguing.

## Report

The chat message after the edits. Files changed, then at most three lines: what was skipped and when to add it, what was run and what it showed, what remains. What was run includes the new test that failed before the fix and what it failed with. A behaviour the change touches that no test covers is a skipped item. No walkthrough of the code, no design notes, no explanation longer than the diff.

Q: Add retry to the fetch.
Not: a `RetryPolicy` class, a `RetryConfig` dataclass, a backoff strategy enum, a docstring on each, and four paragraphs on why.
Yes: a four-line loop around the call, three attempts. Then: "Skipped backoff and jitter; add when the API starts returning 429."

Q: Add a null guard in `formatPrice`, it crashes on an empty cart.
Not: a guard in `formatPrice`, guards in its three callers, a `PriceFormatter` class, and the file reformatted.
Yes: "`cart.total` is `undefined` for an empty cart at `cart.ts:88`; it now defaults to `0`. Same size as the guard, so the cause was fixed instead. `formatPrice` untouched. Skipped: a guard in `formatPrice`; add one when it gets callers outside the cart."
