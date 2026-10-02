import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Block, Gate, Job, Limit, Progress, ToolRow } from '../types'
import { DEMO, drawBlock, parsePayload } from './a2ui'
import { DONE_LINGER_MS, LONG_JOB_MS, NO_JOB, ease, fmtDur, fmtTok, jobBlocks, limitLines, parseProgress, progressBlocks, parseGateLog, statusLine, toolLabel } from './jobs'

const PANE = 'a2ui-claude-code'
const JOB_PANE = 'a2ui-job'
// Set at session start: $A2UI_PROGRESS_DIR, else ~/.cache/a2ui-progress (what bin/a2ui-progress writes).
let PROGRESS_DIR = ''
// The `gate_log` option: a JSONL run log ({ts, process, status: "ok" | "failed at <phase>: <cmd>", duration_s}); empty = off.
let GATE_LOG = ''
// Exact xterm-256 greys: a truecolor hex gets snapped to the 6x6x6 cube on 256-colour terminals.
const DARK_BG = '#1c1c1c'

const title = atom({ plugin: 'a2ui-claude-code', key: 'title' } as const, 'A2UI')
const blocks = atom({ plugin: 'a2ui-claude-code', key: 'blocks' } as const, [])
const error = atom({ plugin: 'a2ui-claude-code', key: 'error' } as const, '')
const job = atom({ plugin: 'a2ui-claude-code', key: 'job' } as const, NO_JOB)
const gate = atom({ plugin: 'a2ui-claude-code', key: 'gate' } as const, null)
const now = atom({ plugin: 'a2ui-claude-code', key: 'now' } as const, 0)
const progress = atom({ plugin: 'a2ui-claude-code', key: 'progress' } as const, [])

let isLightTheme = false
let gateMtime = 0
let jobPaneOpened = ''
let frame = 0
let seenProgress = new Set<string>()

// State outlives a reload, so a Job saved by an older version may lack newer fields.
function withDefaults(j: Partial<Job> | undefined): Job {
  return { ...NO_JOB, ...j, tools: j?.tools ?? [], limits: j?.limits ?? [] }
}

async function readTheme($: any) {
  try {
    const row = (await $.config.list()).find((r: any) => r.key === 'theme')
    isLightTheme = /^light/i.test(String(row?.value ?? ''))
  } catch {
    isLightTheme = false
  }
}

async function refreshGate($: any, isQuiet: boolean) {
  if (GATE_LOG === '') return
  try {
    const stat = await $.fs.stat(GATE_LOG)
    if (stat.mtimeMs === gateMtime) return
    gateMtime = stat.mtimeMs
    const latest: Gate | null = parseGateLog(await $.fs.read(GATE_LOG))
    const before: Gate | null = await read($, gate)
    await update($, gate, () => latest)
    const isNew = latest !== null && (before === null || latest.at !== before.at)
    if (!isQuiet && isNew && latest && !latest.isOk) {
      $.ui.toast(`Deploy gate failed: ${latest.process} at ${latest.phase}`)
    }
  } catch {
    // No log on this machine or unreadable: the status line just leaves the gate out.
  }
}

async function refreshUsage($: any) {
  try {
    const usage = await $.session.usage()
    await update($, job, (j: Job) => ({
      ...j,
      ctxTokens: usage.context.tokens ?? j.ctxTokens,
      ctxPercent: usage.context.percent ?? j.ctxPercent,
      costUsd: usage.cost?.usd ?? j.costUsd,
      limits: usage.rateLimits.map((r: Limit) => ({ kind: r.kind, percentUsed: r.percentUsed, resetsAt: r.resetsAt })),
    }))
  } catch {
    // Usage is a nice-to-have; the dashboard shows what it has.
  }
}

