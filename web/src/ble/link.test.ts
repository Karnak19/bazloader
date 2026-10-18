import { describe, expect, test } from 'bun:test'
import { createBle } from './ble.ts'
import { FakeClock } from './fake-clock.ts'
import { findKnownDevice, WebBluetoothLink } from './link.ts'
import { CHARACTERISTIC_UUID, encodeConfig, encodePresets, encodeUint16, encodeUint8, State } from './protocol.ts'

// An EventTarget that counts the listeners currently attached, per event type.
class Counted extends EventTarget {
  readonly attached = new Map<string, number>()

  override addEventListener(type: string, listener: EventListenerOrEventListenerObject | null, options?: unknown): void {
    this.attached.set(type, (this.attached.get(type) ?? 0) + 1)
    super.addEventListener(type, listener, options as AddEventListenerOptions)
  }

  override removeEventListener(type: string, listener: EventListenerOrEventListenerObject | null): void {
    this.attached.set(type, (this.attached.get(type) ?? 0) - 1)
    super.removeEventListener(type, listener)
  }
}

class FakeCharacteristic extends Counted {
  value: DataView | null = null
  constructor(private bytes: ArrayBuffer) {
    super()
  }
  async readValue() {
    return new DataView(this.bytes.slice(0))
  }
  async writeValueWithResponse() {}
  async startNotifications() {
    return this
  }
  notify(bytes: ArrayBuffer) {
    this.value = new DataView(bytes)
    this.dispatchEvent(new Event('characteristicvaluechanged'))
  }
}

// A device whose GATT server hands back the very same characteristic objects on every connect,
// which Chrome may do.
function fakeDevice() {
  const values: Record<string, ArrayBuffer> = {
    target: encodeUint16(50),
    command: new ArrayBuffer(1),
    count: encodeUint16(0),
    state: encodeUint8(State.Idle),
    battery: encodeUint16(7900),
    presets: encodePresets([30, 50, 120, 300]),
    config: encodeConfig({
      servoNeutralUs: 1500,
      speedFullOffsetUs: 300,
      speedSlowOffsetUs: 100,
      reverse: false,
      slowdownN: 4,
      jamTimeoutMs: 1500,
    }),
  }
  const characteristics = new Map<string, FakeCharacteristic>(
    Object.entries(CHARACTERISTIC_UUID).map(([name, uuid]) => [uuid, new FakeCharacteristic(values[name]!)]),
  )
  const service = { getCharacteristic: async (uuid: string) => characteristics.get(uuid)! }
  const device = new Counted() as Counted & { name: string; gatt: unknown }
  const gatt = {
    connected: false,
    async connect() {
      gatt.connected = true
      return { getPrimaryService: async () => service }
    },
    disconnect() {
      if (!gatt.connected) return
      gatt.connected = false
      device.dispatchEvent(new Event('gattserverdisconnected'))
    },
  }
  device.name = 'BULLOADER'
  device.gatt = gatt
  const count = characteristics.get(CHARACTERISTIC_UUID.count)!
  return { device, gatt, count }
}

describe('WebBluetoothLink across reconnects', () => {
  test('each notification is handled once, however many times the link reconnected', async () => {
    const { device, gatt, count } = fakeDevice()
    const link = new WebBluetoothLink(device as unknown as BluetoothDevice)
    const ble = createBle({ request: async () => link })
    await ble.connect()
    expect(ble.store.get().connection).toBe('connected')

    for (let i = 0; i < 4; i++) {
      // The device drops (gattserverdisconnected), then we open the same link again.
      gatt.connected = true
      gatt.disconnect()
      expect(ble.store.get().connection).toBe('disconnected')
      await ble.open(link)
      expect(ble.store.get().connection).toBe('connected')
    }

    expect(count.attached.get('characteristicvaluechanged')).toBe(1)
    expect(device.attached.get('gattserverdisconnected')).toBe(1)

    let updates = 0
    ble.store.subscribe(() => updates++)
    count.notify(encodeUint16(12))
    expect(ble.store.get().count).toBe(12)
    expect(updates).toBe(1)
  })

  test('disconnect() takes the notification handlers off', async () => {
    const { device, count } = fakeDevice()
    const link = new WebBluetoothLink(device as unknown as BluetoothDevice)
    await link.connect()
    await link.subscribe('count', () => {})
    expect(count.attached.get('characteristicvaluechanged')).toBe(1)
    link.disconnect()
    expect(count.attached.get('characteristicvaluechanged')).toBe(0)
  })

  test('onDisconnect listeners come and go without piling up on the device', () => {
    const { device, gatt } = fakeDevice()
    const link = new WebBluetoothLink(device as unknown as BluetoothDevice)
    let calls = 0
    const offs = [1, 2, 3].map(() => link.onDisconnect(() => calls++))
    for (const off of offs.slice(0, 2)) off()
    gatt.connected = true
    gatt.disconnect()
    expect(calls).toBe(1)
    expect(device.attached.get('gattserverdisconnected')).toBe(1)
  })
})

