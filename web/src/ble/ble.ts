// The one module that talks to the device. Screens call these functions and read the store; they
// never touch Web Bluetooth.
//
// The ESP32 owns the state. The store changes only from reads and notifications; every write here
// is a request, and the device answers with a notification (target, count, state) or we read the
// value back (presets, config, which don't notify).

import type { DeviceLink } from './link.ts'
import {
  Command,
  type DeviceConfig,
  decodeConfig,
  decodePresets,
  decodeState,
  decodeUint16,
  encodeCommand,
  encodeConfig,
  encodePresets,
  encodeUint16,
  type Presets,
  TARGET_MAX,
  TARGET_MIN,
} from './protocol.ts'
import { createQueue } from './queue.ts'
import { createDeviceStore, type DeviceState, type DeviceStore } from './store.ts'

export type Ble = {
  readonly store: DeviceStore
  // The device currently in use, kept after a drop so it can be reconnected without asking the
  // user to pick it again. null before the first connect.
  readonly link: DeviceLink | null
  // Asks the user to pick a device, then opens it. Must be called from a click handler.
  connect(): Promise<void>
  // Opens a link already picked: the second half of connect(), and the way back after a drop.
  open(link: DeviceLink): Promise<void>
  disconnect(): void
  setTarget(n: number): Promise<void>
  go(): Promise<void>
  stop(): Promise<void>
  testSpin(speed: 'full' | 'slow'): Promise<void>
  writePresets(presets: Presets): Promise<void>
  writeConfig(config: DeviceConfig): Promise<void>
}

const message = (error: unknown) => (error instanceof Error ? error.message : String(error))

export function createBle(options: {
  request: () => Promise<DeviceLink>
  store?: DeviceStore
}): Ble {
  const store = options.store ?? createDeviceStore()
  const queue = createQueue()
  let link: DeviceLink | null = null
  // The link the current session is attached to. A drop or a decode failure on any other link
  // (an older session) is ignored.
  let active: DeviceLink | null = null
  let stopListening: (() => void) | null = null

  function detach(): void {
    stopListening?.()
    stopListening = null
    active = null
  }

  // Leaves the device and puts the store in `connection`. The disconnect event that follows is
  // ignored because the link is no longer active.
  function drop(connection: DeviceState['connection'], error: string | null): void {
    const l = active
    detach()
    l?.disconnect()
    store.set({ connection, error })
  }

  function requireLink(): DeviceLink {
    if (!active || store.get().connection !== 'connected') throw new Error('Not connected')
    return active
  }

  async function write(name: Parameters<DeviceLink['write']>[0], value: ArrayBuffer): Promise<void> {
    const l = requireLink()
    return queue.run(() => l.write(name, value))
  }

  // Decodes a notification right away (the browser may reuse the buffer) and stores it.
  function onNotify<T>(l: DeviceLink, decode: (v: DataView) => T, apply: (value: T) => Partial<DeviceState>) {
    return (value: DataView) => {
      if (active !== l) return
      try {
        store.set(apply(decode(value)))
      } catch (error) {
        store.set({ error: message(error) })
      }
    }
  }

  async function open(l: DeviceLink): Promise<void> {
    detach()
    link = l
    active = l
    store.set({ connection: 'connecting', error: null, deviceName: l.name })
    stopListening = l.onDisconnect(() => {
      if (active !== l) return
      detach()
      store.set({ connection: 'disconnected' })
    })

    try {
      await queue.run(() => l.connect())

      // Config first: if this firmware speaks another version, nothing else is worth reading.
      const configBytes = await queue.run(() => l.read('config'))
      let config: DeviceConfig
      try {
        config = decodeConfig(configBytes)
      } catch (error) {
        if (active === l) {
          drop('incompatible', `Incompatible firmware for this version of the app (${message(error)})`)
        }
        return
      }

      const target = decodeUint16(await queue.run(() => l.read('target')))
      const count = decodeUint16(await queue.run(() => l.read('count')))
      const state = decodeState(await queue.run(() => l.read('state')))
      const battery = decodeUint16(await queue.run(() => l.read('battery')))
      const presets = decodePresets(await queue.run(() => l.read('presets')))
      if (active !== l) return
      store.set({ target, count, state, battery, presets, config })

      await queue.run(() => l.subscribe('target', onNotify(l, decodeUint16, (target) => ({ target }))))
      await queue.run(() => l.subscribe('count', onNotify(l, decodeUint16, (count) => ({ count }))))
      await queue.run(() => l.subscribe('state', onNotify(l, decodeState, (state) => ({ state }))))
      await queue.run(() => l.subscribe('battery', onNotify(l, decodeUint16, (battery) => ({ battery }))))
      if (active !== l) return
      store.set({ connection: 'connected' })
    } catch (error) {
      if (active === l) drop('disconnected', message(error))
    }
  }

  return {
    store,
    get link() {
      return link
    },

    async connect() {
      const { connection } = store.get()
      if (connection === 'connecting' || connection === 'connected') return
      let l: DeviceLink
      try {
        l = await options.request()
      } catch (error) {
        // Includes the user closing the device picker.
        store.set({ connection: 'disconnected', error: message(error) })
        return
      }
      await open(l)
    },

    open,

    disconnect() {
      drop('disconnected', null)
    },

    setTarget(n) {
      const target = Math.min(TARGET_MAX, Math.max(TARGET_MIN, Math.round(n)))
      return write('target', encodeUint16(target))
    },

    go: () => write('command', encodeCommand(Command.Go)),
    stop: () => write('command', encodeCommand(Command.Stop)),
    testSpin: (speed) => write('command', encodeCommand(speed === 'full' ? Command.TestFull : Command.TestSlow)),

    async writePresets(presets) {
      const l = requireLink()
      await queue.run(() => l.write('presets', encodePresets(presets)))
      // Not notified: read back what the device kept.
      const stored = decodePresets(await queue.run(() => l.read('presets')))
      if (active === l) store.set({ presets: stored })
    },

    async writeConfig(config) {
      const l = requireLink()
      await queue.run(() => l.write('config', encodeConfig(config)))
      const stored = decodeConfig(await queue.run(() => l.read('config')))
      if (active === l) store.set({ config: stored })
    },
  }
}
