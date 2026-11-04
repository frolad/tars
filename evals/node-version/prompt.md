---
description: "'Which instance' question: name it, do not explain the concept."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

Which Node version should I use for this project?

.nvmrc:
```
20.11.1
```

package.json:
```json
{
  "engines": { "node": ">=20 <21" }
}
```

CI runs on the node:20-alpine image.
