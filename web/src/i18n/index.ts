// The app's two languages. No library: two dictionaries (fr.ts, en.ts) and t().
//
// The language follows the phone (navigator.language: French if it starts with "fr", English
// otherwise) until the user picks one in the app; that choice is kept in localStorage. Switching
// only re-renders the island: no navigation, which would drop the Bluetooth link.

import { createStore, type Store } from '../ble/store.ts'
import { en } from './en.ts'
import { fr } from './fr.ts'

export type Lang = 'fr' | 'en'
export type Key = keyof typeof fr
export type Vars = Record<string, string | number>

export const LANGS: readonly Lang[] = ['fr', 'en']
// Each language named in its own language, for the switch.
export const LANG_NAMES: Record<Lang, string> = { fr: 'Français', en: 'English' }

export const dictionaries: Record<Lang, Record<Key, string>> = { fr, en }

const STORAGE_KEY = 'bulloader-plus.lang'

export function translate(lang: Lang, key: Key, vars?: Vars): string {
  const text = dictionaries[lang][key]
  if (!vars) return text
  return text.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match))
}

export function detectLang(language: string | undefined | null): Lang {
  return language?.toLowerCase().startsWith('fr') ? 'fr' : 'en'
}

// The part of localStorage used here, so tests can pass a fake one.
export type LangStorage = Pick<Storage, 'getItem' | 'setItem'>

// localStorage can be missing, or throw on access (blocked site data, some private modes).
function defaultStorage(): LangStorage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage
  } catch {
    return null
  }
}

function browserLanguage(): string | undefined {
  return typeof navigator === 'undefined' ? undefined : navigator.language
}

// The language picked in the app if there is one, else the phone's.
export function initialLang(storage: LangStorage | null, language: string | undefined): Lang {
  try {
    const stored = storage?.getItem(STORAGE_KEY)
    if (stored === 'fr' || stored === 'en') return stored
  } catch {
    // Unreadable storage: fall back to the phone's language.
  }
  return detectLang(language)
}

export function storeLang(storage: LangStorage | null, lang: Lang): void {
  try {
    storage?.setItem(STORAGE_KEY, lang)
  } catch {
    // Not kept for next time, but the switch still works for this visit.
  }
}

// Numbers the way each language writes them: « 7,90 » in French, "7.90" in English.
export function formatNumber(lang: Lang, n: number, digits = 0): string {
  return new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    useGrouping: false,
  }).format(n)
}

// ---- The app's current language ----

export const langStore: Store<{ lang: Lang }> = createStore({
  lang: initialLang(defaultStorage(), browserLanguage()),
})

function applyToDocument(lang: Lang): void {
  if (typeof document !== 'undefined') document.documentElement.lang = lang
}
applyToDocument(langStore.get().lang)

export function setLang(lang: Lang): void {
  storeLang(defaultStorage(), lang)
  applyToDocument(lang)
  langStore.set({ lang })
}

// In the current language. Components re-render on a switch because App reads langStore.
export function t(key: Key, vars?: Vars): string {
  return translate(langStore.get().lang, key, vars)
}
