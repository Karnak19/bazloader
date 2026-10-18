// The byte-level link to a device: either the real one over Web Bluetooth, or MockDevice.
// It only moves bytes. Decoding, the operation queue and the store live in ble.ts, so the mock and
// the real device go through exactly the same path.

import { type Clock, MockDevice, type MockOptions, realClock } from './mock.ts'
import { CHARACTERISTIC_UUID, SERVICE_UUID } from './protocol.ts'

export type CharacteristicName = keyof typeof CHARACTERISTIC_UUID

export type DeviceLink = {
  readonly name: string
  // Opens the GATT connection and finds the characteristics. Can be called again after a
  // disconnect to reconnect to the same device without asking the user to pick it again.
  connect(): Promise<void>
  // Closes the connection. Also aborts a connect() still in progress, which then rejects.
  disconnect(): void
  read(name: CharacteristicName): Promise<DataView>
  write(name: CharacteristicName, value: ArrayBuffer): Promise<void>
  // Starts notifications. The DataView handed to the listener may be reused by the browser once
  // the listener returns: decode it straight away. Subscribing again to the same characteristic
  // replaces the previous listener.
  subscribe(name: CharacteristicName, listener: (value: DataView) => void): Promise<void>
  // Called when the connection drops, whoever dropped it. Returns a function that stops listening.
  onDisconnect(listener: () => void): () => void
}

export class WebBluetoothLink implements DeviceLink {
  readonly device: BluetoothDevice
  private characteristics = new Map<CharacteristicName, BluetoothRemoteGATTCharacteristic>()
  // The one `characteristicvaluechanged` handler we put on each characteristic. After a reconnect
  // Chrome may hand back the very same characteristic objects, so a handler left on them would
  // fire next to the new one and every notification would be handled twice. connect(),
  // disconnect() and subscribe() take the old ones off first.
  private readonly handlers = new Map<
    CharacteristicName,
    { characteristic: BluetoothRemoteGATTCharacteristic; handler: () => void }
  >()
  // One `gattserverdisconnected` handler on the device for the link's whole life, however many
  // sessions come and go: onDisconnect only adds to this set.
  private readonly disconnectListeners = new Set<() => void>()

  constructor(device: BluetoothDevice) {
    this.device = device
    device.addEventListener('gattserverdisconnected', () => {
      for (const listener of [...this.disconnectListeners]) listener()
    })
  }

  get name(): string {
    return this.device.name ?? 'BULLOADER'
  }

  async connect(): Promise<void> {
    const gatt = this.device.gatt
    if (!gatt) throw new Error('GATT not available on this device')
    this.removeHandlers()
    const server = await gatt.connect()
    const service = await server.getPrimaryService(SERVICE_UUID)
    const characteristics = new Map<CharacteristicName, BluetoothRemoteGATTCharacteristic>()
    // One at a time: discovery calls are GATT operations too.
    for (const [name, uuid] of Object.entries(CHARACTERISTIC_UUID)) {
      characteristics.set(name as CharacteristicName, await service.getCharacteristic(uuid))
    }
    this.characteristics = characteristics
  }

  disconnect(): void {
    this.removeHandlers()
    this.device.gatt?.disconnect()
  }

  read(name: CharacteristicName): Promise<DataView> {
    return this.characteristic(name).readValue()
  }

  write(name: CharacteristicName, value: ArrayBuffer): Promise<void> {
    return this.characteristic(name).writeValueWithResponse(value)
  }

  async subscribe(name: CharacteristicName, listener: (value: DataView) => void): Promise<void> {
    const characteristic = this.characteristic(name)
    this.removeHandler(name)
    const handler = () => {
      if (characteristic.value) listener(characteristic.value)
    }
    characteristic.addEventListener('characteristicvaluechanged', handler)
    this.handlers.set(name, { characteristic, handler })
    await characteristic.startNotifications()
  }

  onDisconnect(listener: () => void): () => void {
    // Wrapped, so the same function registered twice gets two entries and two removals.
    const entry = () => listener()
    this.disconnectListeners.add(entry)
    return () => {
      this.disconnectListeners.delete(entry)
    }
  }

  private removeHandler(name: CharacteristicName): void {
    const old = this.handlers.get(name)
    if (!old) return
    old.characteristic.removeEventListener('characteristicvaluechanged', old.handler)
    this.handlers.delete(name)
  }

