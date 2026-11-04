---
description: "Items with internal labels: each named by its subject, not by its label alone."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

Review state of RFC-42, "Move session storage from Redis to Postgres":

| Comment | Reviewer | Status | Text |
|---|---|---|---|
| C1 | ana | resolved | Typo in the title. |
| C2 | ben | open | Sessions are read on every request. The RFC gives no numbers for the extra load on the primary database. |
| C3 | ana | resolved | Link the migration ticket. |
| C4 | chen | open | Logout must delete the session row. The RFC only says sessions "expire after 30 days", so a logged-out session stays valid until then. |
| C5 | ben | resolved | Name the table `sessions`. |
| C6 | dev | open | Nit: the diagram colors. |

Can I approve it?
