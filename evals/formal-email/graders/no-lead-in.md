---
type: regex
pattern: '^\W*(Here''s|Here is|Below is|Sure|Certainly|I''ve (drafted|written)|This email)'
flags: i
match: not_contains
---

Output starts with the email (Subject line or greeting), not a sentence about the email.