// Reads every <id>.json a script wrote with a2ui-progress; a finished bar lingers, then drops.
async function scanProgress($: any) {
  if (PROGRESS_DIR === '') return
  const t = await $.clock.now()
  let entries: { name: string; kind: string; mtimeMs: number }[] = []
  try {
    entries = await $.fs.list(PROGRESS_DIR)
  } catch {
    entries = []
  }
  const before: Progress[] = (await read($, progress)) ?? []
  const next: Progress[] = []
  for (const f of entries) {
    if (f.kind !== 'file' || !f.name.endsWith('.json')) continue
    const id = f.name.slice(0, -5)
    const prev = before.find(p => p.id === id)
    if (prev && prev.updatedAt === f.mtimeMs && prev.state !== 'running') {
      if (!(prev.state === 'done' && t - f.mtimeMs > DONE_LINGER_MS)) next.push(prev)
      continue
    }
    let text = ''
    try {
      text = await $.fs.read(`${PROGRESS_DIR}/${f.name}`)
    } catch {
      continue
    }
    const p = parseProgress(id, text, f.mtimeMs, t, prev)
    if (!p || (p.state === 'done' && t - f.mtimeMs > DONE_LINGER_MS)) continue
    next.push(p)
    if (!seenProgress.has(id) && p.state === 'running') {
      seenProgress.add(id)
      void $.ui.open({ id: JOB_PANE, title: 'Jobs' })
    }
  }
  await update($, progress, () => next)
}

// 4 frames a second while any bar moves or runs: eases values and walks the shimmer.
async function animate($: any) {
  frame += 1
  if (frame % 4 === 0) await scanProgress($)
  const list: Progress[] = (await read($, progress)) ?? []
  const isMoving = list.some(p => p.state === 'running' || p.shown !== p.value)
  if (!isMoving) return
  await update($, progress, (ps: Progress[]) => ps.map(p => ({ ...p, shown: ease(p.shown, p.value) })))
  const t = await $.clock.now()
  await update($, now, () => t)
  if (frame % 4 === 0) $.ui.status(statusLine(await read($, gate), withDefaults(await read($, job)), t, list))
}

async function tick($: any) {
  const t = await $.clock.now()
  const j: Job = withDefaults(await read($, job))
  if (j.isActive) {
    await refreshUsage($)
    await update($, now, () => t)
    if (t - j.startedAt >= LONG_JOB_MS && jobPaneOpened !== j.turnId) {
      jobPaneOpened = j.turnId
      void $.ui.open({ id: JOB_PANE, title: 'Long job' })
    }
  }
  $.ui.status(statusLine(await read($, gate), withDefaults(await read($, job)), t, (await read($, progress)) ?? []))
}

