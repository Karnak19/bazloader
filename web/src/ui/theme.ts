// Light or dark. « Auto » follows the phone; « Clair » and « Sombre » pin one. The pick is kept in
// localStorage, read before first paint by the inline script in src/pages/app.astro (same key, same
// colours), so the page never flashes the wrong theme. This module takes over once the island runs.

import { createStore, type Store } from '../ble/store.ts'

export type ThemePref = 'auto' | 'light' | 'dark'
export const THEME_PREFS: readonly ThemePref[] = ['auto', 'light', 'dark']

export const THEME_KEY = 'bazloader.theme'
// The browser bar's colour, the page's ground in each theme. Same values as --bg in style.css and
// as the inline script in app.astro.
export const THEME_COLORS = { light: '#f6f4ef', dark: '#0b0c0e' } as const

export type ThemeStorage = Pick<Storage, 'getItem' | 'setItem'>

export function readThemePref(storage: ThemeStorage | null): ThemePref {
  try {
    const stored = storage?.getItem(THEME_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'auto') return stored
  } catch {
    // Unreadable storage: follow the phone.
  }
  return 'auto'
}

export function storeThemePref(storage: ThemeStorage | null, pref: ThemePref): void {
  try {
    storage?.setItem(THEME_KEY, pref)
  } catch {
    // Not kept for next time, but the switch still works for this visit.
  }
}

export function effectiveTheme(pref: ThemePref, systemDark: boolean): 'light' | 'dark' {
  return pref === 'auto' ? (systemDark ? 'dark' : 'light') : pref
}

function defaultStorage(): ThemeStorage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage
  } catch {
    return null
  }
}

const darkQuery =
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

export const themeStore: Store<{ pref: ThemePref }> = createStore({ pref: readThemePref(defaultStorage()) })

// data-theme pins the theme for the CSS; without it, the CSS follows prefers-color-scheme.
function apply(pref: ThemePref): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (pref === 'auto') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', pref)
  const meta = document.querySelector('meta[name="theme-color"]')
  meta?.setAttribute('content', THEME_COLORS[effectiveTheme(pref, darkQuery?.matches ?? true)])
}

apply(themeStore.get().pref)
// In Auto, the phone switching to dark at sunset changes the browser bar too.
darkQuery?.addEventListener('change', () => apply(themeStore.get().pref))

export function setTheme(pref: ThemePref): void {
  storeThemePref(defaultStorage(), pref)
  apply(pref)
  themeStore.set({ pref })
}
