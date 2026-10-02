import type { Block } from '../types'
import { barCells } from './jobs'

export const DEMO: Block[] = [
  { type: 'heading', text: 'A2UI in Claude Code' },
  { type: 'body', text: 'The same declarative blocks the GAS and web renderers draw, here as terminal cells.' },
  { type: 'callout', kind: 'tip', title: 'Surface scope', text: 'Only a subset of atoms is drawn here; the rest show a placeholder.' },
  {
    type: 'metric_row',
    metrics: [
      { label: 'Atoms drawn', value: '10', trend: 'up' },
      { label: 'Surface', value: 'mod' },
    ],
  },
  { type: 'steps', items: [{ label: 'Write', text: 'Emit a payload' }, { label: 'Render', text: 'Run /a2ui payload.json' }] },
  { type: 'table', headers: ['Atom', 'Terminal'], rows: [['callout', 'yes'], ['hub', 'not yet']] },
  { type: 'code', language: 'json', content: '{ "type": "badge", "text": "preview" }' },
]

const str = (v: unknown): string => (typeof v === 'string' ? v : v == null ? '' : String(v))
const list = (v: unknown): unknown[] => (Array.isArray(v) ? v : [])
const plain = (s: string): string => s.replace(/\*\*(.+?)\*\*/g, '$1')

const KIND: Record<string, { color: string; icon: string }> = {
  info: { color: 'suggestion', icon: 'i' },
  tip: { color: 'success', icon: '*' },
  warning: { color: 'warning', icon: '!' },
  danger: { color: 'error', icon: 'x' },
}

// Accepts { blocks: [...] }, a bare array, or a single block.
export const parsePayload = (raw: string): { title: string; blocks: Block[] } => {
  const data = JSON.parse(raw)
  const found = Array.isArray(data) ? data : Array.isArray(data?.blocks) ? data.blocks : [data]
  const ok = found.filter((b: unknown) => b && typeof (b as Block).type === 'string')
  if (ok.length === 0) throw new Error('no blocks with a "type" found')

  return { title: str(data?.title) || 'A2UI', blocks: ok as Block[] }
}

type Els = any

export const drawBlock = (b: Block, { Box, Text, Code }: Els, key: number, frame = 0): any => {
  switch (b.type) {
    case 'progress_bar': {
      const value = Number(b.value) || 0
      const target = typeof b._target === 'number' ? b._target : value
      const c = barCells(value, 32, frame)
      const color = b._state === 'done' ? 'success' : b._state === 'stalled' ? 'warning' : str(b.accent) || 'claude'
      const before = c.shimmer >= 0 ? c.shimmer : c.full
      const after = c.shimmer >= 0 ? c.full - c.shimmer - 1 : 0
      return (
        <Box key={key} flexDirection="column">
          <Text>
            <Text bold>{str(b.label)}</Text>
            {b.show_percent === false ? '' : <Text color={color}> {Math.round(target)}%</Text>}
            {b._state === 'done' ? <Text color="success"> ✓</Text> : null}
          </Text>
          <Text>
            <Text color={color}>{'█'.repeat(before)}</Text>
            {c.shimmer >= 0 ? <Text color="text">█</Text> : null}
            <Text color={color}>{'█'.repeat(Math.max(0, after))}{c.partial}</Text>
            <Text dimColor>{'░'.repeat(Math.max(0, c.empty))}</Text>
          </Text>
          {b.caption ? <Text dimColor>{str(b.caption)}</Text> : null}
        </Box>
      )
    }
    case 'heading':
      return <Box key={key} marginTop={1}><Text bold color="claude">{str(b.text)}</Text></Box>
    case 'subheading':
      return <Box key={key}><Text bold>{str(b.text)}</Text></Box>
    case 'body':
      return <Box key={key}><Text wrap="wrap">{plain(str(b.text))}</Text></Box>
    case 'badge':
      return <Box key={key}><Text inverse color={str(b.color) || 'permission'}>{' ' + str(b.text) + ' '}</Text></Box>
    case 'callout': {
      const k = KIND[str(b.kind)] ?? { color: 'suggestion', icon: 'i' }
      return (
        <Box key={key} flexDirection="column" borderStyle="round" borderColor={k.color} paddingX={1}>
          <Text bold color={k.color}>{k.icon} {str(b.title) || str(b.kind)}</Text>
          <Text wrap="wrap">{plain(str(b.text))}</Text>
        </Box>
      )
    }
    case 'metric_row':
      return (
        <Box key={key} gap={2} flexWrap="wrap">
          {list(b.metrics ?? b.items).map((m: any) => (
            <Box flexDirection="column" borderStyle="single" borderColor="promptBorder" paddingX={1}>
              <Text bold>{str(m.prefix)}{str(m.value)}{str(m.suffix)} {m.trend === 'up' ? '▲' : m.trend === 'down' ? '▼' : ''}</Text>
              <Text dimColor>{str(m.label)}</Text>
              {m.sub ? <Text dimColor>{str(m.sub)}</Text> : null}
            </Box>
          ))}
        </Box>
      )
    case 'key_takeaways':
      return (
        <Box key={key} flexDirection="column">
          {list(b.points).map((p) => <Text wrap="wrap">• {plain(str(p))}</Text>)}
        </Box>
      )
    case 'steps':
      return (
        <Box key={key} flexDirection="column">
          {list(b.items).map((s: any, i) => (
            <Text wrap="wrap"><Text bold color="claude">{i + 1}.</Text> {s.label ? <Text bold>{str(s.label)}: </Text> : null}{plain(str(s.text))}</Text>
          ))}
        </Box>
      )
    case 'table': {
      const headers = list(b.headers).map(str)
      const rows = list(b.rows).map((r) => list(r).map(str))
      const widths = headers.map((h, c) => Math.min(48, Math.max(h.length, ...rows.map((r) => (r[c] ?? '').length))))
      const line = (cells: string[]) => cells.map((c, i) => c.slice(0, widths[i] ?? 0).padEnd(widths[i] ?? 0)).join('  ')
      return (
        <Box key={key} flexDirection="column">
          {b.caption ? <Text dimColor>{str(b.caption)}</Text> : null}
          <Text bold>{line(headers)}</Text>
          <Text dimColor>{widths.map((w) => '─'.repeat(w)).join('  ')}</Text>
          {rows.map((r) => <Text>{line(r)}</Text>)}
        </Box>
      )
    }
    case 'code':
      return <Code key={key} source={str(b.content).slice(0, 9000)} language={str(b.language) || undefined} />
    default:
      return <Box key={key}><Text dimColor>[{b.type}: not drawn on this surface]</Text></Box>
  }
}
