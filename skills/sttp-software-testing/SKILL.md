---
name: sttp-software-testing
description: Straight To The Point testing, built on test-driven development. Applies whenever tests are written, changed or judged, in chat or in files - a bug fix, new behaviour, a new write path, a flaky run, proving that a test catches a bug. Red first, then only enough code to go green, tests at the interface callers use, fakes only at system boundaries. Loaded automatically with sttp-software-coding before the first edit in a session; load it yourself when tests come up without an edit, or when the user says "sttp testing".
---

sttp and sttp-software-coding apply. This skill decides which tests to write, when, in what order and at which seam, and how to read a test run. Running the checks and reporting them stays with sttp-software-coding. Inside workshop-forge, workshop-forge sets the process; this skill governs the tests written.

Repo instructions and the existing test conventions win over these rules.

## When the test comes first

- A repo with tests, and a bug fix or new behaviour at a seam: red first.
- A repo with tests, and a change no test observes (copy text, styling, a config value): no new test.
- A repo without tests: one runnable check, only for money, security or parsing logic, written red first. No test framework unless the user asks.
- A throwaway script: no test.

## Seams

A seam is where a test observes behaviour: the module's interface, the one its callers use. Test there, not past it; wanting to test past it means the module has the wrong shape.

- A test already crosses the interface the change touches: name the seam in one line and go on.
- No test crosses it yet, or the test needs a new fake: ask before writing the test. Where the tests observe the code is the user's decision. Under workshop-forge, the question belongs in step 2 of the mini grill.

The dependency decides how a test crosses the seam:

- in-process code: test it directly;
- a local stand-in exists (an in-memory database, a temp directory): run the test with it;
- your own remote service: an in-memory adapter behind a port;
- a third-party service: a mock adapter behind a port.

Test names use the project's own terms: its glossary, ADRs or docs, and under workshop-forge the blueprint's knowledge files.

## The loop

1. Write one test for one behaviour. Run it and see it fail.
2. Red means the test ran and failed on an assertion about the missing behaviour. An import error, a setup error, or a test that passes at once is not red: fix the test, or report it up front. A test never seen failing proves nothing.
3. Write only enough code to make it pass. No speculative code, no tests for later.
4. Run it green, then start the next slice.

- One vertical slice at a time: one test, one minimal implementation. All the tests first would fix a shape before the code has taught anything.
- Each item of sttp-software-coding's "Never cut" (validation at trust boundaries, error handling that prevents data loss, security) is its own slice with its own red test, so "only enough code" never drops it. What no test in the repo can observe, such as some accessibility basics, is built anyway and named untested in the report.
- An iteration holds one or more slices. The stop comes after the iteration, not after each slice.

## Refactoring

Refactoring is its own stage, never part of red to green: mixed with new behaviour, a reviewer cannot tell a moved line from a changed one. Ask first and do it as its own iteration, as sttp-software-coding says. Through a refactor the test assertions do not change and the tests stay green; imports and calls re-pointed by a rename or a move are part of the refactor.

## Good tests

- They check behaviour through the public interface and survive an internal refactor. A test that must change when the implementation changes is testing past the interface.
- Mock only at system boundaries: external APIs, time, randomness, sometimes the database or the file system. Your own modules, private methods and internal collaborators are tested for real, and a result is read through the interface, not through a side channel such as a direct query.
- The expected value comes from an independent source: a known literal, a worked example, the spec. A value computed the way the code computes it passes by construction.
- One logical assertion per test. The name says what the caller gets, not how.

Examples of good and bad tests: `tests.md`. When and how to mock: `mocking.md`.

## Write paths

- The first slice writes the data and reads it back through the code that reads it in this codebase.
- Nothing here reads it yet: read at the storage boundary, with a comment naming the real reader, and mark that reader unverified in the report. When the reader lands, its iteration moves the test onto it.
- Each refusal case that applies is its own slice: bad input, no access, an object that belongs to someone else.

## Fakes, stand-ins, test infrastructure

- What the repo's tests already use comes first: their fakes, test database, helpers.
- Anything new (a fake, a stand-in, a test dependency, a runner): ask first, like a new seam. Once agreed, it goes in with the first slice that needs it, and later slices extend it.
- A port with a test adapter only for your own remote service or a third-party service, where no local stand-in can run in the tests. In-process code and code with a local stand-in get no port. A new port is a new seam: ask first.

## Proving a test without a red step

For a test added to code that already works, an existing test the user wants proven, or a test written after the fix: edit the code to the broken behaviour, run the test, see it fail, and edit the code back. Undo by editing only. `git stash`, `git checkout` and `git restore` touch the user's uncommitted work and what the user has staged. The report names the test that failed.

A bug that already existed, found this way, stays out of the current change: list it with a one-line cost. It becomes its own iteration: a red test that reproduces it, then the fix.

## Reading a test run

- A deadlock or timeout in a parallel test run counts as a flake only after rerunning that package or file alone.
- Old tests made redundant by new tests at a deeper interface: list them, each with a one-line reason, and propose deleting them as a cleanup iteration. The current change leaves them in place.

## Report

Inside sttp-software-coding's report:

- What was run: the new test that went red and what it failed with. Under workshop-forge it is the report's only line about tests.
- A red step that did not go red: up front, as a failed check.
- A behaviour the change touches that no test covers: a skipped item, with when to add it.
