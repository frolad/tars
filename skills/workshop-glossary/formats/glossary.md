# docs/GLOSSARY.md

The project's terms, for the agent and for the people who review it. Every engineering task reads it before
working in an area.

```
# Glossary

## <group, once groups form>

**<Term>**: <what it is, in one or two sentences>.
_Avoid_: <a word not to use for it>, <another>
_In the code_: <the code's name for it, only when it differs>
```

- One entry per term: the term in bold, what it is, and the words to avoid for it, when there are any.
- `_In the code_` gives the code's name for the thing when it differs from the term, such as `Transaction` for
  "sale": the one mapping an agent cannot infer from the prose, and a candidate for a rename. `_Avoid_` lists the
  words not to use in prose; new code follows the names of the code around it.
- Only terms specific to the project, not the general words of the trade.
- What the thing is, for a person who knows the domain: not how the code implements it, no field names, no file
  paths.
- Groups become `##` subheadings once several terms belong together. Before that, there are no headings.
- A blueprint's Terms section uses the same fields, as list entries (`../../workshop-craft/formats/knowledge.md`), so
  a term moves from the blueprint with nothing rewritten.
