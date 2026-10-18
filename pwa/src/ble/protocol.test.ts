import { describe, expect, test } from 'bun:test'
import {
  CHARACTERISTIC_UUID,
  Command,
  CONFIG_LENGTH,
  type DeviceConfig,
  decodeConfig,
  decodePresets,
  decodeState,
  decodeUint16,
  decodeUint8,
  encodeCommand,
  encodeConfig,
  encodePresets,
  encodeUint16,
  encodeUint8,
  SERVICE_UUID,
  State,
} from './protocol.ts'

const bytes = (buf: ArrayBuffer) => [...new Uint8Array(buf)]

describe('uuids', () => {
  test('share the base and number 01..07', () => {
    expect(SERVICE_UUID).toBe('8adb7600-5374-47c7-9127-d9895246807a')
    Object.values(CHARACTERISTIC_UUID).forEach((uuid, i) => {
      expect<string>(uuid).toBe(`8adb760${i + 1}-5374-47c7-9127-d9895246807a`)
    })
  })
})

describe('uint16', () => {
  test('is little-endian', () => {
    expect(bytes(encodeUint16(0x1234))).toEqual([0x34, 0x12])
  })

  test.each([0, 1, 300, 9999, 65535])('round-trips %d', (n) => {
    expect(decodeUint16(encodeUint16(n))).toBe(n)
  })

  test('decodes a DataView with an offset', () => {
    const buf = new Uint8Array([0xff, 0x2c, 0x01, 0xff]).buffer
    expect(decodeUint16(new DataView(buf, 1, 2))).toBe(300)
  })

  test('rejects the wrong length', () => {
    expect(() => decodeUint16(new ArrayBuffer(3))).toThrow()
  })
})

describe('uint8, command, state', () => {
  test.each([0, 1, 255])('round-trips %d', (n) => {
    expect(decodeUint8(encodeUint8(n))).toBe(n)
  })

  test('encodes commands', () => {
    expect(bytes(encodeCommand(Command.Stop))).toEqual([0])
    expect(bytes(encodeCommand(Command.Go))).toEqual([1])
    expect(bytes(encodeCommand(Command.TestFull))).toEqual([2])
    expect(bytes(encodeCommand(Command.TestSlow))).toEqual([3])
  })

  test('decodes every state', () => {
    for (const s of Object.values(State)) {
      expect(decodeState(encodeUint8(s))).toBe(s)
    }
  })

  test('rejects an unknown state', () => {
    expect(() => decodeState(encodeUint8(7))).toThrow()
  })
})

describe('presets', () => {
  test('round-trips the defaults', () => {
    const buf = encodePresets([30, 50, 120, 300])
    expect(buf.byteLength).toBe(8)
    expect(bytes(buf)).toEqual([30, 0, 50, 0, 120, 0, 0x2c, 0x01])
    expect(decodePresets(buf)).toEqual([30, 50, 120, 300])
  })

  test('rejects the wrong length', () => {
    expect(() => decodePresets(new ArrayBuffer(6))).toThrow()
  })
})

describe('config', () => {
  const defaults: DeviceConfig = {
    servoNeutralUs: 1500,
    speedFullOffsetUs: 300,
    speedSlowOffsetUs: 100,
    reverse: false,
    slowdownN: 4,
    jamTimeoutMs: 1500,
  }

  test('encodes the defaults byte for byte', () => {
    expect(bytes(encodeConfig(defaults))).toEqual([
      1, // version
      0xdc, 0x05, // 1500
      0x2c, 0x01, // 300
      0x64, 0x00, // 100
      0, // reverse
      4, // slowdown_n
      0xdc, 0x05, // 1500
    ])
  })

  test('round-trips the defaults', () => {
    const buf = encodeConfig(defaults)
    expect(buf.byteLength).toBe(CONFIG_LENGTH)
    expect(decodeConfig(buf)).toEqual(defaults)
  })

  test('round-trips negative offsets and reverse', () => {
    const config: DeviceConfig = {
      servoNeutralUs: 1480,
      speedFullOffsetUs: -300,
      speedSlowOffsetUs: -1,
      reverse: true,
      slowdownN: 10,
      jamTimeoutMs: 3000,
    }
    const buf = encodeConfig(config)
    expect(bytes(buf).slice(3, 7)).toEqual([0xd4, 0xfe, 0xff, 0xff])
    expect(decodeConfig(buf)).toEqual(config)
  })

  test('rejects the wrong length', () => {
    expect(() => decodeConfig(new ArrayBuffer(10))).toThrow(/expected 11 bytes/)
    expect(() => decodeConfig(new ArrayBuffer(12))).toThrow(/expected 11 bytes/)
  })

  test('rejects an unknown version', () => {
    const buf = encodeConfig(defaults)
    new DataView(buf).setUint8(0, 2)
    expect(() => decodeConfig(buf)).toThrow(/unsupported version 2/)
    new DataView(buf).setUint8(0, 0)
    expect(() => decodeConfig(buf)).toThrow(/unsupported version 0/)
  })
})
