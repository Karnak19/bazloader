// Every user-facing string of the app, in French. French is the original language and this file is
// the list of keys: en.ts must have exactly the same ones, or tsc fails.
//
// {name} is replaced by t()'s second argument. French typography: a non-breaking space ( )
// before « : » and units, and inside « ».

export const fr = {
  // Language switch. Each language is named in its own language, on purpose.
  'lang.title': 'Langue',

  'app.noBluetooth': 'Web Bluetooth indisponible. Utilise Chrome sur Android.',

  'banner.reconnecting': 'Déconnecté — reconnexion…',
  'banner.lost': 'Connexion perdue. Rallume le BULLOADER ou rapproche-toi.',
  'banner.retry': 'Reconnecter',
  'banner.changeDevice': "Changer d'appareil",

  'connect.button': 'Connecter',
  'connect.busy': 'Connexion…',
  'connect.searching': 'Recherche du BULLOADER déjà utilisé…',
  'connect.incompatible': "Firmware incompatible : mets à jour l'app ou le BULLOADER.",
  'connect.mock': 'Mode démo (?mock) : pas de vrai appareil.',

  // Same words as the OLED (firmware/src/screen.cpp), so the phone and the device can be matched.
  'state.idle': 'Prêt',
  'state.running': 'Chargement',
  'state.slowdown': 'Ralenti',
  'state.done': 'Terminé',
  'state.jam': 'Bourrage / trémie vide',
  'state.lowBatt': 'Batterie faible',
  'state.testing': 'Test moteur',

  'main.settings': 'Réglages',
  'main.disconnect': 'Déconnecter',
  'main.target': 'Objectif',
  'main.minusOne': 'Moins un',
  'main.plusOne': 'Plus un',

  'error.cancelled': 'Aucun appareil choisi.',
  'error.bluetoothOff': 'Le Bluetooth du téléphone est désactivé.',
  'error.connect': 'Connexion impossible : {error}',
  'error.notConnected': 'Pas connecté.',
  'error.send': "Échec de l'envoi : {error}",

  'settings.title': 'Réglages',
  'settings.back': 'Retour',
  'settings.incompatible':
    "Firmware incompatible : réglages indisponibles. Mets à jour l'app ou le BULLOADER.",
  'settings.presets': 'Préréglages',
  'settings.preset': 'Préréglage {n}',
  'settings.presetError': 'Préréglage {n} : {error}',
  'settings.loading': 'Chargement',
  'settings.slowdown': 'Ralentir à N billes de la fin',
  'settings.jam': 'Bourrage après (ms sans bille)',
  'settings.servo': 'Servo',
  'settings.neutral': 'Neutre (µs)',
  'settings.minusUs': 'Moins {n} µs',
  'settings.plusUs': 'Plus {n} µs',
  'settings.fullOffset': 'Écart vitesse rapide (µs)',
  'settings.slowOffset': 'Écart vitesse lente (µs)',
  'settings.reverse': 'Sens inversé',
  'settings.yes': 'OUI',
  'settings.no': 'NON',
  'settings.fixErrors': 'Corrige les valeurs en rouge pour enregistrer.',
  'settings.motorRunning': 'Moteur en marche : arrête-le pour enregistrer ou tester.',
  'settings.save': 'Enregistrer',
  'settings.saving': 'Enregistrement…',
  'settings.saved': 'Enregistré.',
  'settings.notKept': "L'appareil n'a pas tout pris : voici ses valeurs.",
  'settings.motorTest': 'Test du moteur',
  'settings.testOffline': 'Connexion perdue : le BULLOADER arrête le moteur de lui-même.',
  'settings.testRunning': 'Test en cours : le moteur tourne.',
  'settings.testSavesFirst': 'Chaque test enregistre d’abord tes changements.',
  'settings.testSaved': 'Tourne avec les valeurs enregistrées.',
  'settings.testFull': 'Tester rapide',
  'settings.testSlow': 'Tester lent',

  // {unit} is empty or starts with a non-breaking space (« 1000 µs »).
  'validation.integer': 'Nombre entier attendu, entre {min} et {max}{unit}.',
  'validation.range': 'Doit être entre {min} et {max}{unit}.',
}
