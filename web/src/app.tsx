// The whole app: one island, every screen in it. Changing page would drop the Bluetooth link.
// Screens only read the store and call ble.*; the ESP32 owns the state.

import type { ComponentChildren, JSX } from 'preact'
import { useEffect, useRef, useState } from 'preact/hooks'
import { createBle } from './ble/ble.ts'
import { isMockRequested, requestLink } from './ble/link.ts'
import { createReconnect, type Phase } from './ble/reconnect.ts'
import { PRESET_COUNT, State, TARGET_MAX, TARGET_MIN } from './ble/protocol.ts'
import { createStore, type DeviceState, useStore } from './ble/store.ts'
import { LANG_NAMES, LANGS, langStore, setLang, t } from './i18n/index.ts'
import {
  batteryLevel,
  batteryText,
  canEditSettings,
  canGo,
  canStep,
  clampTarget,
  connectionErrorText,
  countIsCurrent,
  goReloadsHint,
  isRunning,
  type LastRun,
  lastRunText,
  motorMayRun,
  nextLastRun,
  progress,
  readTarget,
  sendErrorText,
  stateLabel,
  stateTone,
  type TargetNote,
  type Tone,
} from './ui/rules.ts'
import {
  draftFrom,
  type DraftField,
  NEUTRAL_STEP_US,
  PRESET_INDEXES,
  type SettingsDraft,
  sameDraft,
  stepNeutral,
  validateSettings,
} from './ui/settings.ts'

const hasBluetooth = typeof navigator !== 'undefined' && 'bluetooth' in navigator
const mock = isMockRequested()

const ble = createBle({ request: requestLink })
const reconnect = createReconnect({ ble })

type Screen = 'main' | 'settings'

// A write that failed (link dropped mid-way, GATT busy): the store didn't move, so the screen
// already shows the truth. Nothing more to do here.
const ignore = () => {}

const message = (error: unknown) => (error instanceof Error ? error.message : String(error))

// ---- Test spins ----
// A test spin must never outlive the screen that started it: leaving the settings screen, hiding
// the page and disconnecting all send stop (see stopSpinIfAny's callers). The firmware also stops
// on disconnect (#6), but that is the safety net, not the plan.

// A test spin asked for and not stopped yet. Covers the gap between the command and the TESTING
// notification; once the device says TESTING, its state takes over.
let spinRequested = false
ble.store.subscribe((s) => {
  if (s.state === State.Testing) spinRequested = false
})

function spinning(): boolean {
  return spinRequested || ble.store.get().state === State.Testing
}

function stopSpin(): Promise<void> {
  spinRequested = false
  return ble.stop()
}

function stopSpinIfAny(): void {
  if (spinning()) stopSpin().catch(ignore)
}

// ---- What the app remembers about this session ----
// lastRun: how the last run ended, worked out from the states the device notified (see
// nextLastRun). pendingStop: a stop that couldn't be sent because the link was down, sent on
// reconnect. 'spin' only stops a test spin; 'any' (STOP tapped while disconnected) also stops a run.
type PendingStop = null | 'spin' | 'any'
const session = createStore<{ lastRun: LastRun | null; pendingStop: PendingStop }>({
  lastRun: null,
  pendingStop: null,
})

// The state of the previous connected update. Reset while the link is down, so a jump seen
// across a reconnect isn't taken for a transition we watched.
let prevState: State | null = null
ble.store.subscribe((s) => {
  if (s.connection !== 'connected') {
    prevState = null
    return
  }
  const before = session.get().lastRun
  const lastRun = nextLastRun(before, prevState, s)
  if (lastRun !== before) session.set({ lastRun })
  // A buzz on the two endings worth feeling with the phone in the pocket.
  if (prevState !== null && s.state !== prevState) {
    if (s.state === State.Done) buzz(150)
    if (s.state === State.Jam) buzz([300, 150, 300])
  }
  prevState = s.state
})

function buzz(pattern: number | number[]): void {
  try {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) navigator.vibrate(pattern)
  } catch {
    // No vibration motor, or the browser said no: the screen says it anyway.
  }
}