// A known device that can watch advertisements; `advertise()` makes it show up.
function knownDevice(name = 'BULLOADER') {
  const device = new EventTarget() as EventTarget & {
    name: string
    watchAdvertisements: (options: { signal: AbortSignal }) => Promise<void>
    signal: AbortSignal | null
    advertise: () => void
  }
  device.name = name
  device.signal = null
  device.watchAdvertisements = async ({ signal }) => {
    device.signal = signal
  }
  device.advertise = () => device.dispatchEvent(new Event('advertisementreceived'))
  return device
}

describe('findKnownDevice', () => {
  test('no Web Bluetooth, or no getDevices: null straight away', async () => {
    const clock = new FakeClock()
    expect(await findKnownDevice({ bluetooth: undefined, timeoutMs: 1000, clock })).toBeNull()
    expect(await findKnownDevice({ bluetooth: {}, timeoutMs: 1000, clock })).toBeNull()
    expect(clock.pending).toBe(0)
  })

  test('getDevices without watchAdvertisements: null, nothing watched', async () => {
    const clock = new FakeClock()
    let asked = false
    const bluetooth = {
      getDevices: async () => {
        asked = true
        return [{ name: 'BULLOADER' }] as unknown as BluetoothDevice[]
      },
    }
    expect(await findKnownDevice({ bluetooth, timeoutMs: 1000, clock })).toBeNull()
    expect(asked).toBe(true)
    expect(clock.pending).toBe(0)
  })

  test('a getDevices that throws (flag off, permission) is a null too', async () => {
    const bluetooth = {
      getDevices: async (): Promise<BluetoothDevice[]> => {
        throw new Error('NotSupportedError')
      },
    }
    expect(await findKnownDevice({ bluetooth, timeoutMs: 1000, clock: new FakeClock() })).toBeNull()
  })

  test('waits for the known device to advertise, then stops watching', async () => {
    const clock = new FakeClock()
    const device = knownDevice()
    const bluetooth = { getDevices: async () => [device] as unknown as BluetoothDevice[] }
    const found = findKnownDevice({ bluetooth, timeoutMs: 30_000, clock })
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(device.signal?.aborted).toBe(false)
    device.advertise()
    expect((await found) as unknown).toBe(device)
    expect(device.signal?.aborted).toBe(true)
    expect(clock.pending).toBe(0)
  })

  test('gives up after the timeout and stops watching', async () => {
    const clock = new FakeClock()
    const device = knownDevice()
    const bluetooth = { getDevices: async () => [device] as unknown as BluetoothDevice[] }
    const found = findKnownDevice({ bluetooth, timeoutMs: 30_000, clock })
    await new Promise((resolve) => setTimeout(resolve, 0))
    clock.advance(30_000)
    expect(await found).toBeNull()
    expect(device.signal?.aborted).toBe(true)
  })

  test('an abort from the caller stops it too', async () => {
    const clock = new FakeClock()
    const device = knownDevice()
    const bluetooth = { getDevices: async () => [device] as unknown as BluetoothDevice[] }
    const controller = new AbortController()
    const found = findKnownDevice({ bluetooth, timeoutMs: 30_000, clock, signal: controller.signal })
    await new Promise((resolve) => setTimeout(resolve, 0))
    controller.abort()
    expect(await found).toBeNull()
    expect(device.signal?.aborted).toBe(true)
    expect(clock.pending).toBe(0)
  })
})
