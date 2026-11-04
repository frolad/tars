---
type: regex
pattern: '(?:\S+\s+){120}'
match: not_contains
---

Fails when the response has 120 or more whitespace-separated tokens. Code blocks count. Calibrated at roughly twice the length of an STTP answer on Opus 5, so it separates STTP from default verbosity rather than enforcing the ideal.
