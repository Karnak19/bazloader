import { createBle } from './ble/ble.ts'
import { isMockRequested, requestLink } from './ble/link.ts'
import { State } from './ble/protocol.ts'
import { useStore } from './ble/store.ts'

const hasBluetooth = typeof navigator !== 'undefined' && 'bluetooth' in navigator
const mock = isMockRequested()

const ble = createBle({ request: requestLink })

const stateNames = Object.fromEntries(Object.entries(State).map(([name, value]) => [value, name]))

// TEMPORARY debug view: raw values from the store, to exercise the BLE layer by hand (real device
// or ?mock). The real screens replace it in #8 and #9.
function DebugView() {
  const s = useStore(ble.store)
  const busy = s.connection === 'connecting'
  const connected = s.connection === 'connected'
  return (
    <>
      {connected ? (
        <button class="primary" type="button" onClick={() => ble.disconnect()}>
          Déconnecter
        </button>
      ) : (
        <button class="primary" type="button" disabled={busy} onClick={() => ble.connect()}>
          {busy ? 'Connexion…' : 'Connecter'}
        </button>
      )}
      {s.connection === 'incompatible' && (
        <p class="error" role="alert">
          Firmware incompatible : mets à jour l'app ou le BULLOADER.
        </p>
      )}
      {s.error && <p class="hint">{s.error}</p>}
      <pre class="hint" style={{ textAlign: 'left' }}>
        {[
          `appareil   ${s.deviceName ?? '—'}${mock ? ' (?mock)' : ''}`,
          `connexion  ${s.connection}`,
          `état       ${s.state === null ? '—' : stateNames[s.state]}`,
          `billes     ${s.count ?? '—'} / ${s.target ?? '—'}`,
          `batterie   ${s.battery === null ? '—' : `${s.battery} mV`}`,
        ].join('\n')}
      </pre>
      {connected && (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="button" onClick={() => ble.go().catch(() => {})}>
            Go
          </button>
          <button type="button" onClick={() => ble.stop().catch(() => {})}>
            Stop
          </button>
        </div>
      )}
    </>
  )
}

export function App() {
  return (
    <main class="screen">
      <h1 class="title">BULLOADER+</h1>
      {hasBluetooth || mock ? (
        <DebugView />
      ) : (
        <p class="error" role="alert">
          Web Bluetooth indisponible. Utilise Chrome sur Android.
        </p>
      )}
    </main>
  )
}