// A link that drops during a test spin can't carry the stop. The firmware stops the motor on
// disconnect, but in case it didn't: once reconnected, if the device still says TESTING, stop it.
// Only then: any other state (a run started from the encoder meanwhile) is left alone, unless the
// user tapped STOP while disconnected.
reconnect.store.subscribe((r) => {
  if (r.phase === 'reconnecting' && spinning()) {
    spinRequested = false
    if (session.get().pendingStop === null) session.set({ pendingStop: 'spin' })
  }
})
ble.store.subscribe((s) => {
  const pending = session.get().pendingStop
  if (s.connection !== 'connected' || pending === null) return
  session.set({ pendingStop: null })
  if (s.state === State.Testing || (pending === 'any' && isRunning(s.state))) ble.stop().catch(ignore)
})

// STOP tapped while the link is down: nothing can be sent now, so it goes on reconnect.
function queueStop(): void {
  session.set({ pendingStop: 'any' })
}

// Disconnecting during a test spin stops it first. Bounded wait: a stuck GATT must not keep the
// user from leaving.
async function disconnect(): Promise<void> {
  if (spinning()) {
    await Promise.race([stopSpin().catch(ignore), new Promise((resolve) => setTimeout(resolve, 1000))])
  }
  reconnect.disconnect()
  session.set({ lastRun: null, pendingStop: null })
}

// The current language, for the pure functions that take it. Read during render: App subscribes to
// langStore, so a switch re-renders every screen.
const lang = () => langStore.get().lang

export function App() {
  // Switching language re-renders from here down; nothing navigates, so the link stays up.
  useStore(langStore)
  const s = useStore(ble.store)
  const { phase } = useStore(reconnect.store)
  const [screen, setScreen] = useState<Screen>('main')

  // On start, connect to a device used before if the browser lets us find it (no picker).
  useEffect(() => {
    if (!mock && hasBluetooth) void reconnect.start()
    return () => reconnect.stopSearch()
  }, [])

  // Hiding the page (switching app, locking the phone, closing the tab) stops a test spin.
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') stopSpinIfAny()
    }
    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('pagehide', stopSpinIfAny)
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('pagehide', stopSpinIfAny)
    }
  }, [])

  // A dropped link keeps the session: the screen stays, greyed, with a banner, while it reconnects
  // or waits for « Reconnecter ». Only leaving for the connect screen ends it.
  const offline = s.connection !== 'connected'
  const lost = phase === 'reconnecting' || phase === 'gaveup'
  const inSession = !offline || lost

  // Back on the connect screen, the next session starts on the main screen.
  useEffect(() => {
    if (!inSession) setScreen('main')
  }, [inSession])

  if (!hasBluetooth && !mock) {
    return (
      <main class="screen center">
        <h1 class="title">BULLOADER+</h1>
        <p class="error" role="alert">
          {t('app.noBluetooth')}
        </p>
        <LanguageSwitch />
      </main>
    )
  }

  if (!inSession) return <ConnectScreen s={s} searching={phase === 'searching'} />

  const banner = offline ? <LinkBanner phase={phase} state={s.state} /> : null
  if (screen === 'settings') {
    return <SettingsScreen s={s} offline={offline} banner={banner} onBack={() => setScreen('main')} />
  }
  return <MainScreen s={s} offline={offline} banner={banner} onSettings={() => setScreen('settings')} />
}

// Over the screen while the link is down. The values under it are the last ones the device sent.
// If the device was moving the motor, say it may still be, and how to stop it from the device.
function LinkBanner({ phase, state }: { phase: Phase; state: State | null }) {
  const { pendingStop } = useStore(session)
  const moving = motorMayRun(state)
  const notes = moving && (
    <>
      <p class="banner-note">{t('banner.motorMayRun')}</p>
      {pendingStop === 'any' && <p class="banner-note">{t('banner.stopQueued')}</p>}
    </>
  )
  if (phase !== 'gaveup') {
    return (
      <div class="banner" role={moving ? 'alert' : 'status'}>
        <p>{t('banner.reconnecting')}</p>
        {notes}
      </div>
    )
  }
  return (
    <div class="banner lost" role="alert">
      <p>{t('banner.lost')}</p>
      {notes}
      <div class="banner-actions">
        <button class="btn" type="button" onClick={() => reconnect.retry()}>
          {t('banner.retry')}
        </button>
        <button class="btn ghost" type="button" onClick={() => disconnect()}>
          {t('banner.changeDevice')}
        </button>
      </div>
    </div>
  )
}

