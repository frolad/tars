---
description: "Decisions mid-way through a plan with its own labels: each problem in plain words, with what goes wrong."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

The conversation so far:

[user] Move the `orders` table from MySQL to Postgres. Go step by step and ask me at each decision.

[assistant] Plan in four phases: P1 schema, P2 backfill, P3 dual-write, P4 read cutover. Exit criteria for each phase: EC-a row counts match, EC-b checksums match, EC-c no write errors for 24 h.

P1: `status` is a MySQL ENUM. Map it to a Postgres enum type, or to text with a CHECK? Recommended: text with a CHECK, so adding a status later is one line.

[user] text with check

[assistant] P1 done: `migrations/001_orders.sql`. P2: backfill in one pass with the app down (about 40 min for 12M rows), or in batches while it runs? Recommended: batches, no downtime.

[user] batches

[assistant, after a dry run of the batched backfill on staging. Its notes, not shown to the user yet:]
- 1,200 batches of 10k rows, 2 h 10 min.
- 3 rows fail: `created_at` = '0000-00-00 00:00:00', which Postgres rejects. EC-a fails by 3.
- Rows updated during the backfill are copied in their old state, since P3 is not on yet. EC-b fails for every order changed in those 2 h 10 min.

Write the assistant's next message to the user.