export const register: Register = (on, options) => {
  GATE_LOG = typeof options.gate_log === 'string' ? options.gate_log.trim() : ''

  on('session.start', async ($, e, next) => {
    const home = (await $.env.get('HOME')) ?? ''
    PROGRESS_DIR = (await $.env.get('A2UI_PROGRESS_DIR')) ?? (home ? `${home}/.cache/a2ui-progress` : '')
    await $.command.register({
      name: 'a2ui',
      description: 'Render an A2UI payload (file path or inline JSON; none = demo) in a pane',
    })
    await $.command.register({
      name: 'a2ui-job',
      description: 'Open the long-job dashboard (opens by itself once a turn passes 60s)',
    })
    await refreshGate($, true)
    await tick($)
    $.clock.every(2000, () => void tick($))
    $.clock.every(15000, () => void refreshGate($, false))
    $.clock.every(250, () => void animate($))

    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    const t = await $.clock.now()
    let ctx = 0
    try {
      ctx = (await $.session.usage()).context.tokens ?? 0
    } catch {}
    await update($, job, () => ({
      ...NO_JOB,
      isActive: true,
      turnId: e.turnId,
      prompt: e.text,
      startedAt: t,
      ctxStart: ctx,
      ctxTokens: ctx,
    }))

    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const started = await $.clock.now()
    const id = e.tool_use_id
    const args = e as unknown as Record<string, any>
    const label = (e.agentId ? '↳ ' : '') + toolLabel(e.tool, args)

    // An a2uicatalog MCP call carrying a blocks payload: draw it natively too.
    const payload = args.payload
    if (e.tool.startsWith('mcp__a2uicatalog__') && Array.isArray(payload?.blocks) && payload.blocks.length) {
      await update($, title, () => String(payload.title ?? 'A2UI'))
      await update($, blocks, () => payload.blocks.filter((b: any) => b && typeof b.type === 'string'))
      await update($, error, () => '')
      void $.ui.open({ id: PANE, title: 'A2UI' })
    }
    await update($, job, (j: Job) =>
      j.isActive ? { ...j, tools: [...j.tools, { id, label, state: 'running' as const, startedAt: started, endedAt: 0 }].slice(-200) } : j,
    )
    const ran = await next(e)
    const ended = await $.clock.now()
    const state: ToolRow['state'] = ran.deny !== undefined || ran.isError ? 'error' : 'ok'
    await update($, job, (j: Job) => ({
      ...j,
      tools: (j.tools ?? []).map(t => (t.id === id ? { ...t, state, endedAt: ended } : t)),
    }))
    // An ops.py run just finished in this session: pick up its gate result now, not in 15s.
    if (e.tool === 'Bash' && /ops\.py/.test(String(args.command ?? ''))) {
      await refreshGate($, false)
    }

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const t = await $.clock.now()
    await refreshUsage($)
    const j: Job = withDefaults(await read($, job))
    const wasLong = t - j.startedAt >= LONG_JOB_MS
    const out = done.usage ? ` · ${fmtTok(done.usage.output_tokens)} out` : ''
    const outcome = e.isAborted ? `interrupted after ${fmtDur(t - j.startedAt)}` : `done in ${fmtDur(t - j.startedAt)}${out}`
    await update($, job, (x: Job) => ({ ...x, isActive: false, endedAt: t, outcome }))
    await update($, now, () => t)
    if (wasLong) $.ui.toast(`Long job ${outcome}`)
    $.ui.status(statusLine(await read($, gate), withDefaults(await read($, job)), t))

    return done
  })

  on('command.run', { command: 'a2ui' }, async ($, e) => {
    await readTheme($)
    const arg = e.args.trim()
    try {
      let next: { title: string; blocks: Block[] }
      if (arg === '') {
        next = { title: 'A2UI demo', blocks: DEMO }
      } else {
        const raw = /^[{[]/.test(arg) ? arg : await $.fs.read(arg)
        next = parsePayload(raw)
      }
      await update($, title, () => next.title)
      await update($, blocks, () => next.blocks)
      await update($, error, () => '')
    } catch (err) {
      await update($, error, () => `Could not render: ${(err as Error).message}`)
    }
    await $.ui.open({ id: PANE, title: 'A2UI' })

    return { text: 'A2UI pane opened.' }
  })

  on('command.run', { command: 'a2ui-job' }, async $ => {
    await readTheme($)
    await refreshGate($, true)
    await refreshUsage($)
    const t = await $.clock.now()
    await update($, now, () => t)
    await $.ui.open({ id: JOB_PANE, title: 'Long job' })

    return { text: 'Long-job dashboard opened.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text } = els
    const [t, bs, err] = [await read($, title), await read($, blocks), await read($, error)]

    return (
      <Box flexDirection="column" gap={1} backgroundColor={isLightTheme ? undefined : DARK_BG} width="100%" minHeight={Math.max(10, (e.viewport?.rows ?? 24) - 2)} paddingX={1}>
        <Text bold color="claude">{t}</Text>
        {err !== '' && <Text color="error">{err}</Text>}
        {err === '' && bs.length === 0 && <Text dimColor>Run /a2ui [file.json] to render a payload.</Text>}
        {bs.map((b, i) => drawBlock(b, els, i))}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: JOB_PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text } = els
    const [j, g, t] = [withDefaults(await read($, job)), await read($, gate), await read($, now)]
    const ps: Progress[] = (await read($, progress)) ?? []
    const bs = [...(ps.length ? [{ type: 'subheading', text: 'Script progress' }, ...progressBlocks(ps, t)] : []), ...(j.startedAt === 0 ? [] : jobBlocks(j, g, t))]
    const f = Math.floor(t / 250)

    return (
      <Box flexDirection="column" gap={1} backgroundColor={isLightTheme ? undefined : DARK_BG} width="100%" minHeight={Math.max(10, (e.viewport?.rows ?? 24) - 2)} paddingX={1}>
        {bs.length === 0 && <Text dimColor>No turn or script progress yet this session.</Text>}
        {bs.map((b, i) => drawBlock(b, els, i, f))}
        <Box flexGrow={1} />
        <Box flexDirection="column" alignItems="flex-end">
          {limitLines(j.limits, t).map(l => (
            <Text color={l.isHigh ? 'warning' : undefined} dimColor={!l.isHigh}>{l.text}</Text>
          ))}
        </Box>
      </Box>
    )
  })
}
