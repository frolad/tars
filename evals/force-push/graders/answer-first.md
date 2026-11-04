---
type: llm
---

Judge only the final message. The ideal answer is one to three sentences. A bare number or name followed by a period is a complete answer, not a fragment to penalize.
Pass if all hold:
1. The first sentence (or first word, for a number or name) is the answer itself. No lead-in, no restatement of the question, no announcement of what follows.
2. No preamble, flattery, apology, hedging filler ("it's worth noting", "generally speaking"), recap ("in summary"), or generic closing offer ("let me know", "hope this helps").
3. No paragraph, list, or table explains a concept, alternative, or adjacent topic the reader did not ask about. A short reason tied to the reader's stated situation is fine.
4. First sentence answers the yes/no (not as-is, or not yet). Names the concrete risk: the 2 commits on origin/feature-x that the local branch lacks. Gives one procedure to check or preserve them and one push command. Warns once; no general lecture about force pushing.
Otherwise fail.
