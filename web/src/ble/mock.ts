// A fake device that speaks the same bytes as the firmware, for the tests and for `?mock`.
// It mirrors firmware/src/run.cpp: Go starts a run (slow straight away if the target is within
// slowdown_n), one BB per tick, slowdown when ≤ slowdown_n remain, DONE held a while then IDLE,
// JAM when no BB comes for jam_timeout_ms, LOW_BATT on GO with a flat pack. Test spins (commands 2 and 3) hold TESTING until stop;
// presets and config writes are ignored during a run. A dropped link stops a test spin but not a
// run, and simulateDisconnect() can keep the device out of reach for a while to test reconnection.

import type { CharacteristicName, DeviceLink } from './link.ts'
import {
  Command,
  CONFIG_LENGTH,
  type DeviceConfig,
  decodeConfig,
  decodePresets,
  decodeUint16,
  decodeUint8,
  encodeConfig,
  encodePresets,
  encodeUint16,
  encodeUint8,
  PRESET_COUNT,
  type Presets,
  State,
  TARGET_MAX,
  TARGET_MIN,
} from './protocol.ts'

export type Clock = {
  setTimeout(fn: () => void, ms: number): unknown
  clearTimeout(id: unknown): void
}

export const realClock: Clock = {
  setTimeout: (fn, ms) => globalThis.setTimeout(fn, ms),
  clearTimeout: (id) => globalThis.clearTimeout(id as ReturnType<typeof setTimeout>),
}

export type MockOptions = {
  // Timers, so tests can drive time by hand.
  clock?: Clock
  // Time between two BBs.
  tickMs?: number
  // The feed stops after this many BBs in a run, so the run ends in JAM.
  jamAt?: number
  // Version byte the config read answers with. Anything but 1 is an incompatible firmware.
  configVersion?: number
  target?: number
  battery?: number
  config?: Partial<DeviceConfig>
  // Drops the link this long after the first connect, once, like walking out of range.
  dropAfterMs?: number
  // How long the device stays out of reach after a drop. Infinity: it never comes back.
  awayMs?: number
}

// Same values as firmware/src/config.h.
const FIRST_BB_TIMEOUT_MS = 4000
const DONE_HOLD_MS = 2000
const BATTERY_PERIOD_MS = 5000
// BATT_REFUSE_MV: below it, GO and test spins go to LOW_BATT instead of starting.
const BATTERY_REFUSE_MV = 6600

const defaultConfig: DeviceConfig = {
  servoNeutralUs: 1500,
  speedFullOffsetUs: 300,
  speedSlowOffsetUs: 100,
  reverse: false,
  slowdownN: 4,
  jamTimeoutMs: 1500,
}

export class MockDevice implements DeviceLink {
  readonly name = 'BULLOADER (mock)'

  private readonly clock: Clock
  private readonly tickMs: number
  private readonly jamAt: number | undefined
  private readonly configVersion: number
  private readonly dropAfterMs: number | undefined
  private readonly awayMs: number

  private connected = false
  private away = false
  private dropScheduled = false
  private pendingConnect: { resolve: () => void; reject: (error: Error) => void } | null = null
  private target: number
  private count = 0
  private state: State = State.Idle
  private battery: number
  private presets: Presets = [30, 50, 120, 300]
  private config: DeviceConfig

  private runTimer: unknown = null
  private batteryTimer: unknown = null
  private readonly listeners = new Map<CharacteristicName, (value: DataView) => void>()
  private readonly disconnectListeners = new Set<() => void>()

  constructor(options: MockOptions = {}) {
    this.clock = options.clock ?? realClock
    this.tickMs = options.tickMs ?? 80
    this.jamAt = options.jamAt
    this.configVersion = options.configVersion ?? 1
    this.dropAfterMs = options.dropAfterMs
    this.awayMs = options.awayMs ?? 0
    this.target = options.target ?? 50
    this.battery = options.battery ?? 7900
    this.config = { ...defaultConfig, ...options.config }
  }

  async connect(): Promise<void> {
    if (this.away) {
      // Out of range: like Chrome, the attempt hangs until the device shows up or the caller
      // gives up with disconnect().
      await new Promise<void>((resolve, reject) => {
        this.pendingConnect = { resolve, reject }
      })
    }
    this.connected = true
    this.cancel('battery')
    this.scheduleBattery()
    if (this.dropAfterMs !== undefined && !this.dropScheduled) {
      this.dropScheduled = true
      this.clock.setTimeout(() => this.simulateDisconnect(this.awayMs), this.dropAfterMs)
    }
  }

  disconnect(): void {
    if (this.pendingConnect) {
      this.pendingConnect.reject(new Error('Connection attempt aborted'))
      this.pendingConnect = null
    }
    if (!this.connected) return
    this.connected = false
    this.listeners.clear()
    this.cancel('battery')
    // A test spin stops when the link goes (firmware #6); a run carries on, the device owns it.
    if (this.state === State.Testing) {
      this.cancel('run')
      this.state = State.Idle
    }
    for (const listener of [...this.disconnectListeners]) listener()
  }

  // The device going out of range or powering off. With awayMs, connect() can't reach it for that
  // long (Infinity: never again).
  simulateDisconnect(awayMs = 0): void {
    this.disconnect()
    if (awayMs <= 0) return
    this.away = true
    if (awayMs !== Number.POSITIVE_INFINITY) this.clock.setTimeout(() => this.comeBack(), awayMs)
  }

