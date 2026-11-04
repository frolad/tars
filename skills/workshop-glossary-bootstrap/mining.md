# Mining an area

What the run reads in an area, what it looks for, and the shape of the area's result. A subagent that mines one
area reads this file and returns the result; it writes nothing.

## Sources

- The code: the models and the schema, the routes, the labels and headings of the UI, the test names.
- The project's docs: README, CLAUDE.md, AGENTS.md, `docs/`.
- The decision records the project already has.
- Git history, only to find the why of a surprise: the commit that introduced it (`git log -S <name>`, `git blame`)
  and its message.
- Not the issue tracker, and not agent memories: they hold much noise, and memories are per machine.
- Outside software, the project's own files.

## What to look for

- **A term**: a thing the area's work is about, specific to the project, that its code, its UI or its docs name.
  Not the general words of the trade, such as user, page or request. Say what it is for a person who knows the
  domain, not how the code does it, and note every name it goes by: what the users see and what the code says, with
  a source for each.
- **A collision**: one thing named differently in two sources, such as `Customer` in the code and "client" on
  every page, or one name used for two things. The user picks the word, so a collision is recorded, not settled.
- **A surprise**: code that looks like a deliberate decision with no explanation in the code, the docs or the
  decision records, and that already looks like it passes workshop-glossary's three ADR tests: hard to reverse,
  surprising without its context, the result of a real trade-off. Look for its why in git. Most oddities are not
  surprises: a style choice, a leftover, a bug. Leave those out. A deliberate oddity with no ADR is what a later
  agent "fixes", and with no filter every oddity becomes a question.
- **A contradicted entry**: an entry of the existing glossary, or a decision record, that the code contradicts. It
  becomes a proposed change.
- What the glossary already has, and the code does not contradict, is not mined again.

## The result

One section per area, under the working file's Candidates. A subagent returns exactly this section.

```
### <Area>

Terms:
- <Term, as the users see it>: <what it is, in one or two sentences>.
  Users see: "<word>" (<source>). In the code: `<Name>` (<file:line>).

Collisions:
- <the thing>: "<word>" in <source>, `<Name>` in <source>.

Surprises:
- <what the code does> (<file:line>). Looks deliberate because <reason>.
  Git: <commit date and message> | nothing found.

Changes:
- <existing entry>: says "<its text>"; the code <what it does instead> (<source>).
```

- `In the code` only when the code's name differs from what the users see. It names a thing, such as a class or a
  table. A thing the code only marks with a flag or a field, such as `is_staff` on an account, has no name in the
  code and gets no `In the code`.
- A heading with nothing under it is left out.
