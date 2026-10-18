import { describe, expect, test } from 'bun:test'
import { createBle } from './ble.ts'
import { FakeClock } from './fake-clock.ts'
import type { DeviceLink } from './link.ts'
import { MockDevice, type MockOptions } from './mock.ts'
import { State } from './protocol.ts'
import { createReconnect, defaultTiming, type Phase } from './reconnect.ts'

async function setup(options: MockOptions = {}, findKnown?: (signal: AbortSignal) => Promise<DeviceLink | null>) {
  const clock = new FakeClock()
  const device = new MockDevice({ clock, tickMs: 10, ...options })
  let connects = 0
  const connect = device.connect.bind(device)
  device.connect = () => {
    connects++
    return connect()
  }
  const ble = createBle({ request: async () => device })
  const reconnect = createReconnect({ ble, clock, findKnown })
  const phases: Phase[] = []
  reconnect.store.subscribe((r) => phases.push(r.phase))
  return { ble, device, clock, reconnect, phases, connects: () => connects }
}

describe('reconnect after a drop', () => {
  test('connected → reconnecting → connected, values kept meanwhile', async () => {
    const { ble, device, clock, reconnect, phases } = await setup()
    await ble.connect()
    device.simulateDisconnect(3000)
    expect(reconnect.store.get().phase).toBe('reconnecting')
    expect(ble.store.get().connection).not.toBe('connected')
    // Last values stay for the greyed-out screen.
    expect(ble.store.get().target).toBe(50)
    await clock.run(2900)
    expect(reconnect.store.get().phase).toBe('reconnecting')
    await clock.run(500)
    expect(ble.store.get().connection).toBe('connected')
    expect(reconnect.store.get().phase).toBe('off')
    expect(phases).toEqual(['reconnecting', 'off'])
  })

  test('a device that is back fast is reconnected on the first attempts', async () => {
    const { ble, device, clock } = await setup()
    await ble.connect()
    device.simulateDisconnect()
    await clock.run(100)
    expect(ble.store.get().connection).toBe('connected')
  })

  test('everything is read again: a run that finished while away shows as finished', async () => {
    const { ble, device, clock } = await setup()
    await ble.connect()
    await ble.setTarget(50)
    await ble.go()
    clock.advance(100)
    expect(ble.store.get().count).toBe(10)
    device.simulateDisconnect(1000)
    // The run goes on without us: 50 BBs × 10 ms.
    await clock.run(1200)
    expect(ble.store.get().connection).toBe('connected')
    expect(ble.store.get().state).toBe(State.Done)
    expect(ble.store.get().count).toBe(50)
    // And notifications flow again.
    await clock.run(2000)
    expect(ble.store.get().state).toBe(State.Idle)
  })

  test('gives up after the time limit and stops trying', async () => {
    const { ble, device, clock, reconnect, connects } = await setup()
    await ble.connect()
    device.simulateDisconnect(Number.POSITIVE_INFINITY)
    await clock.run(defaultTiming.giveUpMs - 100)
    expect(reconnect.store.get().phase).toBe('reconnecting')
    await clock.run(200)
    expect(reconnect.store.get().phase).toBe('gaveup')
    expect(ble.store.get().connection).toBe('disconnected')
    const tried = connects()
    // First connect plus a handful of retries, not a tight loop.
    expect(tried).toBeGreaterThan(2)
    expect(tried).toBeLessThan(10)
    await clock.run(120_000, 1000)
    expect(connects()).toBe(tried)
    expect(clock.pending).toBe(0)
    expect(reconnect.store.get().phase).toBe('gaveup')
  })

  test('attempts that fail fast follow the backoff, not a busy loop', async () => {
    const { ble, device, clock, reconnect, connects } = await setup()
    await ble.connect()
    // Out of range and every attempt refused at once.
    device.connect = async () => {
      throw new Error('GATT Server is disconnected')
    }
    let attempts = 0
    const connect = device.connect
    device.connect = () => {
      attempts++
      return connect()
    }
    device.simulateDisconnect()
    await clock.run(defaultTiming.giveUpMs + 1000)
    expect(reconnect.store.get().phase).toBe('gaveup')
    // 0, 0.5, 1.5, 3.5, 7.5, then every 5 s until 30 s: 0 + 4 + 5 = about 10.
    expect(attempts).toBeGreaterThanOrEqual(8)
    expect(attempts).toBeLessThanOrEqual(11)
    expect(connects()).toBe(1)
  })

  test('« Reconnecter » after giving up tries the same device again', async () => {
    const { ble, device, clock, reconnect } = await setup()
    await ble.connect()
    device.simulateDisconnect(Number.POSITIVE_INFINITY)
    await clock.run(defaultTiming.giveUpMs + 100)
    expect(reconnect.store.get().phase).toBe('gaveup')
    device.comeBack()
    reconnect.retry()
    expect(reconnect.store.get().phase).toBe('reconnecting')
    await clock.run(100)
    expect(ble.store.get().connection).toBe('connected')
    expect(reconnect.store.get().phase).toBe('off')
  })

  test('the device coming back during a slow attempt connects at once', async () => {
    const { ble, device, clock } = await setup()
    await ble.connect()
    device.simulateDisconnect(Number.POSITIVE_INFINITY)
    await clock.run(2000) // an attempt is hanging
    device.comeBack()
    await clock.run(50)
    expect(ble.store.get().connection).toBe('connected')
  })

  test('the user disconnecting is not a drop: no retries', async () => {
    const { ble, clock, reconnect, connects } = await setup()
    await ble.connect()
    reconnect.disconnect()
    await clock.run(5000)
    expect(reconnect.store.get().phase).toBe('off')
    expect(ble.store.get().connection).toBe('disconnected')
    expect(connects()).toBe(1)
  })

  test('leaving while reconnecting stops the retries', async () => {
    const { ble, device, clock, reconnect, connects } = await setup()
    await ble.connect()
    device.simulateDisconnect(Number.POSITIVE_INFINITY)
    await clock.run(1000)
    reconnect.disconnect()
    const tried = connects()
    await clock.run(60_000, 1000)
    expect(connects()).toBe(tried)
    expect(reconnect.store.get().phase).toBe('off')
  })

  test('drops again after a reconnect are retried too', async () => {
    const { ble, device, clock, reconnect } = await setup()
    await ble.connect()
    for (let i = 0; i < 3; i++) {
      device.simulateDisconnect(500)
      expect(reconnect.store.get().phase).toBe('reconnecting')
      await clock.run(2000)
      expect(ble.store.get().connection).toBe('connected')
    }
  })

  test('notifications are handled once after several reconnects', async () => {
    const { ble, device, clock } = await setup()
    await ble.connect()
    for (let i = 0; i < 3; i++) {
      device.simulateDisconnect(200)
      await clock.run(1000)
    }
    let updates = 0
    ble.store.subscribe(() => updates++)
    await ble.setTarget(77)
    expect(ble.store.get().target).toBe(77)
    expect(updates).toBe(1)
  })
})

