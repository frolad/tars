# Glossary bootstrap

Current: Catalog, group 1: proposed, waiting on the user for entries 1 to 5, Q3 and Q4.

## Plan

Scope: the whole project: Catalog, Members, Loans. Confirmed by the user on 2026-10-01.
Size: small, mined inline.
Glossary: CONTEXT.md, existing, in its own format. ADRs: docs/adrs/, new.

## Areas

1. Catalog (catalog/, templates/catalog/): group 1 proposed.
2. Members (members/, templates/members/): not mined.
3. Loans (loans/, templates/loans/): not mined.

## Proposed

Catalog, group 1 of 1: four new terms and one change, for `CONTEXT.md`, in its format. Its Tool and Deposit stand.

1. New:
   **Category**:
   The group a tool is listed under when members browse, such as Garden or Woodwork.
2. New:
   **Power tool**:
   A tool that runs on mains or a battery; only members who have had the induction may borrow one.
3. New:
   **Kit**:
   A set of tools lent together, such as a tiling kit; every tool of the kit goes out and comes back together.
4. New:
   **Retired tool**:
   A tool taken out of lending for good; it stays on record with its loans.
   _Avoid_: removed tool, deleted tool
5. Change: the code and the Add a tool form have three grades, Good, Fair and Worn (catalog/models.py:3).
   **Condition**:
   How worn a tool is: Good, Fair or Worn.
   It replaces "How worn a tool is: Good or Worn."

**Q3 - Tool in the code**: the code calls a tool `Item` (catalog/models.py:19), which CONTEXT.md's Tool does not say. Options: 1) add `_In the code_: Item` under Tool's `_Avoid_` line; 2) leave Tool as it is.

Recommended: 1: an agent reading CONTEXT.md cannot tell otherwise that `Item` is the tool.

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
