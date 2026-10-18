// Getting the link back without the user: after a drop, and on app start.
//
// After a drop (the link was connected and went away without the user asking), it retries the
// same device with a growing pause between attempts, for GIVE_UP_MS in all, then stops and waits
// for a tap: retrying forever would keep the radio busy and drain the phone. Each attempt is a
// full ble.open(), so everything is read again and every notification subscribed again, exactly
// as on a first connect; whatever the device did meanwhile (a run that finished) is what shows.
//
// On start, if the browser can list the devices this site was already allowed to use, it waits
// for one to advertise and opens it without the picker (see findKnownDevice in link.ts).

import type { Ble } from './ble.ts'
import { type DeviceLink, knownLink } from './link.ts'
import { type Clock, realClock } from './mock.ts'
import { createStore, type Store } from './store.ts'

export type Phase =
  // Nothing going on: connected, or on the connect screen.
  | 'off'
  // On start, waiting for a known device to advertise. The « Connecter » button still works.
  | 'searching'
  // The link dropped; trying to get it back.
  | 'reconnecting'
  // Tried for GIVE_UP_MS without success; waiting for « Reconnecter ».
  | 'gaveup'

export type ReconnectState = { phase: Phase }

export type Timing = {
  // Pause after each failed attempt; the last one repeats.
  delaysMs: readonly number[]
  // Total time spent retrying after a drop before giving up.
  giveUpMs: number
  // A single attempt that takes longer than this is cut short. Chrome can sit on a connect to a
  // device that isn't there for a long time.
  attemptMs: number
  // How long to wait on start for a known device to show up.
  searchMs: number
}

export const defaultTiming: Timing = {
  delaysMs: [500, 1000, 2000, 4000, 5000],
  giveUpMs: 30_000,
  attemptMs: 8000,
  searchMs: 30_000,
}

export type Reconnect = {
  readonly store: Store<ReconnectState>
  // On app start: look for a known device and open it if it shows up.
  start(): Promise<void>
  // Stops the start-up search (the user tapped « Connecter »).
  stopSearch(): void
  // « Reconnecter » after giving up: another full round on the same device.
  retry(): void
  // The user leaves: stop everything and disconnect. A drop that follows is not retried.
  disconnect(): void
}

export function createReconnect(options: {
  ble: Ble
  clock?: Clock
  timing?: Partial<Timing>
  // Finds a known device on start; null when there is none or the browser can't tell.
  findKnown?: (signal: AbortSignal, timeoutMs: number) => Promise<DeviceLink | null>
}): Reconnect {
  const { ble } = options
  const clock = options.clock ?? realClock
  const timing = { ...defaultTiming, ...options.timing }
  const findKnown = options.findKnown ?? ((signal, timeoutMs) => knownLink({ signal, timeoutMs }))
  const store = createStore<ReconnectState>({ phase: 'off' })

  // Bumped whenever a round of retries starts or ends; a callback from an older round does nothing.
  let round = 0
  let timers: unknown[] = []
  let search: AbortController | null = null
  // Set while the app itself disconnects, so that drop isn't taken for a lost link.
  let leaving = false
  let last = ble.store.get().connection

  const setPhase = (phase: Phase) => {
    if (store.get().phase !== phase) store.set({ phase })
  }

  function later(fn: () => void, ms: number): void {
    timers.push(clock.setTimeout(fn, ms))
  }

  function endRound(): void {
    round++
    for (const t of timers) clock.clearTimeout(t)
    timers = []
  }

  // ble.open() with a time limit. Disconnecting aborts a connect still in progress.
  async function openWithin(link: DeviceLink, isCurrent: () => boolean): Promise<void> {
    const timer = clock.setTimeout(() => {
      if (isCurrent() && ble.store.get().connection === 'connecting') ble.disconnect()
    }, timing.attemptMs)
    try {
      await ble.open(link)
    } finally {
      clock.clearTimeout(timer)
    }
  }

  function startRound(): void {
    endRound()
    const r = round
    setPhase('reconnecting')
    later(() => {
      if (r !== round) return
      endRound()
      // Cut an attempt still running; its failure is then ignored.
      if (ble.store.get().connection === 'connecting') ble.disconnect()
      setPhase('gaveup')
    }, timing.giveUpMs)
    void attempt(r, 0)
  }

  async function attempt(r: number, n: number): Promise<void> {
    const link = ble.link
    if (r !== round || !link) return
    await openWithin(link, () => r === round)
    if (r !== round) return
    const { connection } = ble.store.get()
    if (connection === 'connected') return
    if (connection === 'incompatible') {
      // Another firmware answered: the connect screen says so; retrying won't change it.
      endRound()
      setPhase('off')
      return
    }
    const delay = timing.delaysMs[Math.min(n, timing.delaysMs.length - 1)] ?? 1000
    later(() => void attempt(r, n + 1), delay)
  }

  ble.store.subscribe((s) => {
    const was = last
    last = s.connection
    if (s.connection === 'connected') {
      if (store.get().phase === 'reconnecting' || store.get().phase === 'gaveup') {
        endRound()
        setPhase('off')
      }
      return
    }
    if (was === 'connected' && s.connection === 'disconnected' && !leaving) startRound()
  })

  return {
    store,

    async start() {
      if (store.get().phase !== 'off' || ble.store.get().connection !== 'disconnected') return
      const controller = new AbortController()
      search = controller
      setPhase('searching')
      let link: DeviceLink | null = null
      try {
        link = await findKnown(controller.signal, timing.searchMs)
      } catch {
        link = null
      }
      if (search !== controller) return
      search = null
      setPhase('off')
      if (link && ble.store.get().connection === 'disconnected') {
        await openWithin(link, () => ble.link === link)
      }
    },

    stopSearch() {
      if (!search) return
      search.abort()
      search = null
      if (store.get().phase === 'searching') setPhase('off')
    },

    retry() {
      if (store.get().phase !== 'gaveup' || !ble.link) return
      startRound()
    },

    disconnect() {
      endRound()
      leaving = true
      try {
        ble.disconnect()
      } finally {
        leaving = false
      }
      setPhase('off')
    },
  }
}
