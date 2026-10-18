import { describe, expect, test } from 'bun:test'
import { effectiveTheme, readThemePref, storeThemePref, THEME_KEY, type ThemeStorage } from './theme.ts'

function memoryStorage(): ThemeStorage {
  const data = new Map<string, string>()
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => void data.set(key, value),
  }
}

const brokenStorage: ThemeStorage = {
  getItem: () => {
    throw new Error('SecurityError')
  },
  setItem: () => {
    throw new Error('QuotaExceededError')
  },
}

describe('theme preference', () => {
  test('Auto until one is picked, then keeps the pick', () => {
    const storage = memoryStorage()
    expect(readThemePref(storage)).toBe('auto')
    storeThemePref(storage, 'light')
    expect(readThemePref(storage)).toBe('light')
    storeThemePref(storage, 'dark')
    expect(readThemePref(storage)).toBe('dark')
  })

  test('ignores a stored value it does not know', () => {
    const storage = memoryStorage()
    storage.setItem(THEME_KEY, 'sepia')
    expect(readThemePref(storage)).toBe('auto')
  })

  test('falls back to Auto when localStorage throws or is missing', () => {
    expect(readThemePref(brokenStorage)).toBe('auto')
    expect(readThemePref(null)).toBe('auto')
    expect(() => storeThemePref(brokenStorage, 'dark')).not.toThrow()
  })

  test('Auto follows the phone, a pick ignores it', () => {
    expect(effectiveTheme('auto', true)).toBe('dark')
    expect(effectiveTheme('auto', false)).toBe('light')
    expect(effectiveTheme('light', true)).toBe('light')
    expect(effectiveTheme('dark', false)).toBe('dark')
  })
})