  // Back in range: an attempt waiting in connect() goes through.
  comeBack(): void {
    this.away = false
    const pending = this.pendingConnect
    this.pendingConnect = null
    pending?.resolve()
  }

  async read(name: CharacteristicName): Promise<DataView> {
    this.ensureConnected()
    return new DataView(this.bytes(name))
  }

  async write(name: CharacteristicName, value: ArrayBuffer): Promise<void> {
    this.ensureConnected()
    switch (name) {
      case 'target': {
        // Ignored during a run; the real value is notified back either way.
        if (!this.isRunning()) {
          this.target = Math.min(TARGET_MAX, Math.max(TARGET_MIN, decodeUint16(value)))
        }
        this.notify('target')
        return
      }
      case 'command':
        return this.command(decodeUint8(value))
      // Presets and config are ignored during a run, like the firmware does. They don't notify:
      // the app reads them back and sees the old values.
      case 'presets': {
        if (this.isRunning() || value.byteLength !== PRESET_COUNT * 2) return
        this.presets = decodePresets(value)
        return
      }
      case 'config': {
        if (this.isRunning() || value.byteLength !== CONFIG_LENGTH) return
        try {
          this.config = decodeConfig(value)
        } catch {
          // Wrong version: the firmware ignores the write.
        }
        return
      }
      default:
        throw new Error(`${name} is not writable`)
    }
  }

  async subscribe(name: CharacteristicName, listener: (value: DataView) => void): Promise<void> {
    this.ensureConnected()
    this.listeners.set(name, listener)
  }

  onDisconnect(listener: () => void): () => void {
    this.disconnectListeners.add(listener)
    return () => {
      this.disconnectListeners.delete(listener)
    }
  }

  private command(command: number): void {
    switch (command) {
      case Command.Stop:
        this.cancel('run')
        return this.setState(State.Idle)
      case Command.Go:
        return this.go()
      case Command.TestFull:
      case Command.TestSlow:
        if (this.isRunning()) return
        this.cancel('run')
        if (this.battery < BATTERY_REFUSE_MV) return this.setState(State.LowBatt)
        return this.setState(State.Testing)
      default:
      // Unknown commands are ignored.
    }
  }

  private go(): void {
    if (this.isRunning()) return
    this.cancel('run')
    if (this.battery < BATTERY_REFUSE_MV) return this.setState(State.LowBatt)
    this.count = 0
    this.notify('count')
    this.setState(this.target <= this.config.slowdownN ? State.Slowdown : State.Running)
    this.scheduleTick()
  }

  private tick(): void {
    this.runTimer = null
    this.count += 1
    this.notify('count')
    if (this.count >= this.target) {
      this.setState(State.Done)
      this.runTimer = this.clock.setTimeout(() => {
        this.runTimer = null
        this.setState(State.Idle)
      }, DONE_HOLD_MS)
      return
    }
    if (this.state === State.Running && this.target - this.count <= this.config.slowdownN) {
      this.setState(State.Slowdown)
    }
    this.scheduleTick()
  }

  private scheduleTick(): void {
    if (this.jamAt !== undefined && this.count >= this.jamAt) {
      // No more BBs: the run times out into JAM.
      const timeout = this.count === 0 ? FIRST_BB_TIMEOUT_MS : this.config.jamTimeoutMs
      this.runTimer = this.clock.setTimeout(() => {
        this.runTimer = null
        this.setState(State.Jam)
      }, timeout)
      return
    }
    this.runTimer = this.clock.setTimeout(() => this.tick(), this.tickMs)
  }

  private scheduleBattery(): void {
    this.batteryTimer = this.clock.setTimeout(() => {
      this.battery = Math.max(6400, this.battery - 5)
      this.notify('battery')
      this.scheduleBattery()
    }, BATTERY_PERIOD_MS)
  }

  private cancel(which: 'run' | 'battery'): void {
    const timer = which === 'run' ? this.runTimer : this.batteryTimer
    if (timer !== null) this.clock.clearTimeout(timer)
    if (which === 'run') this.runTimer = null
    else this.batteryTimer = null
  }

  private setState(state: State): void {
    this.state = state
    this.notify('state')
  }

  private isRunning(): boolean {
    return this.state === State.Running || this.state === State.Slowdown
  }

  private notify(name: CharacteristicName): void {
    // A fresh buffer each time, like a real notification.
    this.listeners.get(name)?.(new DataView(this.bytes(name)))
  }

  private bytes(name: CharacteristicName): ArrayBuffer {
    switch (name) {
      case 'target':
        return encodeUint16(this.target)
      case 'count':
        return encodeUint16(this.count)
      case 'state':
        return encodeUint8(this.state)
      case 'battery':
        return encodeUint16(this.battery)
      case 'presets':
        return encodePresets(this.presets)
      case 'config': {
        const buf = encodeConfig(this.config)
        new DataView(buf).setUint8(0, this.configVersion)
        return buf
      }
      case 'command':
        throw new Error('command is not readable')
    }
  }

  private ensureConnected(): void {
    if (!this.connected) throw new Error('Mock disconnected')
  }
}
