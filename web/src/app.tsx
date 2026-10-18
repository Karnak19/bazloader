// The whole app: one island, every screen in it. Changing page would drop the Bluetooth link.
// Screens only read the store and call ble.*; the ESP32 owns the state.

import { useEffect, useRef, useState } from 'preact/hooks'
import { createBle } from './ble/ble.ts'
import { isMockRequested, requestLink } from './ble/link.ts'
import { PRESET_COUNT, State } from './ble/protocol.ts'
import { type DeviceState, useStore } from './ble/store.ts'
import {
  batteryLevel,
  batteryText,
  canEditSettings,
  canGo,
  clampTarget,
  connectionErrorText,
  isRunning,
  parseTarget,
  progress,
  stateLabel,
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

// Disconnecting during a test spin stops it first. Bounded wait: a stuck GATT must not keep the
// user from leaving.
async function disconnect(): Promise<void> {
  if (spinning()) {
    await Promise.race([stopSpin().catch(ignore), new Promise((resolve) => setTimeout(resolve, 1000))])
  }
  ble.disconnect()
}

export function App() {
  const s = useStore(ble.store)
  const [screen, setScreen] = useState<Screen>('main')

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

  // After a drop, come back to the main screen once reconnected.
  useEffect(() => {
    if (s.connection !== 'connected') setScreen('main')
  }, [s.connection])

  if (!hasBluetooth && !mock) {
    return (
      <main class="screen center">
        <h1 class="title">BULLOADER+</h1>
        <p class="error" role="alert">
          Web Bluetooth indisponible. Utilise Chrome sur Android.
        </p>
      </main>
    )
  }

  // TODO(#10): when the link drops mid-session, show a "Connexion perdue" banner over the main
  // screen and reconnect, instead of falling back to the connect screen.
  if (s.connection !== 'connected') return <ConnectScreen s={s} />

  if (screen === 'settings') return <SettingsScreen s={s} onBack={() => setScreen('main')} />
  return <MainScreen s={s} onSettings={() => setScreen('settings')} />
}

function ConnectScreen({ s }: { s: DeviceState }) {
  const busy = s.connection === 'connecting'
  return (
    <main class="screen center">
      <h1 class="title">BULLOADER+</h1>
      <button class="btn primary wide" type="button" disabled={busy} onClick={() => ble.connect()}>
        {busy ? 'Connexion…' : 'Connecter'}
      </button>
      {s.connection === 'incompatible' ? (
        <p class="error" role="alert">
          Firmware incompatible : mets à jour l'app ou le BULLOADER.
        </p>
      ) : (
        s.error && (
          <p class="error" role="alert">
            {connectionErrorText(s.error)}
          </p>
        )
      )}
      {mock && <p class="hint">Mode démo (?mock) : pas de vrai appareil.</p>}
    </main>
  )
}

function MainScreen({ s, onSettings }: { s: DeviceState; onSettings: () => void }) {
  const running = isRunning(s.state)
  const alarm = s.state === State.Jam || s.state === State.LowBatt
  const ratio = progress(s.count, s.target)

  return (
    <main class="screen main">
      <header class="bar">
        <span class="device">{s.deviceName}</span>
        {s.battery !== null && (
          <span class={`battery ${batteryLevel(s.battery)}`}>{batteryText(s.battery)}</span>
        )}
        <button class="btn icon" type="button" aria-label="Réglages" onClick={onSettings}>
          ⚙
        </button>
      </header>

      <section class="status" aria-live="polite">
        <p class={alarm ? 'state alarm' : 'state'}>{s.state === null ? '—' : stateLabel[s.state]}</p>
        <p class="count">
          <span>{s.count ?? '—'}</span>
          <span class="of"> / {s.target ?? '—'}</span>
        </p>
        <div
          class="progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={s.target ?? 0}
          aria-valuenow={s.count ?? 0}
        >
          <div class="fill" style={{ width: `${ratio * 100}%` }} />
        </div>
      </section>

      <TargetField target={s.target} disabled={running} />

      <div class="presets">
        {(s.presets ?? []).slice(0, PRESET_COUNT).map((p, i) => (
          <button
            key={i}
            class={p === s.target ? 'btn chip current' : 'btn chip'}
            type="button"
            disabled={running}
            onClick={() => ble.setTarget(p).catch(ignore)}
          >
            {p}
          </button>
        ))}
      </div>

      <div class="actions">
        <button class="btn go" type="button" disabled={!canGo(s.state)} onClick={() => ble.go().catch(ignore)}>
          GO
        </button>
        <button class="btn stop" type="button" onClick={() => ble.stop().catch(ignore)}>
          STOP
        </button>
      </div>

      <button class="btn quiet" type="button" onClick={() => disconnect()}>
        Déconnecter
      </button>
    </main>
  )
}

// The target with − / + and a field. The field shows the device's target; while it has focus it
// holds what the user is typing, sent once on blur or Enter. Whatever the device answers replaces it.
function TargetField({ target, disabled }: { target: number | null; disabled: boolean }) {
  const [draft, setDraft] = useState<string | null>(null)
  // Escape blurs the field too; this tells the blur not to send.
  const cancelled = useRef(false)

  function commit(text: string) {
    setDraft(null)
    if (cancelled.current) {
      cancelled.current = false
      return
    }
    const n = parseTarget(text)
    if (n !== null && n !== target) ble.setTarget(n).catch(ignore)
  }

  function step(delta: number) {
    if (target === null) return
    const n = clampTarget(target + delta)
    if (n !== target) ble.setTarget(n).catch(ignore)
  }

  return (
    <div class="target">
      <label for="target" class="label">
        Objectif
      </label>
      <div class="stepper">
        <button
          class="btn step"
          type="button"
          aria-label="Moins un"
          disabled={disabled || target === null}
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
          disabled={disabled || target === null}
          value={draft ?? (target === null ? '' : String(target))}
          onFocus={(e) => {
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
          aria-label="Plus un"
          disabled={disabled || target === null}
          onClick={() => step(1)}
        >
          +
        </button>
      </div>
    </div>
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

function SettingsScreen({ s, onBack }: { s: DeviceState; onBack: () => void }) {
  const [draft, setDraft] = useState<SettingsDraft | null>(null)
  const [busy, setBusy] = useState<Busy>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const mounted = useRef(true)

  // Leaving this screen (Retour, or the link dropping back to the connect screen) stops a spin.
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
  const validation = validateSettings(values)
  const errors: Partial<Record<DraftField, string>> = validation.ok ? {} : validation.errors
  const atRest = canEditSettings(s.state)
  const canAct = !incompatible && atRest && busy === null && validation.ok
  const testing = s.state === State.Testing

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
    setNotice(kept ? 'Enregistré.' : "L'appareil n'a pas tout pris : voici ses valeurs.")
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
      if (mounted.current) setNotice(`Échec de l'envoi : ${message(error)}`)
    } finally {
      if (mounted.current) setBusy(null)
    }
  }

  return (
    <main class="screen settings">
      <header class="bar">
        <button class="btn icon" type="button" aria-label="Retour" onClick={onBack}>
          ←
        </button>
        <h1 class="bar-title">Réglages</h1>
        <span class={testing ? 'pill active' : 'pill'}>{s.state === null ? '—' : stateLabel[s.state]}</span>
      </header>

      {incompatible && (
        <p class="error" role="alert">
          Firmware incompatible : réglages indisponibles. Mets à jour l'app ou le BULLOADER.
        </p>
      )}

      <section class="group">
        <h2 class="group-title">Préréglages</h2>
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
              aria-label={`Préréglage ${i + 1}`}
              aria-invalid={!!errors[`preset${i}`]}
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
        {PRESET_INDEXES.map((i) => {
          const error = errors[`preset${i}`]
          return (
            error && (
              <p key={i} class="field-error">
                Préréglage {i + 1} : {error}
              </p>
            )
          )
        })}
      </section>

      <section class="group">
        <h2 class="group-title">Chargement</h2>
        <NumberField
          id="slowdown"
          label="Ralentir à N billes de la fin"
          value={values.slowdownN}
          error={errors.slowdownN}
          disabled={incompatible}
          onInput={(slowdownN) => edit({ slowdownN })}
        />
        <NumberField
          id="jam"
          label="Bourrage après (ms sans bille)"
          value={values.jamTimeoutMs}
          error={errors.jamTimeoutMs}
          disabled={incompatible}
          onInput={(jamTimeoutMs) => edit({ jamTimeoutMs })}
        />
      </section>

      <section class="group">
        <h2 class="group-title">Servo</h2>
        <div class="target">
          <label for="neutral" class="label">
            Neutre (µs)
          </label>
          <div class="stepper">
            <button
              class="btn step small"
              type="button"
              aria-label={`Moins ${NEUTRAL_STEP_US} µs`}
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
              disabled={incompatible}
              value={values.servoNeutralUs}
              onInput={(e) => edit({ servoNeutralUs: e.currentTarget.value })}
            />
            <button
              class="btn step small"
              type="button"
              aria-label={`Plus ${NEUTRAL_STEP_US} µs`}
              disabled={incompatible}
              onClick={() => neutralStep(NEUTRAL_STEP_US)}
            >
              +{NEUTRAL_STEP_US}
            </button>
          </div>
          {errors.servoNeutralUs && <p class="field-error">{errors.servoNeutralUs}</p>}
        </div>
        <NumberField
          id="full"
          label="Écart vitesse rapide (µs)"
          value={values.speedFullOffsetUs}
          error={errors.speedFullOffsetUs}
          disabled={incompatible}
          signed
          onInput={(speedFullOffsetUs) => edit({ speedFullOffsetUs })}
        />
        <NumberField
          id="slow"
          label="Écart vitesse lente (µs)"
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
          <span>Sens inversé</span>
          <span class="toggle-value">{values.reverse ? 'OUI' : 'NON'}</span>
        </button>
      </section>

      <section class="group">
        {!validation.ok && !incompatible && (
          <p class="field-error" role="alert">
            Corrige les valeurs en rouge pour enregistrer.
          </p>
        )}
        {!atRest && !testing && !incompatible && <p class="hint">Moteur en marche : arrête-le pour enregistrer ou tester.</p>}
        {notice && (
          <p class="hint" role="status">
            {notice}
          </p>
        )}
        <button class="btn primary" type="button" disabled={!canAct || !dirty} onClick={() => run('save')}>
          {busy === 'save' ? 'Enregistrement…' : 'Enregistrer'}
        </button>
      </section>

      <section class="group">
        <h2 class="group-title">Test du moteur</h2>
        {testing ? (
          <p class="spin-live" aria-live="polite">
            Test en cours : le moteur tourne.
          </p>
        ) : (
          <p class="hint">
            {dirty ? 'Chaque test enregistre d’abord tes changements.' : 'Tourne avec les valeurs enregistrées.'}
          </p>
        )}
        <div class="actions">
          <button class="btn" type="button" disabled={!canAct} onClick={() => run('full')}>
            {busy === 'full' ? '…' : 'Tester rapide'}
          </button>
          <button class="btn" type="button" disabled={!canAct} onClick={() => run('slow')}>
            {busy === 'slow' ? '…' : 'Tester lent'}
          </button>
        </div>
        <button class="btn stop" type="button" onClick={() => stopSpin().catch(ignore)}>
          STOP
        </button>
      </section>
    </main>
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
        disabled={props.disabled}
        value={props.value}
        onInput={(e) => props.onInput(e.currentTarget.value)}
      />
      {props.error && <p class="field-error">{props.error}</p>}
    </div>
  )
}

