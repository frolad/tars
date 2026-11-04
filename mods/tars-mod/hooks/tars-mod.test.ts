import { test, expect } from "claude-code/testing"

// A home folder kept in memory: what the mod writes there, and what it finds. Its files are keyed by "/" paths; on
// Windows the test kit hands the handlers the system's own, "C:\home\u\.tars\mode" for "/home/u/.tars/mode".
const slashed = path => path.replace(/^[A-Za-z]:/, "").replaceAll("\\", "/")
const home = (on, files = {}, { readOnly = false, env = { HOME: "/home/u" } } = {}) => {
  on("env.get", ($, e) => ({ value: env[e.name] }))
  on("session.id", () => ({ value: "s1" }))
  on("fs.exists", ($, e) => ({ value: slashed(e.path) in files }))
  on("fs.read", ($, e) => ({ value: files[slashed(e.path)] }))
  on("fs.write", ($, e) => {
    if (readOnly) throw new Error("read-only")
    files[slashed(e.path)] = e.text
    return { value: undefined }
  })
  return files
}

const run = async ($, command, args = "") => (await $.command.run({ command, args })).text

test("/sttp-mode full writes the mode file and answers with no turn", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-mode", "full")).toBe("STTP mode set to full.")
  expect(files["/home/u/.tars/mode"]).toBe("full\n")
})

test("with no HOME, as in a Windows terminal, the notes go to the profile folder that hooks/sttp.py uses", async ($, on) => {
  const files = home(on, {}, { env: { USERPROFILE: "/profile/u" } })
  await run($, "tars:sttp-mode", "full")
  expect(files["/profile/u/.tars/mode"]).toBe("full\n")
})

test("/sttp-mode alone tells the mode, primary when none is set", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-mode")).toBe("STTP mode: primary.")
  files["/home/u/.tars/mode"] = "full\n"
  expect(await run($, "tars:sttp-mode")).toBe("STTP mode: full.")
})

test("an unknown mode changes nothing", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-mode", "loud")).toBe("Unknown STTP mode 'loud'. Use primary or full.")
  expect(files).toEqual({})
})

test("/workshop-questions writes the question form that hooks/sttp.py reads, dialog when none is set", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:workshop-questions")).toBe("Grill questions: dialog.")
  expect(await run($, "tars:workshop-questions", "transcript")).toBe("Grill questions set to transcript.")
  expect(files["/home/u/.tars/questions"]).toBe("transcript\n")
  expect(await run($, "tars:workshop-questions")).toBe("Grill questions: transcript.")
  expect(await run($, "tars:workshop-questions", "dialog")).toBe("Grill questions set to dialog.")
  expect(files["/home/u/.tars/questions"]).toBe("dialog\n")
})

test("an unknown question form changes nothing", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:workshop-questions", "panel")).toBe("Unknown question form 'panel'. Use dialog or transcript.")
  expect(files).toEqual({})
})

test("/sttp-guards off and on write the session's marker that hooks/sttp.py reads", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-guards", "off")).toBe(
    "TARS guards off for this session: git steps are not checked. /sttp-guards on turns them back on.")
  expect(files["/home/u/.tars/guards-off-s1"]).toBe("off\n")
  expect(await run($, "tars:sttp-guards")).toBe("TARS guards: off for this session; the default is on.")
  expect(await run($, "tars:sttp-guards", "on")).toBe("TARS guards on.")
  expect(await run($, "tars:sttp-guards")).toBe("TARS guards: on for this session; the default is on.")
})

test("/sttp-guards default off and on write the default that hooks/sttp.py reads", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-guards")).toBe("TARS guards: on, the default.")
  expect(await run($, "tars:sttp-guards", "default off")).toBe(
    "TARS guards default: off. Sessions without their own /sttp-guards on|off, open ones too, don't check git " +
      "steps. /sttp-guards default on turns it back on.")
  expect(files["/home/u/.tars/guards-default"]).toBe("off\n")
  expect(await run($, "tars:sttp-guards")).toBe("TARS guards: off, the default.")
  expect(await run($, "tars:sttp-guards", "default")).toBe("TARS guards default: off.")
  expect(await run($, "tars:sttp-guards", "on")).toBe("TARS guards on.")
  expect(await run($, "tars:sttp-guards")).toBe("TARS guards: on for this session; the default is off.")
  expect(await run($, "tars:sttp-guards", "default on")).toBe("TARS guards default: on.")
  expect(files["/home/u/.tars/guards-default"]).toBe("on\n")
})

