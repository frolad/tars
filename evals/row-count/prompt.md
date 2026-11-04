---
description: "'How many' question: the number first."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

How many rows does this return?

```sql
SELECT id FROM users WHERE plan = 'pro' AND deleted_at IS NULL;
```

users:

| id | plan | deleted_at |
|----|------|------------|
| 1  | pro  | NULL       |
| 2  | free | NULL       |
| 3  | pro  | 2026-03-02 |
| 4  | pro  | NULL       |
| 5  | free | 2026-01-15 |
| 6  | pro  | NULL       |
