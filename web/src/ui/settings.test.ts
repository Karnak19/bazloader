import { describe, expect, test } from 'bun:test'
import type { DeviceConfig, Presets } from '../ble/protocol.ts'
import { draftFrom, parseInteger, type SettingsDraft, sameDraft, stepNeutral, validateSettings } from './settings.ts'

const config: DeviceConfig = {
  servoNeutralUs: 1500,
  speedFullOffsetUs: 300,
  speedSlowOffsetUs: 100,
  reverse: false,
  slowdownN: 4,
  jamTimeoutMs: 1500,
}
const presets: Presets = [30, 50, 120, 300]
const draft = (patch: Partial<SettingsDraft> = {}): SettingsDraft => ({ ...draftFrom(presets, config), ...patch })

function errorsOf(d: SettingsDraft) {
  const r = validateSettings(d)
  return r.ok ? {} : r.errors
}

describe('draft', () => {
  test('round-trips the device values', () => {
    const r = validateSettings(draft())
    expect(r).toEqual({ ok: true, values: { presets, config } })
  })

  test('sameDraft tells an edit apart', () => {
    expect(sameDraft(draft(), draftFrom(presets, config))).toBe(true)
    expect(sameDraft(draft({ reverse: true }), draft())).toBe(false)
  })
})

describe('parseInteger', () => {
  test('takes signed integers, including a typographic minus', () => {
    expect(parseInteger(' 42 ')).toBe(42)
    expect(parseInteger('-120')).toBe(-120)
    expect(parseInteger('−120')).toBe(-120)
    expect(parseInteger('+5')).toBe(5)
  })

  test('refuses the rest', () => {
    expect(parseInteger('')).toBeNull()
    expect(parseInteger('1.5')).toBeNull()
    expect(parseInteger('12a')).toBeNull()
    expect(parseInteger('-')).toBeNull()
  })
})

describe('validateSettings', () => {
  test('neutral: 1000–2000 µs', () => {
    expect(errorsOf(draft({ servoNeutralUs: '1000' }))).toEqual({})
    expect(errorsOf(draft({ servoNeutralUs: '2000' }))).toEqual({})
    expect(errorsOf(draft({ servoNeutralUs: '999' })).servoNeutralUs).toBe('Doit être entre 1000 et 2000 µs.')
    expect(errorsOf(draft({ servoNeutralUs: '2001' })).servoNeutralUs).toBeDefined()
  })

  test('offsets: ±500 µs, negative allowed', () => {
    expect(errorsOf(draft({ speedFullOffsetUs: '-500', speedSlowOffsetUs: '500' }))).toEqual({})
    expect(errorsOf(draft({ speedFullOffsetUs: '501' })).speedFullOffsetUs).toBeDefined()
    expect(errorsOf(draft({ speedSlowOffsetUs: '-501' })).speedSlowOffsetUs).toBeDefined()
  })

  test('presets: 1–9999, each reported on its own field', () => {
    const errors = errorsOf(draft({ presets: ['0', '50', '10000', ''] }))
    expect(Object.keys(errors).sort()).toEqual(['preset0', 'preset2', 'preset3'])
    expect(errors.preset3).toBe('Nombre entier attendu, entre 1 et 9999.')
    expect(errorsOf(draft({ presets: ['1', '9999', '2', '3'] }))).toEqual({})
  })

  test('slowdown N: 0–255 (uint8)', () => {
    expect(errorsOf(draft({ slowdownN: '0' }))).toEqual({})
    expect(errorsOf(draft({ slowdownN: '255' }))).toEqual({})
    expect(errorsOf(draft({ slowdownN: '256' })).slowdownN).toBeDefined()
    expect(errorsOf(draft({ slowdownN: '-1' })).slowdownN).toBeDefined()
  })

  test('jam timeout: 300–10000 ms', () => {
    expect(errorsOf(draft({ jamTimeoutMs: '300' }))).toEqual({})
    expect(errorsOf(draft({ jamTimeoutMs: '10000' }))).toEqual({})
    expect(errorsOf(draft({ jamTimeoutMs: '299' })).jamTimeoutMs).toBe('Doit être entre 300 et 10000 ms.')
    expect(errorsOf(draft({ jamTimeoutMs: '65535' })).jamTimeoutMs).toBeDefined()
  })

  test('values come out as numbers, reverse kept', () => {
    const r = validateSettings(draft({ servoNeutralUs: '1490', speedFullOffsetUs: '-250', reverse: true }))
    expect(r.ok && r.values.config).toEqual({ ...config, servoNeutralUs: 1490, speedFullOffsetUs: -250, reverse: true })
  })
})

describe('stepNeutral', () => {
  test('steps from what is typed, within range', () => {
    expect(stepNeutral('1500', 5, 1500)).toBe(1505)
    expect(stepNeutral('1997', 5, 1500)).toBe(2000)
    expect(stepNeutral('1003', -5, 1500)).toBe(1000)
  })

  test('steps from the device value when the field is not a number', () => {
    expect(stepNeutral('', -5, 1480)).toBe(1475)
  })
})
