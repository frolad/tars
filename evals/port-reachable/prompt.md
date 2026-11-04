---
description: "Multi-part question: both parts, in order, no tooling suggestions."
tags: [sttp]
max_turns: 3
timeout_seconds: 120
---

Which port does the API listen on, and is it reachable from outside?

docker-compose.yml:
```yaml
services:
  api:
    image: acme/api:1.4
    ports:
      - "8080:8080"
```

Security group inbound rules on the host:
```
22   tcp  0.0.0.0/0
443  tcp  0.0.0.0/0
```