test("an unknown guards default changes nothing", async ($, on) => {
  const files = home(on)
  expect(await run($, "tars:sttp-guards", "default maybe")).toBe(
    "Unknown argument 'default maybe'. Use /sttp-guards on|off or /sttp-guards default on|off.")
  expect(files).toEqual({})
})

test("other commands run as they would", async ($, on) => {
  home(on)
  on("command.run", () => ({ text: "core answered" }))
  expect(await run($, "compact")).toBe("core answered")
  expect(await run($, "tars:workshop-forge", "exports 1")).toBe("core answered")
})

test("a failed write leaves the command to the skill", async ($, on) => {
  home(on, {}, { readOnly: true })
  on("command.run", () => ({ text: "the skill answered" }))
  expect(await run($, "tars:sttp-mode", "full")).toBe("the skill answered")
})

// The status line: the STTP mode, or the pause, and the pipeline /workshop-forge named in this session, read from its
// status table (hooks/sttp.py notes the pipeline in ~/.tars/forge-<session> and the pause in ~/.tars/paused-<session>).
const PIPELINE = "/p/.blueprints/exports/pipelines/01-csv/iterations.md"
const ITERATIONS = `# Pipeline 1: csv

## Current

CSV, iteration 2.1: running.

## Status

| Category | #   | Title        | Status  |
|----------|-----|--------------|---------|
| Setup    | 1.1 | export route | DONE    |
| CSV      | 2.1 | header row   | CURRENT |
| CSV      | 2.2 | totals       | PLANNED |

## Iterations
`

// What the mod pinned under the prompt, latest last.
const statusLine = on => {
  const shown = []
  on("ui.status", ($, e) => {
    shown.push(e.text)
    return { value: undefined }
  })
  on("turn.complete", () => ({ text: "" }))
  on("tool.call", () => ({ result: {}, text: "done" }))
  return shown
}

const turnEnds = ($, agentId) =>
  $.turn.complete({ answer: "", durationMs: 1, isAborted: false, turnId: "t1", reason: "answer", agentId })

test("the status line shows the STTP mode, or the pause in its place", async ($, on) => {
  const files = home(on)
  const shown = statusLine(on)
  await turnEnds($)
  expect(shown.at(-1)).toBe("primary")
  files["/home/u/.tars/mode"] = "full\n"
  await turnEnds($)
  expect(shown.at(-1)).toBe("full")
  files["/home/u/.tars/paused-s1"] = ""
  await turnEnds($)
  expect(shown.at(-1)).toBe("paused")
})

test("the status line shows the session's pipeline, its CURRENT row else the next, and the count done", async ($, on) => {
  const files = home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  const shown = statusLine(on)
  await turnEnds($)
  expect(shown.at(-1)).toBe("primary · csv → CSV → header row · CURRENT · 1/3")
  files[PIPELINE] = ITERATIONS.replace("| CURRENT |", "| DONE    |")
  await turnEnds($)
  expect(shown.at(-1)).toBe("primary · csv → CSV → totals · PLANNED · 2/3")
  files[PIPELINE] = ITERATIONS.replace("| CURRENT |", "| DONE    |").replace("| PLANNED |", "| WONT-DO |")
  await turnEnds($)
  expect(shown.at(-1)).toBe("primary · csv · DONE · 2/2")
})

test("between iterations, the status line names the NEXT row ahead of an earlier PLANNED one", async ($, on) => {
  const files = home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  const shown = statusLine(on)
  files[PIPELINE] = ITERATIONS.replace("| CURRENT |", "| PLANNED |")
    .replace("| totals       | PLANNED |", "| totals       | NEXT    |")
  await turnEnds($)
  expect(shown.at(-1)).toBe("primary · csv → CSV → totals · NEXT · 1/3")
})

test("the status line follows /sttp-mode and a write under .blueprints/ at once", async ($, on) => {
  const files = home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  const shown = statusLine(on)
  await run($, "tars:sttp-mode", "full")
  expect(shown.at(-1)).toBe("full · csv → CSV → header row · CURRENT · 1/3")
  files[PIPELINE] = ITERATIONS.replace("| CURRENT |", "| DONE    |")
  await $.tool.call({ tool: "Edit", file_path: PIPELINE, old_string: "a", new_string: "b" })
  expect(shown.at(-1)).toBe("full · csv → CSV → totals · PLANNED · 2/3")
})

