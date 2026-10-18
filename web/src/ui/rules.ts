// Pure rules behind the screens, kept apart so they can be tested without a browser.

import { State, TARGET_MAX, TARGET_MIN } from '../ble/protocol.ts'
import { formatNumber, type Key, type Lang, translate } from '../i18n/index.ts'

// Same thresholds as BATT_WARN_MV and BATT_REFUSE_MV in firmware/src/config.h. Keep them in sync.
export const BATT_WARN_MV = 7000
export const BATT_REFUSE_MV = 6600

// 'usb': the firmware reports 0 mV when no battery is plugged (powered over USB).
export type BatteryLevel = 'ok' | 'warn' | 'low' | 'usb'

export function batteryLevel(mv: number): BatteryLevel {
  if (mv === 0) return 'usb'
  if (mv >= BATT_WARN_MV) return 'ok'
  if (mv >= BATT_REFUSE_MV) return 'warn'
  return 'low'
}

// « 7,90 V » in French, "7.90 V" in English. A non-breaking space keeps the unit with the number.
export function batteryText(mv: number, lang: Lang): string {
  if (mv === 0) return 'USB'
  return `${formatNumber(lang, mv / 1000, 2)}\u00a0V`
}

export function isRunning(state: State | null): boolean {
  return state === State.Running || state === State.Slowdown
}

// Mirrors Run::go() in firmware/src/run.cpp: GO is accepted in every state but a running one.
// (With a flat pack the firmware answers GO by going to LOW_BATT, which the screen then shows.)
export function canGo(state: State | null): boolean {
  return state !== null && !isRunning(state)
}

// Saving settings and test spins need the motor at rest: the firmware ignores config writes during
// a run, and a test spin is a run of its own. JAM, LOW_BATT and DONE are fine, the motor is off.
export function canEditSettings(state: State | null): boolean {
  return state !== null && !isRunning(state) && state !== State.Testing
}

// In French, the same words as the OLED (firmware/src/screen.cpp).
const stateKey: Record<State, Key> = {
  [State.Idle]: 'state.idle',
  [State.Running]: 'state.running',
  [State.Slowdown]: 'state.slowdown',
  [State.Done]: 'state.done',
  [State.Jam]: 'state.jam',
  [State.LowBatt]: 'state.lowBatt',
  [State.Testing]: 'state.testing',
}

export function stateLabel(state: State, lang: Lang): string {
  return translate(lang, stateKey[state])
}

export function clampTarget(n: number): number {
  return Math.min(TARGET_MAX, Math.max(TARGET_MIN, Math.round(n)))
}

// What the user typed in the target field, as a target to request. null when it isn't a number.
export function parseTarget(text: string): number | null {
  const trimmed = text.trim()
  if (!/^\d+$/.test(trimmed)) return null
  return clampTarget(Number(trimmed))
}

// Share of the target loaded, 0..1. The count can overshoot the target after DONE.
export function progress(count: number | null, target: number | null): number {
  if (count === null || !target) return 0
  return Math.min(1, count / target)
}

// Errors come from the browser or the BLE layer, in English and technical. Say the common ones in
// plain words; the rest are shown as they are.
export function connectionErrorText(error: string, lang: Lang): string {
  if (/cancel/i.test(error)) return translate(lang, 'error.cancelled')
  if (/incompatible firmware/i.test(error)) return translate(lang, 'connect.incompatible')
  if (/adapter not available|bluetooth is (turned )?off/i.test(error)) {
    return translate(lang, 'error.bluetoothOff')
  }
  return translate(lang, 'error.connect', { error })
}

// A write that failed, for the settings screen.
export function sendErrorText(error: string, lang: Lang): string {
  const reason = /^not connected$/i.test(error) ? translate(lang, 'error.notConnected') : error
  return translate(lang, 'error.send', { error: reason })
}
