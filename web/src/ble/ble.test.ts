import { describe, expect, test } from 'bun:test'
import { createBle } from './ble.ts'
import type { CharacteristicName, DeviceLink } from './link.ts'
import { mockOptionsFromUrl } from './link.ts'
import { FakeClock } from './fake-clock.ts'
import { MockDevice, type MockOptions } from './mock.ts'
import { encodeConfig, encodePresets, encodeUint16, encodeUint8, State } from './protocol.ts'
import { createQueue } from './queue.ts'

async function connectMock(options: MockOptions = {}) {
  const clock = new FakeClock()
  const device = new MockDevice({ clock, tickMs: 10, ...options })
  const ble = createBle({ request: async () => device })
  await ble.connect()
  return { ble, device, clock, store: ble.store }
}

// Every distinct (state, count) the store goes through.
function record(store: ReturnType<typeof createBle>['store']) {
  const states: State[] = []
  const counts: number[] = []
  store.subscribe((s) => {
    if (s.state !== null && states.at(-1) !== s.state) states.push(s.state)
    if (s.count !== null && counts.at(-1) !== s.count) counts.push(s.count)
  })
  return { states, counts }
}

const tick = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('queue', () => {
  test('never runs two operations at once, and keeps their order', async () => {
    const queue = createQueue()
    let active = 0
    let maxActive = 0
    const order: number[] = []
    const op = (i: number, ms: number) => async () => {
      active++
      maxActive = Math.max(maxActive, active)
      await new Promise((resolve) => setTimeout(resolve, ms))
      order.push(i)
      active--
      return i
    }
    const results = await Promise.all([op(0, 5), op(1, 1), op(2, 3), op(3, 0)].map((o) => queue.run(o)))
    expect(maxActive).toBe(1)
    expect(order).toEqual([0, 1, 2, 3])
    expect(results).toEqual([0, 1, 2, 3])
  })

  test('keeps going after a failed operation', async () => {
    const queue = createQueue()
    const failed = queue.run(async () => {
      throw new Error('GATT operation failed')
    })
    const next = queue.run(async () => 'ok')
    await expect(failed).rejects.toThrow('GATT operation failed')
    expect(await next).toBe('ok')
  })

  test('the client never overlaps GATT operations, even when called all at once', async () => {
    let active = 0
    let maxActive = 0
    const values: Record<string, ArrayBuffer> = {
      config: encodeConfig({
        servoNeutralUs: 1500,
        speedFullOffsetUs: 300,
        speedSlowOffsetUs: 100,
        reverse: false,
        slowdownN: 4,
        jamTimeoutMs: 1500,
      }),
      target: encodeUint16(50),
      count: encodeUint16(0),
      state: encodeUint8(State.Idle),
      battery: encodeUint16(7900),
      presets: encodePresets([30, 50, 120, 300]),
    }
    const slow = async <T>(value: T): Promise<T> => {
      active++
      maxActive = Math.max(maxActive, active)
      await new Promise((resolve) => setTimeout(resolve, 1))
      active--
      return value
    }
    const link: DeviceLink = {
      name: 'busy',
      connect: () => slow(undefined),
      disconnect: () => {},
      read: (name: CharacteristicName) => slow(new DataView(values[name]!.slice(0))),
      write: () => slow(undefined),
      subscribe: () => slow(undefined),
      onDisconnect: () => () => {},
    }
    const ble = createBle({ request: async () => link })
    await ble.connect()
    expect(ble.store.get().connection).toBe('connected')
    await Promise.all([
      ble.setTarget(100),
      ble.go(),
      ble.stop(),
      ble.testSpin('slow'),
      ble.writePresets([10, 20, 30, 40]),
    ])
    expect(maxActive).toBe(1)
  })
})

