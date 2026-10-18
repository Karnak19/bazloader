// The byte-level link to a device: either the real one over Web Bluetooth, or MockDevice.
// It only moves bytes. Decoding, the operation queue and the store live in ble.ts, so the mock and
// the real device go through exactly the same path.

import { CHARACTERISTIC_UUID, SERVICE_UUID } from './protocol.ts'
import { MockDevice, type MockOptions } from './mock.ts'

export type CharacteristicName = keyof typeof CHARACTERISTIC_UUID

export type DeviceLink = {
  readonly name: string
  // Opens the GATT connection and finds the characteristics. Can be called again after a
  // disconnect to reconnect to the same device without asking the user to pick it again.
  connect(): Promise<void>
  disconnect(): void
  read(name: CharacteristicName): Promise<DataView>
  write(name: CharacteristicName, value: ArrayBuffer): Promise<void>
  // Starts notifications. The DataView handed to the listener may be reused by the browser once
  // the listener returns: decode it straight away.
  subscribe(name: CharacteristicName, listener: (value: DataView) => void): Promise<void>
  // Called when the connection drops, whoever dropped it. Returns a function that stops listening.
  onDisconnect(listener: () => void): () => void
}

export class WebBluetoothLink implements DeviceLink {
  readonly device: BluetoothDevice
  private characteristics = new Map<CharacteristicName, BluetoothRemoteGATTCharacteristic>()

  constructor(device: BluetoothDevice) {
    this.device = device
  }

  get name(): string {
    return this.device.name ?? 'BULLOADER'
  }

  async connect(): Promise<void> {
    const gatt = this.device.gatt
    if (!gatt) throw new Error('GATT indisponible sur cet appareil')
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
    characteristic.addEventListener('characteristicvaluechanged', () => {
      if (characteristic.value) listener(characteristic.value)
    })
    await characteristic.startNotifications()
  }

  onDisconnect(listener: () => void): () => void {
    this.device.addEventListener('gattserverdisconnected', listener)
    return () => this.device.removeEventListener('gattserverdisconnected', listener)
  }

  private characteristic(name: CharacteristicName): BluetoothRemoteGATTCharacteristic {
    const characteristic = this.characteristics.get(name)
    if (!characteristic) throw new Error(`Caractéristique ${name} introuvable, pas connecté ?`)
    return characteristic
  }
}

// `?mock` in the URL swaps the real device for MockDevice. `?mock=jam` makes the mock jam during
// a run, `?mock=v2` makes it answer with a config version this app doesn't know.
export function mockOptionsFromUrl(search: string): MockOptions | null {
  const params = new URLSearchParams(search)
  if (!params.has('mock')) return null
  const mode = params.get('mock')
  if (mode === 'jam') return { jamAt: 7 }
  if (mode === 'v2') return { configVersion: 2 }
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
