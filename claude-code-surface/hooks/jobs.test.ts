import { test, expect } from 'claude-code/testing'

import { NO_JOB, fmtDur, gateText, jobBlocks, limitLines, parseGateLog, statusLine } from './jobs'

const OK = '{"ts": "2026-10-02T07:59:44+02:00", "process": "repo-publish", "status": "ok", "duration_s": 14.7}'
const FAIL = '{"ts": "2026-10-02T08:10:00+02:00", "process": "atom-change", "status": "failed at verify: python3 -m pytest tests/ -q", "duration_s": 80}'
const AT = Date.parse('2026-10-02T08:12:00+02:00')

test('parseGateLog takes the last parseable run, skipping junk lines', () => {
  const g = parseGateLog([OK, FAIL, 'not json', ''].join('\n'))!
  expect(g.process).toBe('atom-change')
  expect(g.isOk).toBe(false)
  expect(g.phase).toBe('verify')
  expect(g.cmd).toBe('python3 -m pytest tests/ -q')
})

test('gateText reads as a status line', () => {
  expect(gateText(parseGateLog(OK)!, Date.parse('2026-10-02T08:02:00+02:00'))).toBe('gate ✓ repo-publish 15s · 2m ago')
  expect(gateText(parseGateLog(FAIL)!, AT)).toBe('gate ✗ atom-change verify: python3 -m pytest tests/ -q · 2m ago')
})

test('status line adds the job meter only once a turn passes a minute', () => {
  const job = { ...NO_JOB, isActive: true, startedAt: AT - 30_000, ctxStart: 1000, ctxTokens: 49_000 }
  expect(statusLine(null, job, AT)).toBeUndefined()
  expect(statusLine(null, { ...job, startedAt: AT - 75_000 }, AT)).toBe('⏱ 1m15s · +48k ctx')
})

test('dashboard is plain A2UI blocks', () => {
  const job = {
    ...NO_JOB,
    isActive: true,
    prompt: 'deploy it',
    startedAt: AT - 90_000,
    tools: [
      { id: '1', label: 'Bash: ops.py run atom-change', state: 'error' as const, startedAt: AT - 80_000, endedAt: AT - 5000 },
      { id: '2', label: 'Read: x', state: 'running' as const, startedAt: AT - 2000, endedAt: 0 },
    ],
  }
  const blocks = jobBlocks(job, parseGateLog(FAIL), AT)
  expect(blocks.map(b => b.type)).toEqual(['heading', 'body', 'metric_row', 'callout', 'callout', 'table'])
  expect(fmtDur(90_000)).toBe('1m30s')
})

test('usage footer names the window, % used and time to reset', () => {
  const now = Date.parse('2026-10-02T08:00:00Z')
  const lines = limitLines(
    [
      { kind: 'five_hour', percentUsed: 42, resetsAt: '2026-10-02T10:10:00Z' },
      { kind: 'seven_day', percentUsed: 85.5, resetsAt: '2026-10-05T09:00:00Z' },
      { kind: 'spend_limit', percentUsed: 3 },
    ],
    now,
  )
  expect(lines.map(l => l.text)).toEqual([
    'Session (5h) 42% used · resets in 2h10m',
    'Week (7d) 85.5% used · resets in 3d1h',
    'Spend limit 3% used',
  ])
  expect(lines.map(l => l.isHigh)).toEqual([false, true, false])
})
