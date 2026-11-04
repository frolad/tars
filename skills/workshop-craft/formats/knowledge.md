# 00-knowledge.md and pipelines/<n>-<name>/knowledge.md

Mostly for the agent. It holds what the recon found and what the user decided, so it survives a compaction.

```
# Knowledge

## Facts

### <subject in the code>
- <fact>.
  Source: <file:line | document | "user said">, read <date>.
- <fact that was wrong at first>.
  Source: <...>, read <date>.
  Corrected <date>: first assumed <the wrong version>.

## Decisions

- <decision>.
  Why: <reason>.
  Rules out: <what this excludes>.
  Known cost: <optional>.
  Changes the ADR: <optional: the project's ADR this replaces or edits>.
  Decided by <the user> on <date>.

## Terms

- **<Term>**: <what it is, in one or two sentences>.
  _Avoid_: <a word not to use for it>.
  _In the code_: <the code's name for it, only when it differs>.
- **<Term the glossary has>**: <what it means from now on>.
  Changes the glossary: <what the entry says today>.
  Decided by <the user> on <date>.
```

A pipeline's file is titled `# Knowledge: pipeline <n>, <name>`.

- Three kinds of entry: facts, decisions and terms.
- Topic headings name the subject in the code, not the pipeline category; one fact often serves several
  categories.
- A fact carries its source and the date it was read. The date tells when to re-read the code before relying
  on it.
- A wrong fact is fixed in place with a Corrected line that keeps the wrong version visible: those are the
  mistakes an agent repeats.
- A decision carries why, what it rules out, and who decided when. Rules out is what stops a rejected design
  from coming back. A decision that replaces or edits one of the project's ADRs names it in a Changes the ADR
  line.
- A term is a word of the task that a reader could take two ways, or that the code names differently: specific
  to the project or the task, not a general word of the trade. It says what the thing is, not how the code does it.
- `_In the code_` gives the code's name for the thing when it differs from the term, such as `Transaction` for
  "sale": the one mapping an agent cannot infer from the prose. A term that differs from what the project's users
  see, on its pages or in its docs, is the user's choice, not a mapping. `_Avoid_` lists words not to use in
  prose; new code follows the names of the code around it. A rename of the code is a decision of its own, not a
  term.
- The fields are those of a project glossary's entries (`../../workshop-glossary/formats/glossary.md`), so a term
  moves there with nothing rewritten. A term the project's glossary already has appears only when the task changes
  it, with a Changes the glossary line. A wrong term is fixed in place with a Corrected line, like a fact.
- Terms live in `00-knowledge.md`; a pipeline started from a session, without one, keeps them in its own
  `knowledge.md`. When the project has a glossary or ADRs, workshop-glossary's merge at the end of the pipeline that
  built them moves them to the project's glossary, and a decision that passes its three tests to the project's
  ADRs. Otherwise they stay in the blueprint.
- A fact lives at the level that uses it: in the pipeline's `knowledge.md` while one pipeline uses it, moved up
  to `00-knowledge.md` when a second pipeline or the scope needs it. Moved, not copied.
