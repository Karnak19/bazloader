import { describe, expect, test } from 'bun:test'
import { en } from './en.ts'
import { fr } from './fr.ts'
import { detectLang, formatNumber, initialLang, type LangStorage, storeLang, translate } from './index.ts'

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort()

describe('dictionaries', () => {
  // tsc already refuses a missing or extra key in en.ts; this also covers a cast slipping through.
  test('fr and en have the same keys', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(fr).sort())
  })

  test('the same placeholders on both sides, and no empty string', () => {
    for (const key of Object.keys(fr) as (keyof typeof fr)[]) {
      expect({ key, vars: placeholders(en[key]) }).toEqual({ key, vars: placeholders(fr[key]) })
      expect(fr[key].trim()).not.toBe('')
      expect(en[key].trim()).not.toBe('')
    }
  })

  // French puts a space before « : ; ! ? » and inside « » quotes; it must not break across lines.
  test('French uses non-breaking spaces where its typography wants one', () => {
    for (const text of Object.values(fr)) {
      expect(text).not.toMatch(/ [:;!?»]/)
      expect(text).not.toMatch(/« /)
    }
  })
})

describe('translate', () => {
  test('fills {placeholders}', () => {
    expect(translate('fr', 'settings.preset', { n: 2 })).toBe('Préréglage 2')
    expect(translate('en', 'settings.presetError', { n: 3, error: 'Too big.' })).toBe('Preset 3: Too big.')
  })

  test('leaves an unknown placeholder visible rather than dropping it', () => {
    expect(translate('en', 'settings.preset')).toBe('Preset {n}')
  })
})

describe('detectLang', () => {
  test('French for any fr-*, English for everything else', () => {
    expect(detectLang('fr')).toBe('fr')
    expect(detectLang('fr-FR')).toBe('fr')
    expect(detectLang('fr-CA')).toBe('fr')
    expect(detectLang('FR-be')).toBe('fr')
    expect(detectLang('en-US')).toBe('en')
    expect(detectLang('de-DE')).toBe('en')
    expect(detectLang('')).toBe('en')
    expect(detectLang(undefined)).toBe('en')
  })
})

function memoryStorage(): LangStorage & { data: Map<string, string> } {
  const data = new Map<string, string>()
  return {
    data,
    getItem: (k) => data.get(k) ?? null,
    setItem: (k, v) => {
      data.set(k, v)
    },
  }
}

const brokenStorage: LangStorage = {
  getItem: () => {
    throw new Error('SecurityError')
  },
  setItem: () => {
    throw new Error('QuotaExceededError')
  },
}

describe('initialLang / storeLang', () => {
  test('follows the phone until a language is picked, then keeps the pick', () => {
    const storage = memoryStorage()
    expect(initialLang(storage, 'fr-FR')).toBe('fr')
    storeLang(storage, 'en')
    expect(initialLang(storage, 'fr-FR')).toBe('en')
    storeLang(storage, 'fr')
    expect(initialLang(storage, 'en-GB')).toBe('fr')
  })

  test('ignores a stored value it does not know', () => {
    const storage = memoryStorage()
    storage.setItem('bazloader.lang', 'de')
    expect(initialLang(storage, 'en-US')).toBe('en')
  })

  test('falls back to the phone when localStorage throws or is missing', () => {
    expect(initialLang(brokenStorage, 'fr-FR')).toBe('fr')
    expect(initialLang(brokenStorage, 'en-US')).toBe('en')
    expect(initialLang(null, 'fr')).toBe('fr')
    expect(() => storeLang(brokenStorage, 'en')).not.toThrow()
    expect(() => storeLang(null, 'en')).not.toThrow()
  })
})

describe('formatNumber', () => {
  test('decimal comma in French, point in English, no grouping', () => {
    expect(formatNumber('fr', 7.9, 2)).toBe('7,90')
    expect(formatNumber('en', 7.9, 2)).toBe('7.90')
    expect(formatNumber('fr', 8.4, 1)).toBe('8,4')
    expect(formatNumber('fr', 10000)).toBe('10000')
    expect(formatNumber('en', 10000)).toBe('10000')
  })
})