function ConnectScreen({ s, searching }: { s: DeviceState; searching: boolean }) {
  const busy = s.connection === 'connecting'
  return (
    <main class="screen center">
      <h1 class="title">BULLOADER+</h1>
      <button
        class="btn primary wide"
        type="button"
        disabled={busy}
        onClick={() => {
          // The picker needs the click's user gesture: no await before ble.connect().
          reconnect.stopSearch()
          void ble.connect()
        }}
      >
        {busy ? t('connect.busy') : t('connect.button')}
      </button>
      {searching && !busy && <p class="hint">{t('connect.searching')}</p>}
      {s.connection === 'incompatible' ? (
        <p class="error" role="alert">
          {t('connect.incompatible')}
        </p>
      ) : (
        s.error && (
          <p class="error" role="alert">
            {connectionErrorText(s.error, lang())}
          </p>
        )
      )}
      {mock && <p class="hint">{t('connect.mock')}</p>}
      <LanguageSwitch />
    </main>
  )
}

function MainScreen(props: {
  s: DeviceState
  offline: boolean
  banner: ComponentChildren
  onSettings: () => void
}) {
  const { s, offline, onSettings } = props
  const { lastRun, pendingStop } = useStore(session)
  // Nothing can be sent while the link is down: everything that writes is off.
  const locked = isRunning(s.state) || offline
  // One main action at a time: STOP while the motor turns, GO otherwise.
  const moving = motorMayRun(s.state)
  const tone = stateTone(s.state)
  const current = countIsCurrent(s.state, lastRun, s.target)
  const ratio = current ? progress(s.count, s.target) : 0
  const reload = offline ? null : goReloadsHint(lastRun, s.state, s.target)

  // Under the state: what to do next after a jam or a flat pack, otherwise how the last run ended.
  let sub: ComponentChildren = null
  if (s.state === State.Jam) sub = t('next.jam')
  else if (s.state === State.LowBatt) sub = t('next.lowBatt')
  else if (s.state === State.Idle && lastRun) {
    sub = (
      <>
        {lastRunText(lastRun, lang())}
        {lastRun.end === 'done' && <Icon name="ok" />}
      </>
    )
  }

  return (
    <main class={offline ? 'screen main stale' : 'screen main'}>
      {props.banner}
      <header class="bar">
        <span class="device">{s.deviceName}</span>
        {s.battery !== null && (
          <span class={`battery ${batteryLevel(s.battery)}`}>{batteryText(s.battery, lang())}</span>
        )}
        <button class="btn icon" type="button" aria-label={t('main.settings')} onClick={onSettings}>
          <Icon name="settings" />
        </button>
      </header>

      <section class={`hero tone-${tone}`}>
        {/* Only the state and its line are announced: the count would read out every BB. */}
        <div class="state-block" role="status" aria-atomic="true">
          <p class="state">
            {s.state !== null && <Icon name={tone} />}
            <span>{s.state === null ? '—' : stateLabel(s.state, lang())}</span>
          </p>
          <p class="state-sub">{sub}</p>
        </div>
        <p class={current ? 'count' : 'count old'}>
          <span>{s.count ?? '—'}</span>
          <span class="of"> / {s.target ?? '—'}</span>
        </p>
        <div
          class="progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={s.target ?? 0}
          aria-valuenow={current ? (s.count ?? 0) : 0}
        >
          <div class="fill" style={{ width: `${ratio * 100}%` }} />
        </div>
      </section>

      <TargetField target={s.target} disabled={locked} />

      <div class="presets">
        {(s.presets ?? []).slice(0, PRESET_COUNT).map((p, i) => (
          <button
            key={i}
            class={p === s.target ? 'btn chip current' : 'btn chip'}
            type="button"
            aria-pressed={p === s.target}
            disabled={locked}
            onClick={() => ble.setTarget(p).catch(ignore)}
          >
            {p}
          </button>
        ))}
      </div>

      <div class="dock">
        {reload !== null && <p class="dock-hint">{t('main.goReloads', { n: reload })}</p>}
        {moving ? (
          // Offline, STOP can't be sent: it is kept and sent on reconnect (see queueStop).
          <button
            class="btn stop"
            type="button"
            disabled={offline && pendingStop === 'any'}
            onClick={() => (offline ? queueStop() : ble.stop().catch(ignore))}
          >
            STOP
            {offline && pendingStop === 'any' && <span class="btn-sub">{t('main.stopQueued')}</span>}
          </button>
        ) : (
          <button
            class="btn go"
            type="button"
            disabled={offline || !canGo(s.state)}
            onClick={() => ble.go().catch(ignore)}
          >
            GO
          </button>
        )}
      </div>
    </main>
  )
}

