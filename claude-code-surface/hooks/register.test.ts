import { test, expect } from 'claude-code/testing'

import { parsePayload } from './a2ui'

test('parsePayload accepts blocks object, array, single block', () => {
  expect(parsePayload('{"title":"T","blocks":[{"type":"body","text":"x"}]}').title).toBe('T')
  expect(parsePayload('[{"type":"body","text":"x"}]').blocks.length).toBe(1)
  expect(parsePayload('{"type":"heading","text":"h"}').blocks[0]?.type).toBe('heading')
})

test('parsePayload rejects payloads with no typed blocks', () => {
  expect(() => parsePayload('{"blocks":[{"nope":1}]}')).toThrow()
})
