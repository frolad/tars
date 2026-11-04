---
type: llm
---

Judge only the final message, the assistant's next message to the user.
Pass if all hold:
1. Each problem is named by its subject in plain words: the orders with an invalid or zero date, and the orders changed while the copy runs. A plan label (P2, P3, EC-a, EC-b) may appear only next to what it means; "EC-a fails by 3" with nothing more fails.
2. Each problem comes with its concrete failure: 3 orders whose `created_at` of 0000-00-00 Postgres rejects, so they would be missing; orders changed during the roughly 2-hour copy would land in Postgres with their old data.
3. Each decision put to the user has options and a recommendation.
4. The plan's terms (backfill, dual-write, exit criteria) are said in plain words or explained where used: "copying the existing orders", "writing every change to both databases".
5. No preamble, flattery, hedging filler, recap, or generic closing offer.
Otherwise fail.