// The target with − / + and a field. The field shows the device's target; while it has focus it
// holds what the user is typing, sent once on blur or Enter. Whatever the device answers replaces it.
// A value that had to be changed (0 → 1, letters) says so on a line kept for it.
function TargetField({ target, disabled }: { target: number | null; disabled: boolean }) {
  const [draft, setDraft] = useState<string | null>(null)
  const [note, setNote] = useState<TargetNote | null>(null)
  // Escape blurs the field too; this tells the blur not to send.
  const cancelled = useRef(false)

  function commit(text: string) {
    setDraft(null)
    if (cancelled.current) {
      cancelled.current = false
      return
    }
    const read = readTarget(text)
    setNote(read.note)
    if (read.value !== null && read.value !== target) ble.setTarget(read.value).catch(ignore)
  }

  function step(delta: number) {
    setNote(null)
    if (target === null) return
    const n = clampTarget(target + delta)
    if (n !== target) ble.setTarget(n).catch(ignore)
  }

  const noteText =
    note === 'min'
      ? t('main.noteMin', { n: TARGET_MIN })
      : note === 'max'
        ? t('main.noteMax', { n: TARGET_MAX })
        : note === 'notNumber'
          ? t('main.noteNotNumber')
          : ''

  return (
    <div class="target">
      <label for="target" class="label">
        {t('main.target')}
      </label>
      <div class="stepper">
        <button
          class="btn step"
          type="button"
          aria-label={t('main.minusOne')}
          disabled={disabled || !canStep(target, -1)}
          onClick={() => step(-1)}
        >
          −
        </button>
        <input
          id="target"
          class="field"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={4}
          autoComplete="off"
          aria-describedby="target-note"
          disabled={disabled || target === null}
          value={draft ?? (target === null ? '' : String(target))}
          onFocus={(e) => {
            setNote(null)
            setDraft(e.currentTarget.value)
            e.currentTarget.select()
          }}
          onInput={(e) => setDraft(e.currentTarget.value)}
          onBlur={(e) => commit(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') {
              cancelled.current = true
              e.currentTarget.blur()
            }
          }}
        />
        <button
          class="btn step"
          type="button"
          aria-label={t('main.plusOne')}
          disabled={disabled || !canStep(target, 1)}
          onClick={() => step(1)}
        >
          +
        </button>
      </div>
      <p id="target-note" class="note" role="status">
        {noteText}
      </p>
    </div>
  )
}

// Drawn icons, one stroke weight. Each sits next to a word: never the only carrier of meaning.
type IconName = Tone | 'settings' | 'back'
const iconPaths: Record<IconName, JSX.Element> = {
  idle: <circle cx="12" cy="12" r="4.5" fill="currentColor" stroke="none" />,
  run: <path d="M4.5 5.5 11 12l-6.5 6.5M12.5 5.5 19 12l-6.5 6.5" />,
  slow: <path d="M9 5.5 15.5 12 9 18.5" />,
  ok: <path d="M4.5 12.5 9.5 17.5 19.5 6.5" />,
  alarm: <path d="M12 3.5 2.5 20h19L12 3.5ZM12 10v4.5M12 17.25v.25" />,
  warn: <path d="M3 8h14a1.5 1.5 0 0 1 1.5 1.5v5A1.5 1.5 0 0 1 17 16H3a1.5 1.5 0 0 1-1.5-1.5v-5A1.5 1.5 0 0 1 3 8ZM21.5 10.5v3M5 11v2" />,
  test: <path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3M19.5 4v4h-4" />,
  settings: <path d="M4 7h9M17 7h3M4 17h3M11 17h9M15 4.5v5M9 14.5v5" />,
  back: <path d="M19.5 12h-15M11 5.5 4.5 12l6.5 6.5" />,
}

function Icon({ name }: { name: IconName }) {
  return (
    <svg
      class="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      {iconPaths[name]}
    </svg>
  )
}

// The form edits a local draft. null means "not edited": the fields show the device's values, and
// go back to them after a save, so what you see after saving is what the device kept.
const emptyDraft: SettingsDraft = {
  presets: ['', '', '', ''],
  servoNeutralUs: '',
  speedFullOffsetUs: '',
  speedSlowOffsetUs: '',
  reverse: false,
  slowdownN: '',
  jamTimeoutMs: '',
}

