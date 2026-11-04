# docs/adrs/<area>-<decision>.md

One file per decision that outlives a task. Every engineering task reads the ADRs of the area it works in.

```
# <the decision, as one sentence>

Why: <reason>.
Rules out: <what this excludes>.
Known cost: <optional>.
Decided by <who> on <date>.
```

- The fields are those of a decision in a blueprint's knowledge file, with the decision as the title, so a
  decision moves from the blueprint with nothing rewritten. A question number after it, as in "Decided by the user
  on 2026-10-07 (Q28).", stays behind: it means something only in the chat it was asked in.
- The file name is the area the decision applies to, then the decision, in lowercase with hyphens, and no number:
  `billing-invoice-numbering.md`. An agent finds the ADRs of an area by listing the folder, so the area comes
  first. Numbers collide when parallel branches add ADRs.
- No mechanics: constants, function names, file paths. They tie later work to one implementation.

An example:

```
# Invoice numbers are assigned when an invoice is sent, not when it is drafted

Why: invoice numbers must have no gaps, and drafts get deleted, so numbering drafts leaves gaps.
Rules out: a number on a draft; numbering in the draft editor.
Known cost: support cannot refer to a draft by number; they use the customer and the date.
Decided by the user on 2026-10-01.
```

Not in it: "numbers come from the `invoice_seq` sequence in `billing/send.py:assign_number()`".
