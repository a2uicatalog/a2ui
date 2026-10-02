// Pure helpers for the gate status line and the long-job dashboard.
// Everything here returns plain data or A2UI blocks; register.tsx owns `$`.
import type { Block, Gate, Job, Limit, Progress, ToolRow } from '../types'

export const LONG_JOB_MS = 60_000

export const fmtDur = (ms: number): string => {
  const s = Math.max(0, Math.round(ms / 1000))
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m${String(s % 60).padStart(2, '0')}s`
  return `${Math.floor(m / 60)}h${String(m % 60).padStart(2, '0')}m`
}

export const fmtAgo = (ms: number): string => (ms < 60_000 ? 'just now' : `${fmtDur(ms).replace(/\d+s$/, '')} ago`)

export const fmtTok = (n: number): string =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1000 ? `${Math.round(n / 1000)}k` : String(n)

// ops/log.jsonl: one JSON object per line, `status` is "ok" or "failed at <phase>: <cmd>".
export const parseGateLog = (text: string): Gate | null => {
  const lines = text.trimEnd().split('\n')
  for (let i = lines.length - 1; i >= 0 && i >= lines.length - 50; i--) {
    let d: any
    try {
      d = JSON.parse(lines[i] ?? '')
    } catch {
      continue
    }
    if (!d || typeof d.process !== 'string' || typeof d.status !== 'string') continue
    const at = Date.parse(d.ts)
    if (Number.isNaN(at)) continue
    const failed = /^failed at (\w+): (.*)$/.exec(d.status)
    return {
      process: d.process,
      isOk: d.status === 'ok',
      phase: failed?.[1] ?? '',
      cmd: failed?.[2] ?? '',
      durationS: typeof d.duration_s === 'number' ? d.duration_s : null,
      at,
    }
  }

  return null
}

const shortCmd = (cmd: string): string => {
  const script = /([\w./-]+\.(?:py|sh|mjs|js))/.exec(cmd)?.[1]?.split('/').pop()
  return (script ?? cmd).slice(0, 40)
}

export const gateText = (g: Gate, now: number): string => {
  const took = g.durationS !== null ? ` ${Math.round(g.durationS)}s` : ''
  return g.isOk
    ? `gate ✓ ${g.process}${took} · ${fmtAgo(now - g.at)}`
    : `gate ✗ ${g.process} ${g.phase}: ${shortCmd(g.cmd)} · ${fmtAgo(now - g.at)}`
}

export const statusLine = (gate: Gate | null, job: Job, now: number, progress: Progress[] = []): string | undefined => {
  const parts: string[] = []
  const live = progress.filter(p => p.state !== 'done').sort((a, b) => b.updatedAt - a.updatedAt)[0]
  if (live) parts.push(compactBar(live))
  if (gate) parts.push(gateText(gate, now))
  if (job.isActive && now - job.startedAt >= LONG_JOB_MS) {
    parts.push(`⏱ ${fmtDur(now - job.startedAt)} · +${fmtTok(job.ctxTokens - job.ctxStart)} ctx`)
  }

  return parts.length ? parts.join('  │  ') : undefined
}

export const toolLabel = (tool: string, input: any): string => {
  const raw = input?.command ?? input?.file_path ?? input?.pattern ?? input?.description ?? input?.url ?? ''
  const one = String(raw).split('\n')[0]
  return one ? `${tool}: ${one}`.slice(0, 60) : tool
}

export const NO_JOB: Job = {
  isActive: false,
  turnId: '',
  prompt: '',
  startedAt: 0,
  endedAt: 0,
  ctxStart: 0,
  ctxTokens: 0,
  ctxPercent: null,
  costUsd: null,
  tools: [],
  outcome: '',
  limits: [],
}

// The dashboard is an A2UI payload: the same blocks /a2ui renders from a file.
export const jobBlocks = (job: Job, gate: Gate | null, now: number): Block[] => {
  const end = job.isActive ? now : job.endedAt
  const failed = job.tools.filter((t: ToolRow) => t.state === 'error')
  const out: Block[] = [
    { type: 'heading', text: job.isActive ? 'Long job running' : `Long job ${job.outcome}` },
    { type: 'body', text: job.prompt.slice(0, 200) },
    {
      type: 'metric_row',
      metrics: [
        { label: 'Elapsed', value: fmtDur(end - job.startedAt), trend: job.isActive ? 'up' : undefined },
        { label: 'Tool calls', value: String(job.tools.length), sub: failed.length ? `${failed.length} failed` : undefined },
        { label: 'Context added', value: `+${fmtTok(Math.max(0, job.ctxTokens - job.ctxStart))}`, sub: 'tokens' },
        ...(job.ctxPercent !== null ? [{ label: 'Context used', value: `${Math.round(job.ctxPercent)}%` }] : []),
        ...(job.costUsd !== null ? [{ label: 'Session cost', value: `$${job.costUsd.toFixed(2)}` }] : []),
      ],
    },
  ]
  if (failed.length) {
    out.push({ type: 'callout', kind: 'danger', title: `${failed.length} tool call(s) failed`, text: failed.slice(-3).map(t => t.label).join('\n') })
  }
  if (gate) {
    out.push({
      type: 'callout',
      kind: gate.isOk ? 'tip' : 'warning',
      title: 'Deploy gate',
      text: gateText(gate, now).replace(/^gate /, ''),
    })
  }
  const recent = job.tools.slice(-8)
  if (recent.length) {
    out.push({
      type: 'table',
      caption: `Last ${recent.length} of ${job.tools.length} tool calls`,
      headers: ['', 'Call', 'Took'],
      rows: recent.map(t => [
        t.state === 'running' ? '…' : t.state === 'error' ? '✗' : '✓',
        t.label,
        t.state === 'running' ? fmtDur(now - t.startedAt) : fmtDur(t.endedAt - t.startedAt),
      ]),
    })
  }

  return out
}

const WINDOW: Record<string, string> = { five_hour: 'Session (5h)', seven_day: 'Week (7d)', spend_limit: 'Spend limit' }

export const fmtUntil = (ms: number): string => {
  if (ms <= 0) return 'now'
  const h = Math.floor(ms / 3_600_000)
  return h >= 24 ? `${Math.floor(h / 24)}d${h % 24}h` : fmtDur(ms).replace(/\d+s$/, '') || '<1m'
}

// The usage footer: one line per rate-limit window, as the status line has them.
export const limitLines = (limits: Limit[], now: number): { text: string; isHigh: boolean }[] =>
  limits.map(l => {
    const at = l.resetsAt ? Date.parse(l.resetsAt) : NaN
    const reset = Number.isNaN(at) ? '' : ` · resets in ${fmtUntil(at - now)}`
    return { text: `${WINDOW[l.kind] ?? l.kind} ${l.percentUsed}% used${reset}`, isHigh: l.percentUsed >= 80 }
  })

export const STALL_MS = 120_000
export const DONE_LINGER_MS = 15_000

// One ~/.cache/a2ui-progress/<id>.json file → a Progress, keeping the animated `shown` value.
export const parseProgress = (id: string, text: string, mtimeMs: number, now: number, prev?: Progress): Progress | null => {
  let d: any
  try {
    d = JSON.parse(text)
  } catch {
    return prev ?? null
  }
  const value = Math.max(0, Math.min(100, Number(d?.value ?? d?.percent)))
  if (Number.isNaN(value)) return prev ?? null
  const state = value >= 100 ? 'done' : now - mtimeMs > STALL_MS ? 'stalled' : 'running'

  return {
    id,
    label: String(d.label ?? id).slice(0, 40),
    caption: String(d.caption ?? '').slice(0, 80),
    value,
    shown: prev?.shown ?? 0,
    updatedAt: mtimeMs,
    state,
  }
}

// Eases the drawn value toward the reported one, so a jump from 10 to 60 slides.
export const ease = (shown: number, value: number): number => {
  const next = shown + (value - shown) * 0.3
  return Math.abs(value - next) < 0.2 ? value : next
}

const EIGHTHS = ['', '▏', '▎', '▍', '▌', '▋', '▊', '▉']

// A bar of `width` cells: [filled, shimmer index within filled, partial cell, empty].
export const barCells = (pct: number, width: number, frame: number): { full: number; partial: string; empty: number; shimmer: number } => {
  const eighths = Math.round((Math.max(0, Math.min(100, pct)) / 100) * width * 8)
  const full = Math.floor(eighths / 8)
  const partial = EIGHTHS[eighths % 8] ?? ''
  const empty = width - full - (partial ? 1 : 0)
  const shimmer = full > 2 ? frame % (full + 6) : -1

  return { full, partial, empty, shimmer: shimmer < full ? shimmer : -1 }
}

export const compactBar = (p: Progress): string => {
  const c = barCells(p.shown, 10, 0)
  return `▕${'█'.repeat(c.full)}${c.partial}${' '.repeat(c.empty)}▏${Math.round(p.value)}% ${p.label}`
}

export const progressBlocks = (list: Progress[], now: number): Block[] =>
  list.map(p => ({
    type: 'progress_bar',
    label: p.label,
    value: p.shown,
    show_percent: true,
    caption: p.state === 'stalled' ? `no update for ${fmtDur(now - p.updatedAt)}${p.caption ? ' · ' + p.caption : ''}` : p.caption,
    _state: p.state,
    _target: p.value,
  }))
