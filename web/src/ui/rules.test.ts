import { describe, expect, test } from 'bun:test'
import { State } from '../ble/protocol.ts'
import {
  batteryLevel,
  batteryText,
  canEditSettings,
  canGo,
  connectionErrorText,
  canStep,
  countIsCurrent,
  goReloadsHint,
  type LastRun,
  lastRunText,
  motorMayRun,
  nextLastRun,
  readTarget,
  stateTone,
  progress,
  sendErrorText,
  stateLabel,
} from './rules.ts'

describe('batteryLevel', () => {
  test('follows the firmware thresholds', () => {
    expect(batteryLevel(8400)).toBe('ok')
    expect(batteryLevel(7000)).toBe('ok')
    expect(batteryLevel(6999)).toBe('warn')
    expect(batteryLevel(6600)).toBe('warn')
    expect(batteryLevel(6599)).toBe('low')
    expect(batteryLevel(0)).toBe('usb')
  })

  test('formats volts in each language, USB for 0', () => {
    expect(batteryText(7412, 'fr')).toBe('7,41\u00a0V')
    expect(batteryText(7900, 'fr')).toBe('7,90\u00a0V')
    expect(batteryText(7900, 'en')).toBe('7.90\u00a0V')
    expect(batteryText(0, 'fr')).toBe('USB')
    expect(batteryText(0, 'en')).toBe('USB')
  })
})

describe('canGo', () => {
  test('matches Run::go(): any state but a running one', () => {
    expect(canGo(State.Idle)).toBe(true)
    expect(canGo(State.Done)).toBe(true)
    expect(canGo(State.Jam)).toBe(true)
    expect(canGo(State.LowBatt)).toBe(true)
    expect(canGo(State.Testing)).toBe(true)
    expect(canGo(State.Running)).toBe(false)
    expect(canGo(State.Slowdown)).toBe(false)
    expect(canGo(null)).toBe(false)
  })
})

describe('canEditSettings', () => {
  test('only with the motor at rest', () => {
    expect(canEditSettings(State.Idle)).toBe(true)
    expect(canEditSettings(State.Done)).toBe(true)
    expect(canEditSettings(State.Jam)).toBe(true)
    expect(canEditSettings(State.LowBatt)).toBe(true)
    expect(canEditSettings(State.Running)).toBe(false)
    expect(canEditSettings(State.Slowdown)).toBe(false)
    expect(canEditSettings(State.Testing)).toBe(false)
    expect(canEditSettings(null)).toBe(false)
  })
})

describe('readTarget', () => {
  test('a number in range goes through as is', () => {
    expect(readTarget('50')).toEqual({ value: 50, note: null })
    expect(readTarget(' 120 ')).toEqual({ value: 120, note: null })
  })

  test('out of range is clamped, and says so', () => {
    expect(readTarget('0')).toEqual({ value: 1, note: 'min' })
    expect(readTarget('12000')).toEqual({ value: 9999, note: 'max' })
  })

  test('anything but digits sends nothing, and says so; empty says nothing', () => {
    expect(readTarget('')).toEqual({ value: null, note: null })
    expect(readTarget('-3')).toEqual({ value: null, note: 'notNumber' })
    expect(readTarget('4.5')).toEqual({ value: null, note: 'notNumber' })
    expect(readTarget('abc')).toEqual({ value: null, note: 'notNumber' })
  })
})

describe('canStep', () => {
  test('off at the ends of the range and with no target', () => {
    expect(canStep(1, -1)).toBe(false)
    expect(canStep(1, 1)).toBe(true)
    expect(canStep(9999, 1)).toBe(false)
    expect(canStep(9999, -1)).toBe(true)
    expect(canStep(null, 1)).toBe(false)
  })
})

describe('nextLastRun', () => {
  const at = (state: State, count: number, target = 50) => ({ state, count, target })

  test('a run that reaches DONE is a full mag, and keeps counting the overshoot', () => {
    let last = nextLastRun(null, State.Running, at(State.Done, 50))
    expect(last).toEqual({ end: 'done', count: 50, target: 50 })
    last = nextLastRun(last, State.Done, at(State.Done, 51))
    expect(last).toEqual({ end: 'done', count: 51, target: 50 })
    // Back to IDLE by itself: the result stays.
    expect(nextLastRun(last, State.Done, at(State.Idle, 51))).toEqual(last)
  })

  test('STOP, jam and a flat pack each end the run their own way', () => {
    expect(nextLastRun(null, State.Running, at(State.Idle, 13))).toEqual({ end: 'stopped', count: 13, target: 50 })
    expect(nextLastRun(null, State.Slowdown, at(State.Jam, 7))).toEqual({ end: 'jam', count: 7, target: 50 })
    expect(nextLastRun(null, State.Running, at(State.LowBatt, 20))).toEqual({
      end: 'lowBatt',
      count: 20,
      target: 50,
    })
    // Reached the target but the DONE notification was missed.
    expect(nextLastRun(null, State.Slowdown, at(State.Idle, 50))?.end).toBe('done')
  })

  test('a new run clears it; a stop from JAM keeps it', () => {
    const jam: LastRun = { end: 'jam', count: 7, target: 50 }
    expect(nextLastRun(jam, State.Idle, at(State.Running, 0))).toBeNull()
    expect(nextLastRun(jam, State.Jam, at(State.Idle, 7))).toEqual(jam)
  })

  test('no transition right after (re)connecting, and nothing from a test spin', () => {
    expect(nextLastRun(null, null, at(State.Idle, 13))).toBeNull()
    expect(nextLastRun(null, State.Testing, at(State.Idle, 0))).toBeNull()
  })
})