test("off in /config, the status line is cleared and the commands still answer", { options: { statusLine: false } },
  async ($, on) => {
    const files = home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
    const shown = statusLine(on)
    await turnEnds($)
    expect(shown).toEqual([undefined])
    expect(await run($, "tars:sttp-mode", "full")).toBe("STTP mode set to full.")
    expect(files["/home/u/.tars/mode"]).toBe("full\n")
    await $.tool.call({ tool: "Edit", file_path: PIPELINE, old_string: "a", new_string: "b" })
    expect(shown).toEqual([undefined, undefined, undefined])
  })

test("a subagent's turn leaves the status line alone", async ($, on) => {
  home(on)
  const shown = statusLine(on)
  await turnEnds($, "agent-1")
  expect(shown).toEqual([])
})

test("a subagent's tool calls and answer pass through unchanged", async ($, on) => {
  home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  const shown = [], calls = []
  on("ui.status", ($, e) => (shown.push(e.text), { value: undefined }))
  on("tool.call", ($, e) => (calls.push(e), { result: { ok: true }, text: "core ran it" }))
  on("turn.complete", () => ({ text: "the subagent's answer" }))
  const call = { tool: "Edit", file_path: PIPELINE, old_string: "a", new_string: "b", agentId: "agent-1" }
  expect(await $.tool.call(call)).toMatchObject({ result: { ok: true }, text: "core ran it" })
  expect(calls).toMatchObject([call])
  expect(await turnEnds($, "agent-1")).toMatchObject({ text: "the subagent's answer" })
  expect(shown).toEqual([])
})

test("a subagent's turn start leaves the status line as it is", async ($, on) => {
  home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  const shown = statusLine(on)
  on("turn.start", ($, e) => ({ turnId: e.turnId }))
  await $.turn.start({ text: "", turnId: "t2", agentId: "agent-1" })
  expect(shown).toEqual([])
})

// The pipeline pane: /workshop-forge opens it, and it lists every iteration of the pipeline /workshop-forge named.
const PANE = {
  plugin: "tars-mod",
  component: "Pane",
  requestId: "sttp-pipeline",
  props: {
    title: "Pipeline",
    isFocused: false,
    bodyColumns: 40,
    placement: "dock",
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
}

const MORE = ITERATIONS.replace("| CSV      | 2.2 | totals       | PLANNED |", [
  "| CSV      | 2.2 | totals       | PLANNED |",
  "| CSV      | 2.3 | quoting      | WONT-DO |",
  "| PDF      | 3.1 | layout       | BLOCKED |",
].join("\n"))

// The panes the mod asked to open and to close.
const panes = on => {
  const opened = [], closed = [], open = new Set()
  on("ui.open", ($, e) => (opened.push(e.id), open.add(e.id), { value: { isPlaced: true } }))
  on("ui.close", ($, e) => (closed.push(e.id), open.delete(e.id), { value: undefined }))
  on("ui.panes", () => ({
    value: [...open].map(id => ({ id, title: "Pipeline", isShown: true, isFocused: false, isPlaced: true })),
  }))
  on("command.run", () => ({ text: "the skill runs" }))
  return { opened, closed }
}

const texts = async ui => (await ui.findAll({ type: "Text" })).map(t => t.text)

test("/workshop-forge opens the pipeline pane and runs as it would", async ($, on) => {
  home(on)
  const { opened } = panes(on)
  expect(await run($, "tars:workshop-forge", "exports 1")).toBe("the skill runs")
  expect(opened).toEqual(["sttp-pipeline"])
  await run($, "tars:sttp-mode", "full")
  expect(opened).toEqual(["sttp-pipeline"])
})

test("/workshop-forge-pane opens the pipeline pane with no turn", async ($, on) => {
  home(on)
  const { opened } = panes(on)
  expect(await run($, "workshop-forge-pane")).toBe("Pipeline pane opened.")
  expect(opened).toEqual(["sttp-pipeline"])
})

test("/workshop-forge-pane closes the pipeline pane when it is open", async ($, on) => {
  home(on)
  const { closed } = panes(on)
  await run($, "workshop-forge-pane")
  expect(await run($, "workshop-forge-pane")).toBe("Pipeline pane closed.")
  expect(closed).toEqual(["sttp-pipeline"])
})

test("the pane lists every iteration by category, a check for DONE and a pointer at CURRENT", async ($, on) => {
  home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: MORE })
  for (const surface of ["terminal", "desktop"]) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await texts(ui)).toEqual([
      "csv · 1/4 done",
      "Setup",
      "✓ 1.1 export route",
      "CSV",
      "▶ 2.1 header row",
      "○ 2.2 totals",
      "– 2.3 quoting · WONT-DO",
      "PDF",
      "⊘ 3.1 layout · BLOCKED",
    ])
    await ui.unmount()
  }
})