type Busy = null | 'save' | 'full' | 'slow'

function SettingsScreen(props: {
  s: DeviceState
  offline: boolean
  banner: ComponentChildren
  onBack: () => void
}) {
  const { s, offline, onBack } = props
  const [draft, setDraft] = useState<SettingsDraft | null>(null)
  const [busy, setBusy] = useState<Busy>(null)
  // Kept as a function so it follows a language switch while it is on screen.
  const [notice, setNotice] = useState<{ text: () => string } | null>(null)
  const mounted = useRef(true)
  // « ← » with unsaved changes asks first, in the app (no browser dialog).
  const confirm = useRef<HTMLDialogElement>(null)

  // Leaving this screen (Retour, or giving up on a lost link) stops a spin. A drop alone keeps the
  // screen and the draft; the spin is then stopped on reconnect if the device still runs it.
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
      stopSpinIfAny()
    }
  }, [])

  // The config didn't decode: lock the form rather than show zeros.
  const incompatible = s.config === null || s.presets === null
  const stored = s.config && s.presets ? draftFrom(s.presets, s.config) : emptyDraft
  const values = draft ?? stored
  const dirty = draft !== null && !sameDraft(draft, stored)
  const validation = validateSettings(values, lang())
  const errors: Partial<Record<DraftField, string>> = validation.ok ? {} : validation.errors
  const atRest = canEditSettings(s.state)
  const canAct = !offline && !incompatible && atRest && busy === null && validation.ok
  // Offline, the last state is only a memory: the firmware stops a test spin when the link goes.
  const testing = !offline && s.state === State.Testing

  const edit = (patch: Partial<SettingsDraft>) => {
    setNotice(null)
    setDraft({ ...values, ...patch })
  }

  const neutralStep = (delta: number) =>
    edit({ servoNeutralUs: String(stepNeutral(values.servoNeutralUs, delta, s.config?.servoNeutralUs ?? 1500)) })

  // Writes the draft if it differs from the device. The BLE layer reads both values back into the
  // store; dropping the draft then shows them.
  async function save(): Promise<void> {
    if (!validation.ok || !dirty) return
    const { presets, config } = validation.values
    await ble.writePresets(presets)
    await ble.writeConfig(config)
    if (!mounted.current) return
    setDraft(null)
    const now = ble.store.get()
    const kept =
      now.config !== null &&
      now.presets !== null &&
      sameDraft(draftFrom(now.presets, now.config), draftFrom(presets, config))
    setNotice({ text: () => (kept ? t('settings.saved') : t('settings.notKept')) })
  }

  // « Enregistrer », or « Enregistrer et tester »: a test spin uses the device's saved config, so
  // what is tested is what is stored.
  async function run(kind: Exclude<Busy, null>): Promise<void> {
    setBusy(kind)
    setNotice(null)
    try {
      await save()
      if (kind === 'save') return
      // The user may have left while saving: don't start a spin nobody is watching.
      if (!mounted.current || document.visibilityState === 'hidden') return
      spinRequested = true
      await ble.testSpin(kind)
    } catch (error) {
      if (mounted.current) {
        const reason = message(error)
        setNotice({ text: () => sendErrorText(reason, lang()) })
      }
    } finally {
      if (mounted.current) setBusy(null)
    }
  }

  function leave(): void {
    if (dirty) confirm.current?.showModal()
    else onBack()
  }

  async function saveAndLeave(): Promise<void> {
    confirm.current?.close()
    setBusy('save')
    try {
      await save()
      onBack()
    } catch (error) {
      if (mounted.current) {
        const reason = message(error)
        setNotice({ text: () => sendErrorText(reason, lang()) })
      }
    } finally {
      if (mounted.current) setBusy(null)
    }
  }

  // Why « Enregistrer » can't be used right now, if it can't.
  const cantSave = !validation.ok
    ? t('settings.unsavedInvalid')
    : offline
      ? t('error.notConnected')
      : !atRest
        ? t('settings.motorRunning')
        : null

  const presetError = PRESET_INDEXES.map((i) => {
    const error = errors[`preset${i}`]
    return error ? t('settings.presetError', { n: i + 1, error }) : null
  }).find((e) => e !== null)

  return (
    <main class={offline ? 'screen settings stale' : 'screen settings'}>
      {props.banner}
      <dialog ref={confirm} class="confirm" aria-labelledby="unsaved-title">
        <h2 id="unsaved-title" class="confirm-title">
          {t('settings.unsavedTitle')}
        </h2>
        <p>{t('settings.unsavedBody')}</p>
        {cantSave && <p class="hint">{cantSave}</p>}
        <div class="confirm-actions">
          <button class="btn primary" type="button" disabled={!canAct} onClick={() => void saveAndLeave()}>
            {t('settings.save')}
          </button>
          <button
            class="btn"
            type="button"
            onClick={() => {
              confirm.current?.close()
              onBack()
            }}
          >
            {t('settings.discard')}
          </button>
          <button class="btn quiet" type="button" onClick={() => confirm.current?.close()}>
            {t('settings.stay')}
          </button>
        </div>
      </dialog>
      <header class="bar">
        <button class="btn icon" type="button" aria-label={t('settings.back')} onClick={leave}>
          <Icon name="back" />
        </button>
        <h1 class="bar-title">{t('settings.title')}</h1>
        <span class={testing ? 'pill active' : 'pill'}>{s.state === null ? '—' : stateLabel(s.state, lang())}</span>
      </header>

      {incompatible && (
        <p class="error" role="alert">
          {t('settings.incompatible')}
        </p>
      )}

      <section class="group">
        <h2 class="group-title">{t('settings.presets')}</h2>
        <div class="presets">
          {PRESET_INDEXES.map((i) => (
            <input
              key={i}
              class={errors[`preset${i}`] ? 'field small invalid' : 'field small'}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={4}
              autoComplete="off"
              aria-label={t('settings.preset', { n: i + 1 })}
              aria-invalid={!!errors[`preset${i}`]}
              aria-describedby="preset-error"
              disabled={incompatible}
              value={values.presets[i]}
              onInput={(e) => {
                const presets = [...values.presets] as SettingsDraft['presets']
                presets[i] = e.currentTarget.value
                edit({ presets })
              }}
            />
          ))}
        </div>
        <FieldError id="preset-error" error={presetError} />
      </section>

      <section class="group">
        <h2 class="group-title">{t('settings.loading')}</h2>
        <NumberField
          id="slowdown"
          label={t('settings.slowdown')}
          value={values.slowdownN}
          error={errors.slowdownN}
          disabled={incompatible}
          onInput={(slowdownN) => edit({ slowdownN })}
        />
        <NumberField
          id="jam"
          label={t('settings.jam')}
          value={values.jamTimeoutMs}
          error={errors.jamTimeoutMs}
          disabled={incompatible}
          onInput={(jamTimeoutMs) => edit({ jamTimeoutMs })}
        />
      </section>

      <section class="group">
        <h2 class="group-title">{t('settings.servo')}</h2>
        <div class="target">
          <label for="neutral" class="label">
            {t('settings.neutral')}
          </label>
          <div class="stepper">
            <button
              class="btn step small"
              type="button"
              aria-label={t('settings.minusUs', { n: NEUTRAL_STEP_US })}
              disabled={incompatible}
              onClick={() => neutralStep(-NEUTRAL_STEP_US)}
            >
              −{NEUTRAL_STEP_US}
            </button>
            <input
              id="neutral"
              class={errors.servoNeutralUs ? 'field invalid' : 'field'}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={4}
              autoComplete="off"
              aria-invalid={!!errors.servoNeutralUs}
              aria-describedby="neutral-error"
              disabled={incompatible}
              value={values.servoNeutralUs}
              onInput={(e) => edit({ servoNeutralUs: e.currentTarget.value })}
            />
            <button
              class="btn step small"
              type="button"
              aria-label={t('settings.plusUs', { n: NEUTRAL_STEP_US })}
              disabled={incompatible}
              onClick={() => neutralStep(NEUTRAL_STEP_US)}
            >
              +{NEUTRAL_STEP_US}
            </button>
          </div>
          <FieldError id="neutral-error" error={errors.servoNeutralUs} />
        </div>
        <NumberField
          id="full"
          label={t('settings.fullOffset')}
          value={values.speedFullOffsetUs}
          error={errors.speedFullOffsetUs}
          disabled={incompatible}
          signed
          onInput={(speedFullOffsetUs) => edit({ speedFullOffsetUs })}
        />
        <NumberField
          id="slow"
          label={t('settings.slowOffset')}
          value={values.speedSlowOffsetUs}
          error={errors.speedSlowOffsetUs}
          disabled={incompatible}
          signed
          onInput={(speedSlowOffsetUs) => edit({ speedSlowOffsetUs })}
        />
        <button
          class={values.reverse ? 'btn toggle on' : 'btn toggle'}
          type="button"
          role="switch"
          aria-checked={values.reverse}
          disabled={incompatible}
          onClick={() => edit({ reverse: !values.reverse })}
        >
          <span>{t('settings.reverse')}</span>
          <span class="toggle-value">{values.reverse ? t('settings.yes') : t('settings.no')}</span>
        </button>
      </section>

      <section class="group">
        <p class="field-error" role="status">
          {!validation.ok && !incompatible && (
            <>
              <Icon name="alarm" />
              {t('settings.fixErrors')}
            </>
          )}
        </p>
        {!offline && !atRest && !testing && !incompatible && <p class="hint">{t('settings.motorRunning')}</p>}
        {notice && (
          <p class="hint" role="status">
            {notice.text()}
          </p>
        )}
        <button class="btn primary" type="button" disabled={!canAct || !dirty} onClick={() => run('save')}>
          {busy === 'save' ? t('settings.saving') : t('settings.save')}
        </button>
      </section>

      <section class="group">
        <h2 class="group-title">{t('settings.motorTest')}</h2>
        {offline ? (
          <p class="hint">{t('settings.testOffline')}</p>
        ) : testing ? (
          <p class="spin-live" aria-live="polite">
            {t('settings.testRunning')}
          </p>
        ) : (
          <p class="hint">
            {dirty ? t('settings.testSavesFirst') : t('settings.testSaved')}
          </p>
        )}
        <div class="actions">
          <button class="btn" type="button" disabled={!canAct} onClick={() => run('full')}>
            {busy === 'full' ? '…' : t('settings.testFull')}
          </button>
          <button class="btn" type="button" disabled={!canAct} onClick={() => run('slow')}>
            {busy === 'slow' ? '…' : t('settings.testSlow')}
          </button>
        </div>
        <button class="btn stop" type="button" disabled={offline} onClick={() => stopSpin().catch(ignore)}>
          STOP
        </button>
      </section>

      <section class="group">
        <h2 class="group-title">{t('lang.title')}</h2>
        <LanguageSwitch />
      </section>

      <section class="group">
        <h2 class="group-title">{t('settings.device')}</h2>
        <p class="device-name">{s.deviceName}</p>
        <button class="btn" type="button" onClick={() => void disconnect()}>
          {t('banner.changeDevice')}
        </button>
      </section>
    </main>
  )
}

