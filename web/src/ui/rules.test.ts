import { describe, expect, test } from 'bun:test'
import { State } from '../ble/protocol.ts'
import { batteryLevel, batteryText, canGo, connectionErrorText, parseTarget, progress } from './rules.ts'

describe('batteryLevel', () => {
  test('follows the firmware thresholds', () => {
    expect(batteryLevel(8400)).toBe('ok')
    expect(batteryLevel(7000)).toBe('ok')
    expect(batteryLevel(6999)).toBe('warn')
    expect(batteryLevel(6600)).toBe('warn')
    expect(batteryLevel(6599)).toBe('low')
    expect(batteryLevel(0)).toBe('usb')
  })

  test('formats volts the French way, USB for 0', () => {
    expect(batteryText(7412)).toBe('7,41 V')
    expect(batteryText(0)).toBe('USB')
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

describe('parseTarget', () => {
  test('reads digits and clamps to 1..9999', () => {
    expect(parseTarget('50')).toBe(50)
    expect(parseTarget(' 120 ')).toBe(120)
    expect(parseTarget('0')).toBe(1)
    expect(parseTarget('12000')).toBe(9999)
  })

  test('refuses anything else', () => {
    expect(parseTarget('')).toBeNull()
    expect(parseTarget('-3')).toBeNull()
    expect(parseTarget('4.5')).toBeNull()
    expect(parseTarget('abc')).toBeNull()
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

describe('connectionErrorText', () => {
  test('translates a closed picker', () => {
    expect(connectionErrorText('User cancelled the requestDevice() chooser.')).toBe('Aucun appareil choisi.')
  })
})
