---
type: llm
---

Judge only the final message. Pass only if every point holds:
1. The output is the email itself and nothing else: no introductory line before it, no notes or offers after it.
2. It is a formal email: greeting, apology, the outage window (14:10 to 14:50 UTC, 40 minutes), the cause (expired TLS certificate on the API gateway), the fix (renewed, expiry monitoring added), and a sign-off as the Acme Platform Team.
3. It is short: no filler paragraphs about how seriously reliability is taken beyond one sentence.
Fail if any point is violated.
