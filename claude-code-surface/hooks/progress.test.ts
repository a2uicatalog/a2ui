import { test, expect } from 'claude-code/testing'

import { STALL_MS, barCells, compactBar, ease, parseProgress, progressBlocks } from './jobs'

const NOW = 1_000_000_000

test('parseProgress reads value/percent, clamps, and derives state', () => {
  expect(parseProgress('b', '{"label":"Build","value":42}', NOW, NOW)?.state).toBe('running')
  expect(parseProgress('b', '{"percent":140}', NOW, NOW)?.value).toBe(100)
  expect(parseProgress('b', '{"value":100}', NOW, NOW)?.state).toBe('done')
  expect(parseProgress('b', '{"value":10}', NOW - STALL_MS - 1, NOW)?.state).toBe('stalled')
  expect(parseProgress('b', 'half-written', NOW, NOW)).toBeNull()
})

test('a half-written file keeps the previous bar, and shown carries over', () => {
  const prev = parseProgress('b', '{"value":30}', NOW, NOW)!
  const moved = { ...prev, shown: 25 }
  expect(parseProgress('b', '{"val', NOW, NOW, moved)).toEqual(moved)
  expect(parseProgress('b', '{"value":60}', NOW + 1, NOW + 1, moved)?.shown).toBe(25)
})

test('ease slides toward the target and lands on it', () => {
  let shown = 10
  for (let i = 0; i < 40; i++) shown = ease(shown, 60)
  expect(shown).toBe(60)
  expect(ease(10, 60)).toBeGreaterThan(10)
  expect(ease(10, 60)).toBeLessThan(60)
})

test('barCells fills in eighths and always spans the width', () => {
  const c = barCells(50, 32, 0)
  expect(c.full).toBe(16)
  expect(c.partial).toBe('')
  expect(c.full + (c.partial ? 1 : 0) + c.empty).toBe(32)
  const d = barCells(51.5, 32, 3)
  expect(d.full + (d.partial ? 1 : 0) + d.empty).toBe(32)
  expect(d.shimmer).toBe(3)
  expect(barCells(0, 32, 5).shimmer).toBe(-1)
})

test('progress becomes progress_bar atoms and a compact status bar', () => {
  const p = { ...parseProgress('build', '{"label":"Build","value":42,"caption":"atoms"}', NOW, NOW)!, shown: 42 }
  expect(progressBlocks([p], NOW)[0]).toMatchObject({ type: 'progress_bar', label: 'Build', value: 42, caption: 'atoms' })
  expect(compactBar(p)).toBe('▕████▎     ▏42% Build')
})