// Français / English. Local to the phone: works offline and with no device. Each language is named
// in its own language, so someone who can't read the current one still finds theirs.
function LanguageSwitch() {
  const current = langStore.get().lang
  return (
    <div class="langs" role="group" aria-label={t('lang.title')}>
      {LANGS.map((l) => (
        <button
          key={l}
          class={l === current ? 'btn lang current' : 'btn lang'}
          type="button"
          lang={l}
          aria-pressed={l === current}
          onClick={() => setLang(l)}
        >
          {LANG_NAMES[l]}
        </button>
      ))}
    </div>
  )
}

function NumberField(props: {
  id: string
  label: string
  value: string
  error: string | undefined
  disabled: boolean
  signed?: boolean
  onInput: (value: string) => void
}) {
  return (
    <div class="target">
      <label for={props.id} class="label">
        {props.label}
      </label>
      <input
        id={props.id}
        class={props.error ? 'field small invalid' : 'field small'}
        type="text"
        inputMode="numeric"
        // Signed fields take a minus: no digits-only pattern there.
        pattern={props.signed ? undefined : '[0-9]*'}
        maxLength={5}
        autoComplete="off"
        aria-invalid={!!props.error}
        aria-describedby={`${props.id}-error`}
        disabled={props.disabled}
        value={props.value}
        onInput={(e) => props.onInput(e.currentTarget.value)}
      />
      <FieldError id={`${props.id}-error`} error={props.error} />
    </div>
  )
}


// A field's error, on a line that is always there: an error showing up doesn't push the form down.
// The glyph and the words carry it, the red border only repeats it.
function FieldError({ id, error }: { id: string; error: string | null | undefined }) {
  return (
    <p id={id} class="field-error">
      {error && (
        <>
          <Icon name="alarm" />
          {error}
        </>
      )}
    </p>
  )
}
