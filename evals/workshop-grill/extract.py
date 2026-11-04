"""extract.py <run-dir> <transcript.jsonl>: write outputs/commands.txt, events.json and metrics.json for one run."""
import json, sys
from pathlib import Path

run, transcript = Path(sys.argv[1]), Path(sys.argv[2])
repo = str(run / "repo")
calls, results, order, tools = {}, {}, [], {}
for raw in open(transcript):
    try:
        ev = json.loads(raw)
    except json.JSONDecodeError:
        continue
    msg = ev.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, list):
        continue
    for c in content:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "tool_use":
            calls[c["id"]] = c
            order.append(c["id"])
            tools[c["name"]] = tools.get(c["name"], 0) + 1
        elif c.get("type") == "tool_result":
            body = c.get("content")
            if isinstance(body, list):
                body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
            results[c.get("tool_use_id")] = str(body or "")
events, lines = [], []
for i in order:
    c, inp = calls[i], calls[i].get("input") or {}
    res = results.get(i, "").replace(repo, "<repo>")
    if c["name"] == "Bash":
        cmd = inp.get("command", "").replace(repo, "<repo>")
        events.append({"kind": "bash", "command": cmd, "result": res[-1500:]})
        lines.append("$ " + cmd + "\n  -> " + res[-300:].replace("\n", "\n     "))
    elif c["name"] in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path", "").replace(repo, "<repo>")
        events.append({"kind": "edit", "path": path})
        lines.append(f"[{c['name']}] {path}")
    elif c["name"] == "Read":
        lines.append(f"[Read] {inp.get('file_path', '').replace(repo, '<repo>')}")
(run / "outputs" / "commands.txt").write_text("\n".join(lines) + "\n")
json.dump(events, open(run / "events.json", "w"), indent=1)
json.dump({"tool_calls": tools, "total_tool_calls": sum(tools.values())}, open(run / "metrics.json", "w"), indent=2)