describe('start-up search', () => {
  test('opens the known device it finds, without the picker', async () => {
    const clock = new FakeClock()
    const device = new MockDevice({ clock })
    let picked = false
    const ble = createBle({
      request: async () => {
        picked = true
        return device
      },
    })
    const reconnect = createReconnect({ ble, clock, findKnown: async () => device })
    await reconnect.start()
    expect(ble.store.get().connection).toBe('connected')
    expect(picked).toBe(false)
    expect(reconnect.store.get().phase).toBe('off')
  })

  test('nothing known: back to the button, silently', async () => {
    const clock = new FakeClock()
    const ble = createBle({ request: async () => new MockDevice({ clock }) })
    const reconnect = createReconnect({ ble, clock, findKnown: async () => null })
    await reconnect.start()
    expect(ble.store.get().connection).toBe('disconnected')
    expect(ble.store.get().error).toBeNull()
    expect(reconnect.store.get().phase).toBe('off')
  })

  test('tapping « Connecter » stops the search', async () => {
    const clock = new FakeClock()
    const device = new MockDevice({ clock })
    const ble = createBle({ request: async () => device })
    let aborted = false
    let found: (link: DeviceLink | null) => void = () => {}
    const reconnect = createReconnect({
      ble,
      clock,
      findKnown: (signal) =>
        new Promise((resolve) => {
          found = resolve
          signal.addEventListener('abort', () => {
            aborted = true
          })
        }),
    })
    const started = reconnect.start()
    expect(reconnect.store.get().phase).toBe('searching')
    reconnect.stopSearch()
    expect(aborted).toBe(true)
    expect(reconnect.store.get().phase).toBe('off')
    // A late answer from the search is ignored.
    found(device)
    await started
    expect(ble.store.get().connection).toBe('disconnected')
  })
})
