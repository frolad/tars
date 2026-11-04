---
description: "Wrong premise: one-line correction, then the fix."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

This test fails:

```python
def test_total():
    assert total([0.1, 0.2]) == 0.3
```

Output: `assert 0.30000000000000004 == 0.3`

`total` is a plain wrapper around `sum`. So pytest is broken, right?
