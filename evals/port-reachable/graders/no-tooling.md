---
type: regex
pattern: '\b(nmap|telnet|netcat|nc -z|curl)\b'
flags: i
match: not_contains
---

Does not redirect the reader to go check with a tool; the facts are in the prompt.