describe('goReloadsHint', () => {
  const stopped: LastRun = { end: 'stopped', count: 13, target: 50 }

  test('after a run cut short, GO loads the full target again', () => {
    expect(goReloadsHint(stopped, State.Idle, 50)).toBe(50)
    expect(goReloadsHint({ end: 'jam', count: 7, target: 50 }, State.Jam, 50)).toBe(50)
  })

  test('nothing after a full mag, during a run, or once the target changed', () => {
    expect(goReloadsHint({ end: 'done', count: 50, target: 50 }, State.Idle, 50)).toBeNull()
    expect(goReloadsHint(stopped, State.Running, 50)).toBeNull()
    expect(goReloadsHint(stopped, State.Idle, 30)).toBeNull()
    expect(goReloadsHint(null, State.Idle, 50)).toBeNull()
  })
})

describe('countIsCurrent', () => {
  test('live during a run and on DONE', () => {
    expect(countIsCurrent(State.Running, null, 50)).toBe(true)
    expect(countIsCurrent(State.Done, null, 50)).toBe(true)
  })

  test('at rest, only while the target is the one of the last run', () => {
    const last: LastRun = { end: 'stopped', count: 13, target: 50 }
    expect(countIsCurrent(State.Idle, last, 50)).toBe(true)
    expect(countIsCurrent(State.Idle, last, 1)).toBe(false)
    expect(countIsCurrent(State.Idle, null, 50)).toBe(false)
    expect(countIsCurrent(null, last, 50)).toBe(false)
  })
})

describe('motorMayRun / stateTone', () => {
  test('the motor turns in a run and in a test spin', () => {
    expect(motorMayRun(State.Running)).toBe(true)
    expect(motorMayRun(State.Slowdown)).toBe(true)
    expect(motorMayRun(State.Testing)).toBe(true)
    expect(motorMayRun(State.Idle)).toBe(false)
    expect(motorMayRun(State.Jam)).toBe(false)
    expect(motorMayRun(null)).toBe(false)
  })

  test('running and slowing down look different', () => {
    expect(stateTone(State.Running)).not.toBe(stateTone(State.Slowdown))
    expect(stateTone(State.Done)).toBe('ok')
    expect(stateTone(State.Jam)).toBe('alarm')
    expect(stateTone(null)).toBe('idle')
  })
})

describe('lastRunText', () => {
  test('says how the last run ended, in each language', () => {
    expect(lastRunText({ end: 'done', count: 50, target: 50 }, 'en')).toContain('50 / 50')
    expect(lastRunText({ end: 'stopped', count: 13, target: 50 }, 'fr')).toContain('13 / 50')
    expect(lastRunText({ end: 'jam', count: 7, target: 50 }, 'en')).toContain('7 / 50')
  })
})

describe('progress', () => {
  test('is count / target, capped at 1', () => {
    expect(progress(25, 50)).toBe(0.5)
    expect(progress(53, 50)).toBe(1)
    expect(progress(null, 50)).toBe(0)
    expect(progress(3, null)).toBe(0)
  })
})

describe('stateLabel', () => {
  // The French labels are the OLED's (firmware/src/screen.cpp), so the phone and the device match.
  test('French matches the OLED', () => {
    expect(stateLabel(State.Idle, 'fr')).toBe('Prêt')
    expect(stateLabel(State.Running, 'fr')).toBe('Chargement')
    expect(stateLabel(State.Slowdown, 'fr')).toBe('Ralenti')
    expect(stateLabel(State.Done, 'fr')).toBe('Terminé')
    expect(stateLabel(State.Jam, 'fr')).toBe('Bourrage / trémie vide')
    expect(stateLabel(State.LowBatt, 'fr')).toBe('Batterie faible')
    expect(stateLabel(State.Testing, 'fr')).toBe('Test moteur')
  })

  test('English has its own words', () => {
    expect(stateLabel(State.Idle, 'en')).toBe('Ready')
    expect(stateLabel(State.Jam, 'en')).toBe('Jam / hopper empty')
  })
})

describe('connectionErrorText', () => {
  test('translates a closed picker', () => {
    const error = 'User cancelled the requestDevice() chooser.'
    expect(connectionErrorText(error, 'fr')).toBe('Aucun appareil choisi.')
    expect(connectionErrorText(error, 'en')).toBe('No device picked.')
  })

  test('says Bluetooth is off in plain words', () => {
    expect(connectionErrorText('Bluetooth adapter not available.', 'fr')).toBe('Le Bluetooth du téléphone est désactivé.')
  })

  test('passes other errors through, with French typography', () => {
    expect(connectionErrorText('GATT Server is disconnected', 'fr')).toBe('Connexion impossible\u00a0: GATT Server is disconnected')
    expect(connectionErrorText('GATT Server is disconnected', 'en')).toBe("Couldn't connect: GATT Server is disconnected")
  })
})

describe('sendErrorText', () => {
  test('says the BLE layer\'s "Not connected" in the language', () => {
    expect(sendErrorText('Not connected', 'fr')).toBe("Échec de l'envoi\u00a0: Pas connecté.")
    expect(sendErrorText('Not connected', 'en')).toBe("Couldn't send: Not connected.")
    expect(sendErrorText('GATT operation failed', 'en')).toBe("Couldn't send: GATT operation failed")
  })
})
