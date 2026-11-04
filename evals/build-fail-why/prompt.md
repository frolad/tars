---
description: "'Why' question with a log: the cause, then the fix, no generic cause list."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

Why does my build fail?

```
$ npx tsc -p .
src/app.ts:3:20 - error TS2307: Cannot find module './config' or its corresponding type declarations.

3 import { config } from './config';
                       ~~~~~~~~~~

$ find src -name 'config*'
src/lib/config.ts
```
