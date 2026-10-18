const hasBluetooth = typeof navigator !== 'undefined' && 'bluetooth' in navigator

export function App() {
  return (
    <main class="screen">
      <h1 class="title">BULLOADER+</h1>
      {hasBluetooth ? (
        <>
          <button class="primary" type="button" disabled>
            Connecter
          </button>
          <p class="hint">Bientôt disponible</p>
        </>
      ) : (
        <p class="error" role="alert">
          Web Bluetooth indisponible. Utilise Chrome sur Android.
        </p>
      )}
    </main>
  )
}
