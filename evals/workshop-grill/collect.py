"""collect.py <run-dir> <transcript.jsonl> <total_tokens> <duration_ms>: save one finished run for grade.py.

Writes outputs/final.md (the agent's reply: its SubagentHandback message, else its last text), then runs
extract.py (outputs/commands.txt, events.json, metrics.json) and writes timing.json.
"""
import json, subprocess, sys
from pathlib import Path

run, transcript, tokens, ms = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
reply = None
for raw in open(transcript):
    try:
        msg = json.loads(raw).get("message") or {}
    except json.JSONDecodeError:
        continue
    if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
        continue
    for c in msg["content"]:
        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "SubagentHandback":
            reply = c["input"]["message"]
        elif isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
            reply = c["text"]
(run / "outputs").mkdir(parents=True, exist_ok=True)
(run / "outputs" / "final.md").write_text(reply.strip() + "\n")
subprocess.run(["python3", str(Path(__file__).parent / "extract.py"), str(run), str(transcript)], check=True)
json.dump({"total_tokens": tokens, "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1)},
          open(run / "timing.json", "w"), indent=2)