describe('connect', () => {
  test('reads every value from the mock and ends connected', async () => {
    const { store } = await connectMock({ target: 120, battery: 8100 })
    const s = store.get()
    expect(s.connection).toBe('connected')
    expect(s.error).toBeNull()
    expect(s.deviceName).toBe('BazLoader (mock)')
    expect(s.target).toBe(120)
    expect(s.count).toBe(0)
    expect(s.state).toBe(State.Idle)
    expect(s.battery).toBe(8100)
    expect(s.presets).toEqual([30, 50, 120, 300])
    expect(s.config?.slowdownN).toBe(4)
  })

  test('an unknown config version shows as incompatible firmware, not a crash', async () => {
    const { store, ble } = await connectMock({ configVersion: 2 })
    const s = store.get()
    expect(s.connection).toBe('incompatible')
    expect(s.error).toContain('Incompatible firmware')
    expect(s.config).toBeNull()
    await expect(ble.go()).rejects.toThrow()
  })

  test('a cancelled device picker leaves the store disconnected with the reason', async () => {
    const ble = createBle({
      request: async () => {
        throw new Error('User cancelled the requestDevice() chooser.')
      },
    })
    await ble.connect()
    expect(ble.store.get().connection).toBe('disconnected')
    expect(ble.store.get().error).toContain('cancelled')
  })

  test('a dropped connection (gattserverdisconnected) shows as disconnected, link kept', async () => {
    const { store, device, ble } = await connectMock()
    device.simulateDisconnect()
    expect(store.get().connection).toBe('disconnected')
    expect(ble.link).toBe(device)
    // Values stay as last known; the next open replaces them.
    expect(store.get().target).toBe(50)
    await ble.open(device)
    expect(store.get().connection).toBe('connected')
  })

  test('disconnect() is clean and writes are refused afterwards', async () => {
    const { store, ble } = await connectMock()
    ble.disconnect()
    expect(store.get().connection).toBe('disconnected')
    expect(store.get().error).toBeNull()
    await expect(ble.setTarget(10)).rejects.toThrow('Not connected')
  })

  test('?mock in the URL picks the mock, with its variants', () => {
    expect(mockOptionsFromUrl('')).toBeNull()
    expect(mockOptionsFromUrl('?foo=1')).toBeNull()
    expect(mockOptionsFromUrl('?mock')).toEqual({})
    expect(mockOptionsFromUrl('?mock=jam')).toEqual({ jamAt: 7 })
    expect(mockOptionsFromUrl('?mock=v2')).toEqual({ configVersion: 2 })
    expect(mockOptionsFromUrl('?mock=drop')).toEqual({ dropAfterMs: 4000, awayMs: 6000 })
    expect(mockOptionsFromUrl('?mock=gone')?.awayMs).toBe(Number.POSITIVE_INFINITY)
  })
})

describe('mock run', () => {
  test('idle → running → slowdown at target − N → done → idle, with the right counts', async () => {
    const { ble, store, clock } = await connectMock()
    await ble.setTarget(10)
    expect(store.get().target).toBe(10)
    const seen = record(store)
    let slowdownAt = null as number | null
    store.subscribe((s) => {
      if (s.state === State.Slowdown && slowdownAt === null) slowdownAt = s.count
    })

    await ble.go()
    expect(store.get().state).toBe(State.Running)
    clock.advance(10 * 10)
    expect(store.get().state).toBe(State.Done)
    expect(store.get().count).toBe(10)
    clock.advance(2000)

    expect(seen.states).toEqual([State.Idle, State.Running, State.Slowdown, State.Done, State.Idle])
    expect(slowdownAt).toBe(6) // 10 − slowdown_n (4)
    expect(seen.counts).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    expect(store.get().state).toBe(State.Idle)
    expect(store.get().count).toBe(10)
  })

  test('honours a slowdown_n written to the config', async () => {
    const { ble, store, clock } = await connectMock()
    await ble.writeConfig({ ...store.get().config!, slowdownN: 2 })
    expect(store.get().config?.slowdownN).toBe(2)
    await ble.setTarget(5)
    let slowdownAt = null as number | null
    store.subscribe((s) => {
      if (s.state === State.Slowdown && slowdownAt === null) slowdownAt = s.count
    })
    await ble.go()
    clock.advance(100)
    expect(slowdownAt).toBe(3)
    expect(store.get().state).toBe(State.Done)
  })

  test('a target within slowdown_n starts slow straight away', async () => {
    const { ble, store, clock } = await connectMock()
    await ble.setTarget(3)
    const seen = record(store)
    await ble.go()
    clock.advance(30)
    expect(seen.states).toEqual([State.Idle, State.Slowdown, State.Done])
    expect(store.get().count).toBe(3)
  })

  test('jam: the feed stops, the run times out into JAM, stop goes back to idle', async () => {
    const { ble, store, clock } = await connectMock({ jamAt: 3 })
    await ble.setTarget(20)
    await ble.go()
    clock.advance(30)
    expect(store.get().count).toBe(3)
    expect(store.get().state).toBe(State.Running)
    clock.advance(1499)
    expect(store.get().state).toBe(State.Running)
    clock.advance(1)
    expect(store.get().state).toBe(State.Jam)
    expect(store.get().count).toBe(3)
    await ble.stop()
    expect(store.get().state).toBe(State.Idle)
  })

  test('stop mid-run goes idle and counting stops', async () => {
    const { ble, store, clock } = await connectMock()
    await ble.setTarget(50)
    await ble.go()
    clock.advance(50)
    await ble.stop()
    expect(store.get().state).toBe(State.Idle)
    clock.advance(1000)
    expect(store.get().count).toBe(5)
  })

  test('test spin goes to testing until stop', async () => {
    const { ble, store, clock } = await connectMock()
    for (const speed of ['full', 'slow'] as const) {
      await ble.testSpin(speed)
      clock.advance(10000)
      expect(store.get().state).toBe(State.Testing)
      await ble.stop()
      expect(store.get().state).toBe(State.Idle)
    }
  })

  test('a test spin is refused during a run', async () => {
    const { ble, store } = await connectMock()
    await ble.go()
    await ble.testSpin('slow')
    expect(store.get().state).toBe(State.Running)
  })
})