  private removeHandlers(): void {
    for (const name of [...this.handlers.keys()]) this.removeHandler(name)
  }

  private characteristic(name: CharacteristicName): BluetoothRemoteGATTCharacteristic {
    const characteristic = this.characteristics.get(name)
    if (!characteristic) throw new Error(`Characteristic ${name} not found: not connected?`)
    return characteristic
  }
}

// Looks for a device this site was already allowed to use and waits until it advertises, so the
// app can connect on start without the device picker. Needs navigator.bluetooth.getDevices() and
// BluetoothDevice.watchAdvertisements(); both are missing or behind a flag on some Android Chrome
// versions, and then this returns null straight away and the « Connecter » button is the way in.
// Also null after timeoutMs, or when `signal` aborts. Every watch is stopped before returning.
export async function findKnownDevice(options: {
  bluetooth: Partial<Pick<Bluetooth, 'getDevices'>> | undefined
  timeoutMs: number
  signal?: AbortSignal
  clock?: Clock
}): Promise<BluetoothDevice | null> {
  const { bluetooth, timeoutMs, signal } = options
  const clock = options.clock ?? realClock
  if (typeof bluetooth?.getDevices !== 'function') return null
  let devices: BluetoothDevice[]
  try {
    devices = await bluetooth.getDevices()
  } catch {
    return null
  }
  const known = devices.filter((d) => typeof d.watchAdvertisements === 'function')
  if (known.length === 0 || signal?.aborted) return null

  const watching = new AbortController()
  const stop = () => watching.abort()
  signal?.addEventListener('abort', stop)
  const timer = clock.setTimeout(stop, timeoutMs)
  try {
    return await new Promise<BluetoothDevice | null>((resolve) => {
      watching.signal.addEventListener('abort', () => resolve(null))
      for (const device of known) {
        device.addEventListener('advertisementreceived', () => resolve(device), { signal: watching.signal })
        device.watchAdvertisements({ signal: watching.signal }).catch(() => {
          // Not allowed, or Bluetooth off: this one just never shows up.
        })
      }
    })
  } finally {
    clock.clearTimeout(timer)
    stop()
    signal?.removeEventListener('abort', stop)
  }
}

// `?mock` in the URL swaps the real device for MockDevice. `?mock=jam` makes the mock jam during
// a run, `?mock=v2` makes it answer with a config version this app doesn't know. `?mock=drop`
// drops the link 4 s after connecting and comes back in range 6 s later; `?mock=gone` drops the
// same way and never comes back. `?mock=lowbatt` starts with a flat pack, so GO answers LOW_BATT.
export function mockOptionsFromUrl(search: string): MockOptions | null {
  const params = new URLSearchParams(search)
  if (!params.has('mock')) return null
  const mode = params.get('mock')
  if (mode === 'jam') return { jamAt: 7 }
  if (mode === 'v2') return { configVersion: 2 }
  if (mode === 'drop') return { dropAfterMs: 4000, awayMs: 6000 }
  if (mode === 'lowbatt') return { battery: 6500 }
  if (mode === 'gone') return { dropAfterMs: 4000, awayMs: Number.POSITIVE_INFINITY }
  return {}
}

export function isMockRequested(): boolean {
  return typeof location !== 'undefined' && mockOptionsFromUrl(location.search) !== null
}

// Asks the user to pick a device. Real Web Bluetooth requires this to run from a user gesture
// (a click handler), so call it first thing in the handler, before any other await.
export async function requestLink(): Promise<DeviceLink> {
  const mock = typeof location !== 'undefined' ? mockOptionsFromUrl(location.search) : null
  if (mock) return new MockDevice(mock)
  const device = await navigator.bluetooth.requestDevice({ filters: [{ services: [SERVICE_UUID] }] })
  return new WebBluetoothLink(device)
}

// The device to reconnect to on start, without the picker, or null (see findKnownDevice).
export async function knownLink(options: { timeoutMs: number; signal?: AbortSignal }): Promise<DeviceLink | null> {
  if (typeof navigator === 'undefined') return null
  const device = await findKnownDevice({ bluetooth: navigator.bluetooth, ...options })
  return device ? new WebBluetoothLink(device) : null
}
