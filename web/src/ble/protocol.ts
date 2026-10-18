// BLE protocol: UUIDs, enums and byte codecs.
// Must match web/src/content/docs/protocole-ble.md and firmware/src/ble_uuids.h.
// All integers are little-endian.

export const DEVICE_NAME = 'BULLOADER'

export const SERVICE_UUID = '8adb7600-5374-47c7-9127-d9895246807a'

export const CHARACTERISTIC_UUID = {
  target: '8adb7601-5374-47c7-9127-d9895246807a',
  command: '8adb7602-5374-47c7-9127-d9895246807a',
  count: '8adb7603-5374-47c7-9127-d9895246807a',
  state: '8adb7604-5374-47c7-9127-d9895246807a',
  battery: '8adb7605-5374-47c7-9127-d9895246807a',
  presets: '8adb7606-5374-47c7-9127-d9895246807a',
  config: '8adb7607-5374-47c7-9127-d9895246807a',
} as const

export const State = {
  Idle: 0,
  Running: 1,
  Slowdown: 2,
  Done: 3,
  Jam: 4,
  LowBatt: 5,
  Testing: 6,
} as const
export type State = (typeof State)[keyof typeof State]

export const Command = {
  Stop: 0,
  Go: 1,
  TestFull: 2,
  TestSlow: 3,
} as const
export type Command = (typeof Command)[keyof typeof Command]

export const TARGET_MIN = 1
export const TARGET_MAX = 9999
export const PRESET_COUNT = 4

export const CONFIG_VERSION = 1
export const CONFIG_LENGTH = 11

export type DeviceConfig = {
  servoNeutralUs: number
  speedFullOffsetUs: number
  speedSlowOffsetUs: number
  reverse: boolean
  slowdownN: number
  jamTimeoutMs: number
}

export type Presets = [number, number, number, number]

// Accepts what Web Bluetooth gives back (DataView) or what we build (ArrayBuffer).
type Bytes = DataView | ArrayBuffer

function view(bytes: Bytes): DataView {
  return bytes instanceof DataView ? bytes : new DataView(bytes)
}

function expectLength(v: DataView, length: number, what: string): void {
  if (v.byteLength !== length) {
    throw new RangeError(`${what}: expected ${length} bytes, got ${v.byteLength}`)
  }
}

// uint16: target, count, battery (mV)

export function encodeUint16(value: number): ArrayBuffer {
  const buf = new ArrayBuffer(2)
  new DataView(buf).setUint16(0, value, true)
  return buf
}

export function decodeUint16(bytes: Bytes): number {
  const v = view(bytes)
  expectLength(v, 2, 'uint16')
  return v.getUint16(0, true)
}

// uint8: state, command

export function encodeUint8(value: number): ArrayBuffer {
  const buf = new ArrayBuffer(1)
  new DataView(buf).setUint8(0, value)
  return buf
}

export function decodeUint8(bytes: Bytes): number {
  const v = view(bytes)
  expectLength(v, 1, 'uint8')
  return v.getUint8(0)
}

export function encodeCommand(command: Command): ArrayBuffer {
  return encodeUint8(command)
}

export function decodeState(bytes: Bytes): State {
  const value = decodeUint8(bytes)
  if (!(Object.values(State) as number[]).includes(value)) {
    throw new RangeError(`state: unknown value ${value}`)
  }
  return value as State
}

// presets: 4 × uint16

export function encodePresets(presets: Presets): ArrayBuffer {
  const buf = new ArrayBuffer(PRESET_COUNT * 2)
  const v = new DataView(buf)
  presets.forEach((p, i) => v.setUint16(i * 2, p, true))
  return buf
}

export function decodePresets(bytes: Bytes): Presets {
  const v = view(bytes)
  expectLength(v, PRESET_COUNT * 2, 'presets')
  return [v.getUint16(0, true), v.getUint16(2, true), v.getUint16(4, true), v.getUint16(6, true)]
}

// config: packed struct, v1, 11 bytes

export function encodeConfig(config: DeviceConfig): ArrayBuffer {
  const buf = new ArrayBuffer(CONFIG_LENGTH)
  const v = new DataView(buf)
  v.setUint8(0, CONFIG_VERSION)
  v.setUint16(1, config.servoNeutralUs, true)
  v.setInt16(3, config.speedFullOffsetUs, true)
  v.setInt16(5, config.speedSlowOffsetUs, true)
  v.setUint8(7, config.reverse ? 1 : 0)
  v.setUint8(8, config.slowdownN)
  v.setUint16(9, config.jamTimeoutMs, true)
  return buf
}

export function decodeConfig(bytes: Bytes): DeviceConfig {
  const v = view(bytes)
  expectLength(v, CONFIG_LENGTH, 'config')
  const version = v.getUint8(0)
  if (version !== CONFIG_VERSION) {
    throw new RangeError(`config: unsupported version ${version}`)
  }
  return {
    servoNeutralUs: v.getUint16(1, true),
    speedFullOffsetUs: v.getInt16(3, true),
    speedSlowOffsetUs: v.getInt16(5, true),
    reverse: v.getUint8(7) !== 0,
    slowdownN: v.getUint8(8),
    jamTimeoutMs: v.getUint16(9, true),
  }
}
