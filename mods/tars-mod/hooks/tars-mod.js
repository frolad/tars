// The TARS mod: the parts of TARS that run inside Claude Code. hooks/sttp.py, the settings hooks Codex runs too,
// reads what these commands write, so both tools keep one state.

// A status table row: | Category | # | Title | Status |
const ROW = /^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*([^|]*?)\s*\|\s*([A-Z-]+)\s*\|\s*$/gm
const OPEN = ["CURRENT", "NEXT", "PLANNED", "BLOCKED"]
const PANE = "sttp-pipeline"
// The pane's mark per status; SKIPPED, WONT-DO, REVERTED and SPLIT rows get "–", dimmed, with their status.
const MARK = { DONE: "✓", CURRENT: "▶", NEXT: "○", PLANNED: "○", BLOCKED: "⊘" }
const COLOR = { DONE: "success", CURRENT: "warning" } // theme keys: they follow the person's theme

export function register(on, options) {
  const shown = options.statusLine !== false
  const paned = options.pipelinePane !== false

  // Answers /sttp-mode, /sttp-guards, /workshop-questions and /workshop-forge-pane here, with no model turn; every
  // other command runs as it would.
  on("command.run", async ($, e, next) => {
    const command = e.command.replace(/^tars:/, "")
    const arg = e.args.trim().toLowerCase()
    if (command === "workshop-forge-pane") {
      if (!paned) return { text: "Pipeline pane is off: turn it on in /config (tars-mod → Pipeline pane)." }
      // One still waiting undrawn for a wider terminal is not on screen: the command opens it.
      if ((await $.ui.panes()).some(pane => pane.id === PANE && pane.isPlaced)) {
        await $.ui.close({ id: PANE })
        return { text: "Pipeline pane closed." }
      }
      await $.ui.open({ id: PANE, title: "Pipeline" })
      return { text: "Pipeline pane opened." }
    }
    if (command === "sttp-mode") {
      const text = await mode($, arg)
      await refresh($, shown)
      return { text }
    }
    if (command === "sttp-guards") return { text: await guards($, arg) }
    if (command === "workshop-questions") return { text: await questions($, arg) }
    if (command === "workshop-forge" && paned) void $.ui.open({ id: PANE, title: "Pipeline" }).catch(() => {})
    return next(e)
  }).catch(($, e, next) => next(e)) // a failed read or write: the skill and hooks/sttp.py answer, with a model turn

  // The status line follows the files: at the start and end of each turn, and after a write under .blueprints/.
  on("session.start", async ($, e, next) => {
    const result = await next(e)
    await $.command
      .register({ name: "workshop-forge-pane", description: "Open or close the /workshop-forge pipeline pane" })
      .catch(() => {})
    await refresh($, shown)
    if (!paned) await $.ui.close({ id: PANE }).catch(() => {}) // turned off in /config while it was open
    return result
  })
  on("turn.start", async ($, e, next) => {
    const result = await next(e)
    if (!e.agentId) await refresh($, shown)
    return result
  })
  on("turn.complete", async ($, e, next) => {
    if (!e.agentId) await refresh($, shown)
    return next(e)
  })
  on("tool.call", async ($, e, next) => {
    const result = await next(e)
    const path = String(e.file_path ?? e.notebook_path ?? e.command ?? "")
    if (!e.agentId && path.includes(".blueprints")) await refresh($, shown)
    return result
  })

  // The pipeline pane: what /workshop-forge named, every iteration under its category. refresh() redraws it.
  if (paned) on("ui.render", { component: "Pane", requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const { path, text } = await forgePipeline($)
    if (!text) return h(Text, { dimColor: true }, "No pipeline yet: /workshop-forge names one.")
    const rows = [...text.matchAll(ROW)]
    const done = rows.filter(r => r[4] === "DONE").length
    const counted = done + rows.filter(r => OPEN.includes(r[4])).length
    const lines = [h(Text, { bold: true }, `${pipelineName(path, text)} · ${done}/${counted} done`)]
    const at = nextRow(rows) // between iterations no row is CURRENT: the pointer waits on the next one
    rows.forEach((row, i) => {
      const [, category, number, title, status] = row
      if (category !== rows[i - 1]?.[1]) lines.push(h(Text, { bold: true }, category))
      const mark = row === at ? MARK.CURRENT : MARK[status]
      const suffix = ["DONE", "CURRENT", "PLANNED"].includes(status) ? "" : ` · ${status}`
      const line = `${mark ?? "–"} ${number} ${title}${suffix}`
      lines.push(h(Text, { color: COLOR[row === at ? "CURRENT" : status], dimColor: !mark, bold: row === at }, line))
    })
    return h(Box, { flexDirection: "column" }, ...lines)
  })
}

// ~/.tars as hooks/sttp.py finds it: HOME when set, else the user's profile folder, all a Windows terminal sets.
async function tarsDir($) {
  return `${(await $.env.get("HOME")) || (await $.env.get("USERPROFILE"))}/.tars`
}

