# Glossary bootstrap

Current: Catalog, group 1: proposed, waiting on the user for entries 1 to 7, Q3 and Q4.

## Plan

Scope: the whole project: Catalog, Members, Loans. Confirmed by the user on 2026-10-01.
Size: small, mined inline.
Glossary: docs/GLOSSARY.md, new. ADRs: docs/adrs/, new.

## Areas

1. Catalog (catalog/, templates/catalog/): group 1 proposed.
2. Members (members/, templates/members/): not mined.
3. Loans (loans/, templates/loans/): not mined.

## Proposed

Catalog, group 1 of 1: seven terms for `docs/GLOSSARY.md`, which is created with the first entry you approve.

1. **Tool**: anything the library lends, such as a drill, a ladder or a tile cutter.
   _Avoid_: item, equipment
   _In the code_: Item
2. **Category**: the group a tool is listed under when members browse, such as Garden or Woodwork.
3. **Condition**: how worn a tool is: Good, Fair or Worn.
4. **Deposit**: the money a member leaves when picking up a tool, paid back when the tool comes back undamaged.
5. **Power tool**: a tool that runs on mains or a battery; only members who have had the induction may borrow one.
6. **Kit**: a set of tools lent together, such as a tiling kit; every tool of the kit goes out and comes back together.
7. **Retired tool**: a tool taken out of lending for good; it stays on record with its loans.
   _Avoid_: removed tool, deleted tool

**Q3 - Tool or item**: every page says "tool" (Browse tools, Add a tool, Retire tool); the code calls it `Item` (catalog/models.py:19). Options: 1) Tool, with `_In the code_: Item`, as entry 1 shows; 2) Item.

Recommended: 1, the word members and volunteers see.

---

**Q4 - Why tools are retired, never deleted**: "Retire tool" only marks the tool (catalog/store.py:13), and nothing in the app deletes one. The commit that replaced deleting with retiring, on 2025-03-14, says why: "The insurer asks for the loan history of every tool for six years, and a deleted tool takes its loans with it." As an ADR, `docs/adrs/catalog-tools-retired-not-deleted.md`:

```
# Tools are retired, never deleted

Why: the insurer asks for the loan history of every tool for six years, and deleting a tool would take its loans with it.
Rules out: deleting a tool, or its loans, from the app.
Known cost: retired tools stay in the data, and every list of tools has to leave them out.
Decided by the team on 2025-03-14.
Confirmed by the user on 2026-10-01.
```

Options: 1) write it as shown; 2) the reason is different: tell me which; 3) nobody knows the reason any more: drop it.

Recommended: 1, if the insurer's rule still holds.
