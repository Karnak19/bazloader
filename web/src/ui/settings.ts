// The settings form, as pure functions: the draft the user edits, and the check that turns it
// into values safe to write. Kept apart from the screen so it can be tested without a browser.

import { type DeviceConfig, PRESET_COUNT, type Presets, TARGET_MAX, TARGET_MIN } from '../ble/protocol.ts'
import { type Lang, translate } from '../i18n/index.ts'

// Servo pulse range. With the offsets below the pulse stays within 500–2500 µs, the usual range
// a hobby servo accepts.
export const NEUTRAL_MIN_US = 1000
export const NEUTRAL_MAX_US = 2000
export const NEUTRAL_STEP_US = 5
export const OFFSET_MAX_US = 500
// slowdown_n is a uint8 on the wire.
export const SLOWDOWN_MIN = 0
export const SLOWDOWN_MAX = 255
// jam_timeout_ms is a uint16, but not every uint16 makes sense. Below 300 ms the gap between two
// BBs at slow speed, or a short hiccup in the feed, would read as a jam. Above 10 s the motor
// keeps grinding on a real jam for too long before it stops.
export const JAM_TIMEOUT_MIN_MS = 300
export const JAM_TIMEOUT_MAX_MS = 10000

// What the fields hold: text, as typed, so a half-typed value is not lost or reformatted.
export type SettingsDraft = {
  presets: [string, string, string, string]
  servoNeutralUs: string
  speedFullOffsetUs: string
  speedSlowOffsetUs: string
  reverse: boolean
  slowdownN: string
  jamTimeoutMs: string
}

export type DraftField = Exclude<keyof SettingsDraft, 'presets' | 'reverse'> | `preset${0 | 1 | 2 | 3}`

export type SettingsValues = { presets: Presets; config: DeviceConfig }

export type Validation =
  | { ok: true; values: SettingsValues }
  | { ok: false; errors: Partial<Record<DraftField, string>> }

export function draftFrom(presets: Presets, config: DeviceConfig): SettingsDraft {
  return {
    presets: presets.map(String) as SettingsDraft['presets'],
    servoNeutralUs: String(config.servoNeutralUs),
    speedFullOffsetUs: String(config.speedFullOffsetUs),
    speedSlowOffsetUs: String(config.speedSlowOffsetUs),
    reverse: config.reverse,
    slowdownN: String(config.slowdownN),
    jamTimeoutMs: String(config.jamTimeoutMs),
  }
}

export function sameDraft(a: SettingsDraft, b: SettingsDraft): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

// An integer as typed, with an optional sign. null for anything else (empty, decimals, letters).
export function parseInteger(text: string): number | null {
  const trimmed = text.trim().replace(/^[−–]/, '-')
  if (!/^[+-]?\d+$/.test(trimmed)) return null
  return Number(trimmed)
}

function check(
  text: string,
  min: number,
  max: number,
  unit: string,
  lang: Lang,
): { value: number; error?: undefined } | { value?: undefined; error: string } {
  const n = parseInteger(text)
  // Numbers as the user types them (no thousands separator), the unit kept with the number.
  const vars = { min, max, unit: unit ? `\u00a0${unit}` : '' }
  if (n === null) return { error: translate(lang, 'validation.integer', vars) }
  if (n < min || n > max) return { error: translate(lang, 'validation.range', vars) }
  return { value: n }
}

// The error messages are in `lang`; everything else is the same in both languages.
export function validateSettings(draft: SettingsDraft, lang: Lang): Validation {
  const errors: Partial<Record<DraftField, string>> = {}
  const take = (field: DraftField, text: string, min: number, max: number, unit = ''): number => {
    const r = check(text, min, max, unit, lang)
    if (r.error !== undefined) errors[field] = r.error
    return r.value ?? 0
  }

  const presets = draft.presets.map((p, i) =>
    take(`preset${i as 0 | 1 | 2 | 3}`, p, TARGET_MIN, TARGET_MAX),
  ) as Presets
  const config: DeviceConfig = {
    servoNeutralUs: take('servoNeutralUs', draft.servoNeutralUs, NEUTRAL_MIN_US, NEUTRAL_MAX_US, 'µs'),
    speedFullOffsetUs: take('speedFullOffsetUs', draft.speedFullOffsetUs, -OFFSET_MAX_US, OFFSET_MAX_US, 'µs'),
    speedSlowOffsetUs: take('speedSlowOffsetUs', draft.speedSlowOffsetUs, -OFFSET_MAX_US, OFFSET_MAX_US, 'µs'),
    reverse: draft.reverse,
    slowdownN: take('slowdownN', draft.slowdownN, SLOWDOWN_MIN, SLOWDOWN_MAX),
    jamTimeoutMs: take('jamTimeoutMs', draft.jamTimeoutMs, JAM_TIMEOUT_MIN_MS, JAM_TIMEOUT_MAX_MS, 'ms'),
  }

  if (Object.keys(errors).length > 0) return { ok: false, errors }
  return { ok: true, values: { presets, config } }
}

// The neutral after a ± step. Steps from what is typed when it is a number, else from `fallback`
// (the device's value), and stays within range.
export function stepNeutral(text: string, delta: number, fallback: number): number {
  const n = parseInteger(text) ?? fallback
  return Math.min(NEUTRAL_MAX_US, Math.max(NEUTRAL_MIN_US, n + delta))
}

export const PRESET_INDEXES = Array.from({ length: PRESET_COUNT }, (_, i) => i as 0 | 1 | 2 | 3)
