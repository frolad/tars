---
type: regex
pattern: '^\W*(Sure|Great question|Good question|Certainly|Absolutely|Of course|Let me|I''d be happy|Happy to|Thanks for|Thank you for|That''s a (great|good))'
flags: i
match: not_contains
---

The response must not open with a lead-in. Anchored to the start of the final message.
