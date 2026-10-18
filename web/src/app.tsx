// The whole app: one island, every screen in it. Changing page would drop the Bluetooth link.
// Screens only read the store and call ble.*; the ESP32 owns the state.

import { useRef, useState } from 'preact/hooks'
import { createBle } from './ble/ble.ts'
import { isMockRequested, requestLink } from './ble/link.ts'
import { PRESET_COUNT, State } from './ble/protocol.ts'
import { type DeviceState, useStore } from './ble/store.ts'
import {
  batteryLevel,
  batteryText,
  canGo,
  clampTarget,
  connectionErrorText,
  isRunning,
  parseTarget,
  progress,
  stateLabel,
} from './ui/rules.ts'

const hasBluetooth = typeof navigator !== 'undefined' && 'bluetooth' in navigator
const mock = isMockRequested()

const ble = createBle({ request: requestLink })

// Settings come with #9: flip this on and fill SettingsScreen.
const SETTINGS_READY = false

type Screen = 'main' | 'settings'

// A write that failed (link dropped mid-way, GATT busy): the store didn't move, so the screen
// already shows the truth. Nothing more to do here.
const ignore = () => {}

export function App() {
  const s = useStore(ble.store)
  const [screen, setScreen] = useState<Screen>('main')

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

  if (screen === 'settings') return <SettingsScreen onBack={() => setScreen('main')} />
  return <MainScreen s={s} onSettings={SETTINGS_READY ? () => setScreen('settings') : null} />
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

function MainScreen({ s, onSettings }: { s: DeviceState; onSettings: (() => void) | null }) {
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
        {onSettings && (
          <button class="btn icon" type="button" aria-label="Réglages" onClick={onSettings}>
            ⚙
          </button>
        )}
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

      <button class="btn quiet" type="button" onClick={() => ble.disconnect()}>
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

// Placeholder for #9.
function SettingsScreen({ onBack }: { onBack: () => void }) {
  return (
    <main class="screen center">
      <h1 class="title">Réglages</h1>
      <button class="btn primary wide" type="button" onClick={onBack}>
        Retour
      </button>
    </main>
  )
}
