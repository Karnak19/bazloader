// Device state as last read or notified by the ESP32. The store only changes from reads and
// notifications (see ble.ts): a write is a request, never an optimistic update.

import { useEffect, useState } from 'preact/hooks'
import type { DeviceConfig, Presets, State } from './protocol.ts'

export type Connection =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  // The device answered but speaks a config version this app can't decode.
  | 'incompatible'

export type DeviceState = {
  connection: Connection
  // Last connection or decode error, in plain words, for the UI to show. null when all is well.
  error: string | null
  deviceName: string | null
  // The values below are null until the first read after connecting.
  target: number | null
  count: number | null
  state: State | null
  // LiPo voltage in millivolts.
  battery: number | null
  presets: Presets | null
  config: DeviceConfig | null
}

export const initialDeviceState: DeviceState = {
  connection: 'disconnected',
  error: null,
  deviceName: null,
  target: null,
  count: null,
  state: null,
  battery: null,
  presets: null,
  config: null,
}

export type Store<T> = {
  get(): T
  set(patch: Partial<T>): void
  subscribe(listener: (value: T) => void): () => void
}

export function createStore<T>(initial: T): Store<T> {
  let value = initial
  const listeners = new Set<(value: T) => void>()
  return {
    get: () => value,
    set(patch) {
      value = { ...value, ...patch }
      for (const listener of listeners) listener(value)
    },
    subscribe(listener) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
      }
    },
  }
}

export type DeviceStore = Store<DeviceState>

export function createDeviceStore(): DeviceStore {
  return createStore(initialDeviceState)
}

// Re-renders the component on every store change.
export function useStore<T>(store: Store<T>): T {
  const [value, setValue] = useState(store.get)
  useEffect(() => {
    setValue(store.get())
    return store.subscribe(setValue)
  }, [store])
  return value
}
