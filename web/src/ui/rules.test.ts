import { describe, expect, test } from 'bun:test'
import { State } from '../ble/protocol.ts'
import {
  batteryLevel,
  batteryText,
  canEditSettings,
  canGo,
  connectionErrorText,
  parseTarget,
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