async function mode($, arg) {
  const file = `${await tarsDir($)}/mode`
  if (arg === "primary" || arg === "full") {
    await $.fs.write(file, arg + "\n")
    return `STTP mode set to ${arg}.`
  }
  if (arg) return `Unknown STTP mode '${arg}'. Use primary or full.`
  const set = (await $.fs.exists(file)) ? (await $.fs.read(file)).trim().toLowerCase() : ""
  return `STTP mode: ${set === "full" ? "full" : "primary"}.`
}

async function questions($, arg) {
  const file = `${await tarsDir($)}/questions`
  if (arg === "dialog" || arg === "transcript") {
    await $.fs.write(file, arg + "\n")
    return `Grill questions set to ${arg}.`
  }
  if (arg) return `Unknown question form '${arg}'. Use dialog or transcript.`
  const set = (await readOr($, file)).trim().toLowerCase()
  return `Grill questions: ${set === "transcript" ? "transcript" : "dialog"}.`
}

async function guards($, arg) {
  const dir = await tarsDir($)
  const file = `${dir}/guards-off-${await $.session.id()}`
  const defaultFile = `${dir}/guards-default`
  const words = arg.split(/\s+/).join(" ")
  if (words === "off" || words === "on") {
    await $.fs.write(file, words + "\n")
    return words === "off"
      ? "TARS guards off for this session: git steps are not checked. /sttp-guards on turns them back on."
      : "TARS guards on."
  }
  if (words === "default off" || words === "default on") {
    await $.fs.write(defaultFile, words.split(" ")[1] + "\n")
    return words === "default off"
      ? "TARS guards default: off. Sessions without their own /sttp-guards on|off, open ones too, don't check git " +
          "steps. /sttp-guards default on turns it back on."
      : "TARS guards default: on."
  }
  const fallback = (await readOr($, defaultFile)).trim() === "off" ? "off" : "on"
  if (words === "default") return `TARS guards default: ${fallback}.`
  if (words) return `Unknown argument '${words}'. Use /sttp-guards on|off or /sttp-guards default on|off.`
  const own = (await readOr($, file)).trim()
  return own === "off" || own === "on"
    ? `TARS guards: ${own} for this session; the default is ${fallback}.`
    : `TARS guards: ${fallback}, the default.`
}

async function readOr($, path) {
  return (await $.fs.exists(path)) ? await $.fs.read(path) : ""
}

// Off in /config, each refresh clears the line: the one pinned before the switch would stay up otherwise.
async function refresh($, shown) {
  try {
    $.ui.invalidate("ui.render") // the pipeline pane
    $.ui.status(shown ? await statusLine($) : undefined)
  } catch {
    // a failed read leaves the last line up
  }
}

// "primary · csv → CSV → header row · CURRENT · 1/3", after Claude Code's own "⚠ tars-mod:"; hooks/sttp.py keeps
// the pause and the pipeline /workshop-forge named in ~/.tars/paused-<session> and ~/.tars/forge-<session>.
async function statusLine($) {
  const dir = await tarsDir($)
  const id = await $.session.id()
  const paused = await $.fs.exists(`${dir}/paused-${id}`)
  const set = (await readOr($, `${dir}/mode`)).trim().toLowerCase()
  const parts = [paused ? "paused" : set === "full" ? "full" : "primary"]
  const { path, text } = await forgePipeline($)
  if (text) parts.push(pipelineState(path, text))
  return parts.join(" · ")
}

// The iterations.md /workshop-forge named in this session, and its text; both "" when it named none.
async function forgePipeline($) {
  const path = (await readOr($, `${await tarsDir($)}/forge-${await $.session.id()}`)).trim()
  return { path, text: path ? await readOr($, path) : "" }
}

function pipelineName(path, text) {
  return text.match(/^# Pipeline \d+: (.+)$/m)?.[1].trim() ?? path.split("/").at(-2)
}

// The pipeline's CURRENT row of its status table, else its NEXT one, else its first PLANNED or BLOCKED one, and
// how many rows are DONE of those DONE or still open. WONT-DO, REVERTED, SPLIT and SKIPPED rows count on neither
// side, so the count reaches its total when the pipeline is finished.
function pipelineState(path, text) {
  const name = pipelineName(path, text)
  const rows = [...text.matchAll(ROW)]
  const done = rows.filter(r => r[4] === "DONE").length
  const open = rows.filter(r => OPEN.includes(r[4]))
  const row = nextRow(rows)
  const where = row ? [name, row[1], row[3]].join(" → ") : name
  return [where, row ? row[4] : "DONE", `${done}/${done + open.length}`].join(" · ")
}

// The CURRENT row, else the NEXT one, else the first PLANNED or BLOCKED one: what the status line names and the pane
// points at.
function nextRow(rows) {
  const open = rows.filter(r => OPEN.includes(r[4]))
  return open.find(r => r[4] === "CURRENT") ?? open.find(r => r[4] === "NEXT") ?? open[0]
}