test("the pane colors DONE iterations as a success and the CURRENT one as a warning", async ($, on) => {
  home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: MORE })
  const ui = await $.ui.mount({ ...PANE, surface: "terminal" })
  expect((await ui.find({ type: "Text", text: /export route/ }))?.props.color).toBe("success")
  expect((await ui.find({ type: "Text", text: /header row/ }))?.props.color).toBe("warning")
  expect((await ui.find({ type: "Text", text: /totals/ }))?.props.color).toBeUndefined()
  await ui.unmount()
})

test("between iterations, the pane points at the next one, as the status line does", async ($, on) => {
  home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS.replace("| CURRENT |", "| DONE    |") })
  const ui = await $.ui.mount({ ...PANE, surface: "terminal" })
  const next = await ui.find({ type: "Text", text: /totals/ })
  expect(next?.text).toBe("▶ 2.2 totals")
  expect(next?.props.color).toBe("warning")
  await ui.unmount()
})

test("between iterations, the pane points at the NEXT one, says so, and leaves an earlier PLANNED one plain",
  async ($, on) => {
    const iterations = ITERATIONS.replace("| CURRENT |", "| PLANNED |")
      .replace("| totals       | PLANNED |", "| totals       | NEXT    |")
    home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: iterations })
    const ui = await $.ui.mount({ ...PANE, surface: "terminal" })
    const next = await ui.find({ type: "Text", text: /totals/ })
    expect(next?.text).toBe("▶ 2.2 totals · NEXT")
    expect(next?.props.color).toBe("warning")
    const earlier = await ui.find({ type: "Text", text: /header row/ })
    expect(earlier?.text).toBe("○ 2.1 header row")
    expect(earlier?.props.color).toBeUndefined()
    await ui.unmount()
  })

test("the pane follows the pipeline file at the end of a turn", async ($, on) => {
  const files = home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
  statusLine(on)
  const ui = await $.ui.mount({ ...PANE, surface: "terminal" })
  files[PIPELINE] = ITERATIONS.replace("| CURRENT |", "| DONE    |").replace("| PLANNED |", "| CURRENT |")
  await turnEnds($)
  expect(await texts(ui)).toContain("▶ 2.2 totals")
  expect(await texts(ui)).toContain("✓ 2.1 header row")
  await ui.unmount()
})

test("a session start or a reload registers /workshop-forge-pane", async ($, on) => {
  home(on)
  const registered = []
  on("command.register", ($, e) => (registered.push(e.name), { value: { command: e.name } }))
  on("session.start", (_, e) => ({ cwd: e.cwd }))
  on("ui.status", () => ({ value: undefined }))
  await $.session.start({ cwd: "/", surface: "terminal", isInteractive: true })
  expect(registered).toEqual(["workshop-forge-pane"])
})

test("a session start or a reload leaves the pane closed, even while /workshop-forge has named a pipeline",
  async ($, on) => {
    home(on, { "/home/u/.tars/forge-s1": PIPELINE, [PIPELINE]: ITERATIONS })
    const { opened } = panes(on)
    on("command.register", ($, e) => ({ value: { command: e.name } }))
    on("session.start", (_, e) => ({ cwd: e.cwd }))
    on("ui.status", () => ({ value: undefined }))
    await $.session.start({ cwd: "/", surface: "terminal", isInteractive: true })
    expect(opened).toEqual([])
  })

test("with no pipeline named, the pane says so", async ($, on) => {
  home(on)
  const ui = await $.ui.mount({ ...PANE, surface: "terminal" })
  expect(await texts(ui)).toEqual(["No pipeline yet: /workshop-forge names one."])
  await ui.unmount()
})

test("off in /config, /workshop-forge opens no pane and an open one closes", { options: { pipelinePane: false } },
  async ($, on) => {
    home(on)
    const { opened, closed } = panes(on)
    on("session.start", (_, e) => ({ cwd: e.cwd }))
    await $.session.start({ cwd: "/", surface: "terminal", isInteractive: true })
    expect(closed).toEqual(["sttp-pipeline"])
    expect(await run($, "tars:workshop-forge", "exports 1")).toBe("the skill runs")
    expect(opened).toEqual([])
  })

test("off in /config, /workshop-forge-pane opens no pane and says where to turn it on",
  { options: { pipelinePane: false } }, async ($, on) => {
    home(on)
    const { opened } = panes(on)
    expect(await run($, "workshop-forge-pane")).toBe(
      "Pipeline pane is off: turn it on in /config (tars-mod → Pipeline pane).")
    expect(opened).toEqual([])
  })
