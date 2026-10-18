// The app in English. Same keys as fr.ts, enforced by the type: a missing or extra key fails tsc.
// Written as English, not as a word-for-word copy of the French.

import type { fr } from './fr.ts'

export const en: Record<keyof typeof fr, string> = {
  'lang.title': 'Language',

  'app.noBluetooth': "Web Bluetooth isn't available. Use Chrome on Android.",

  'banner.reconnecting': 'Disconnected — reconnecting…',
  'banner.lost': 'Connection lost. Turn the BULLOADER back on or move closer.',
  'banner.retry': 'Reconnect',
  'banner.changeDevice': 'Change device',

  'connect.button': 'Connect',
  'connect.busy': 'Connecting…',
  'connect.searching': 'Looking for the BULLOADER you used before…',
  'connect.incompatible': 'Incompatible firmware: update the app or the BULLOADER.',
  'connect.mock': 'Demo mode (?mock): no real device.',

  // The OLED stays in French; these say the same thing in English.
  'state.idle': 'Ready',
  'state.running': 'Loading',
  'state.slowdown': 'Slowing down',
  'state.done': 'Done',
  'state.jam': 'Jam / hopper empty',
  'state.lowBatt': 'Low battery',
  'state.testing': 'Motor test',

  'main.settings': 'Settings',
  'main.disconnect': 'Disconnect',
  'main.target': 'Target',
  'main.minusOne': 'Minus one',
  'main.plusOne': 'Plus one',

  'error.cancelled': 'No device picked.',
  'error.bluetoothOff': "The phone's Bluetooth is off.",
  'error.connect': "Couldn't connect: {error}",
  'error.notConnected': 'Not connected.',
  'error.send': "Couldn't send: {error}",

  'settings.title': 'Settings',
  'settings.back': 'Back',
  'settings.incompatible': 'Incompatible firmware: settings unavailable. Update the app or the BULLOADER.',
  'settings.presets': 'Presets',
  'settings.preset': 'Preset {n}',
  'settings.presetError': 'Preset {n}: {error}',
  'settings.loading': 'Loading',
  'settings.slowdown': 'Slow down N BBs before the end',
  'settings.jam': 'Jam after (ms with no BB)',
  'settings.servo': 'Servo',
  'settings.neutral': 'Neutral (µs)',
  'settings.minusUs': 'Minus {n} µs',
  'settings.plusUs': 'Plus {n} µs',
  'settings.fullOffset': 'Fast speed offset (µs)',
  'settings.slowOffset': 'Slow speed offset (µs)',
  'settings.reverse': 'Reverse direction',
  'settings.yes': 'ON',
  'settings.no': 'OFF',
  'settings.fixErrors': 'Fix the values in red to save.',
  'settings.motorRunning': 'Motor running: stop it to save or test.',
  'settings.save': 'Save',
  'settings.saving': 'Saving…',
  'settings.saved': 'Saved.',
  'settings.notKept': "The device didn't take everything: these are its values.",
  'settings.motorTest': 'Motor test',
  'settings.testOffline': 'Connection lost: the BULLOADER stops the motor by itself.',
  'settings.testRunning': 'Test running: the motor is spinning.',
  'settings.testSavesFirst': 'Each test saves your changes first.',
  'settings.testSaved': 'Spins with the saved values.',
  'settings.testFull': 'Test fast',
  'settings.testSlow': 'Test slow',

  'validation.integer': 'Whole number expected, between {min} and {max}{unit}.',
  'validation.range': 'Must be between {min} and {max}{unit}.',
}
