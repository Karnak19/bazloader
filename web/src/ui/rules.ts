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

// What the user typed in the target field: the target to request (null: nothing to send) and why
// it differs from what was typed, so the screen can say so instead of correcting in silence.
// Empty is not an error: the field just goes back to the device's target.
export type TargetNote = 'min' | 'max' | 'notNumber'
export type TargetInput = { value: number | null; note: TargetNote | null }

export function readTarget(text: string): TargetInput {
  const trimmed = text.trim()
  if (trimmed === '') return { value: null, note: null }
  if (!/^\d+$/.test(trimmed)) return { value: null, note: 'notNumber' }
  const n = Number(trimmed)
  if (n < TARGET_MIN) return { value: TARGET_MIN, note: 'min' }
  if (n > TARGET_MAX) return { value: TARGET_MAX, note: 'max' }
  return { value: n, note: null }
}

// − and + do nothing at the ends of the range: they are disabled there rather than silent.
export function canStep(target: number | null, delta: number): boolean {
  if (target === null) return false
  return clampTarget(target + delta) !== target
}

// ---- The last run, as the device reported it ----
// The device goes from DONE back to IDLE by itself after a couple of seconds, and from a stop
// straight to IDLE. The screen doesn't pretend it is still done: it shows « Prêt » and, under it,
// how the last run ended, until the next GO. Worked out from the states the device notifies.

export type RunEnd = 'done' | 'stopped' | 'jam' | 'lowBatt'
export type LastRun = { end: RunEnd; count: number; target: number }

function runEnd(state: State, count: number, target: number): RunEnd {
  if (state === State.Done) return 'done'
  if (state === State.Jam) return 'jam'
  if (state === State.LowBatt) return 'lowBatt'
  // A run that reached its target and then went IDLE between two notifications is still a full mag.
  return count >= target ? 'done' : 'stopped'
}

// Called on every connected update. `prev` is the state of the previous connected update, null
// right after (re)connecting: a jump seen across a reconnect isn't a transition we watched.
export function nextLastRun(
  last: LastRun | null,
  prev: State | null,
  now: { state: State | null; count: number | null; target: number | null },
): LastRun | null {
  const { state, count, target } = now
  if (state === null || count === null || target === null) return last
  // A run in progress: the previous result no longer applies.
  if (isRunning(state)) return null
  if (prev !== null && isRunning(prev)) return { end: runEnd(state, count, target), count, target }
  // DONE keeps counting the BBs pushed after the stop (overshoot).
  if (state === State.Done && last?.end === 'done') return { ...last, count }
  return last
}

// GO always loads the full target again (the firmware starts every run from 0). After a run cut
// short, say so next to GO, with the number, so nobody tops up a half-full mag by mistake.
// Returns the number GO will load, or null when there is nothing to say.
export function goReloadsHint(last: LastRun | null, state: State | null, target: number | null): number | null {
  if (last === null || target === null || state === null) return null
  if (isRunning(state) || state === State.Testing) return null
  if (last.end === 'done' || last.count >= last.target) return null
  if (last.target !== target) return null
  return target
}

// Whether the count on screen belongs to the current target. After the target changes, the count
// of the last run is from another target (« 13 / 1 » with a full bar): it is shown greyed, bar empty.
export function countIsCurrent(state: State | null, last: LastRun | null, target: number | null): boolean {
  if (state === null) return false
  if (isRunning(state) || state === State.Done || state === State.Testing) return true
  return last !== null && last.target === target
}

// The states that move the motor: when the link drops in one of them, the motor may still turn.
export function motorMayRun(state: State | null): boolean {
  return isRunning(state) || state === State.Testing
}

// One look per state: a tint and a glyph, always with the word, so colour is never alone.
export type Tone = 'idle' | 'run' | 'slow' | 'ok' | 'alarm' | 'warn' | 'test'

export function stateTone(state: State | null): Tone {
  switch (state) {
    case State.Running:
      return 'run'
    case State.Slowdown:
      return 'slow'
    case State.Done:
      return 'ok'
    case State.Jam:
      return 'alarm'
    case State.LowBatt:
      return 'warn'
    case State.Testing:
      return 'test'
    default:
      return 'idle'
  }
}

const lastRunKey: Record<RunEnd, Key> = {
  done: 'last.done',
  stopped: 'last.stopped',
  jam: 'last.jam',
  lowBatt: 'last.lowBatt',
}

export function lastRunText(last: LastRun, lang: Lang): string {
  return translate(lang, lastRunKey[last.end], { count: last.count, target: last.target })
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
