---
type: llm
---

Judge only the final message. The ideal answer is one to three sentences. A bare number or name followed by a period is a complete answer, not a fragment to penalize.
Pass if all hold:
1. The first sentence (or first word, for a number or name) is the answer itself. No lead-in, no restatement of the question, no announcement of what follows.
2. No preamble, flattery, apology, hedging filler ("it's worth noting", "generally speaking"), recap ("in summary"), or generic closing offer ("let me know", "hope this helps").
3. No paragraph, list, or table explains a concept, alternative, or adjacent topic the reader did not ask about. A short reason tied to the reader's stated situation is fine.
4. 20.11.1 first, optionally why (pinned by .nvmrc, satisfies engines and CI) and the switch command. No explanation of what nvm, .nvmrc, or the engines field are.
Otherwise fail.