describe('store follows the device, never the request', () => {
  test('a target write during a run is ignored and the real value comes back', async () => {
    const { ble, store } = await connectMock()
    await ble.setTarget(30)
    await ble.go()
    await ble.setTarget(99)
    expect(store.get().target).toBe(30)
  })

  test('a write alone does not change the store', async () => {
    const { ble, store, device } = await connectMock()
    // A device that accepts the write but never notifies it back.
    const write = device.write.bind(device)
    device.write = async (name, value) => {
      if (name !== 'target') return write(name, value)
    }
    await ble.setTarget(77)
    expect(store.get().target).toBe(50)
  })

  test('target is clamped to 1–9999 before it is sent', async () => {
    const { ble, store } = await connectMock()
    await ble.setTarget(12000)
    expect(store.get().target).toBe(9999)
    await ble.setTarget(0)
    expect(store.get().target).toBe(1)
  })

  test('battery notifications update the store', async () => {
    const { store, clock } = await connectMock({ battery: 8000 })
    clock.advance(5000)
    expect(store.get().battery).toBe(7995)
  })

  test('config is read back after a write', async () => {
    const { ble, store } = await connectMock()
    const config = { ...store.get().config!, servoNeutralUs: 1485, speedFullOffsetUs: -250, reverse: true }
    await ble.writeConfig(config)
    expect(store.get().config).toEqual(config)
  })

  test('presets and config written during a run are ignored, the read-back shows the old ones', async () => {
    const { ble, store } = await connectMock()
    const before = store.get().config!
    await ble.go()
    await ble.writePresets([10, 20, 30, 40])
    await ble.writeConfig({ ...before, slowdownN: 9 })
    expect(store.get().presets).toEqual([30, 50, 120, 300])
    expect(store.get().config).toEqual(before)
  })

  test('presets are read back after a write', async () => {
    const { ble, store } = await connectMock()
    await ble.writePresets([10, 20, 30, 40])
    expect(store.get().presets).toEqual([10, 20, 30, 40])
  })

  test('a notification is decoded at once, so a reused buffer does not matter', async () => {
    let notifyCount: ((v: DataView) => void) | undefined
    const { ble, store, device } = await connectMock()
    // Re-open with a spy on the count listener.
    const subscribe = device.subscribe.bind(device)
    device.subscribe = async (name, listener) => {
      if (name === 'count') notifyCount = listener
      return subscribe(name, listener)
    }
    await ble.open(device)
    await tick()
    const buf = new DataView(new ArrayBuffer(2))
    buf.setUint16(0, 42, true)
    notifyCount!(buf)
    buf.setUint16(0, 999, true) // the browser reuses the buffer
    expect(store.get().count).toBe(42)
  })
})
