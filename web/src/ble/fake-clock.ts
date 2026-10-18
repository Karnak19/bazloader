// Timers that only move when a test says so. Test helper, not shipped.

import type { Clock } from './mock.ts'

export class FakeClock implements Clock {
  private now = 0
  private nextId = 0
  private timers = new Map<number, { at: number; fn: () => void }>()

  setTimeout(fn: () => void, ms: number): unknown {
    const id = this.nextId++
    this.timers.set(id, { at: this.now + ms, fn })
    return id
  }

  clearTimeout(id: unknown): void {
    this.timers.delete(id as number)
  }

  get pending(): number {
    return this.timers.size
  }

  advance(ms: number): void {
    const end = this.now + ms
    for (;;) {
      let next: [number, { at: number; fn: () => void }] | undefined
      for (const entry of this.timers) {
        if (entry[1].at <= end && (!next || entry[1].at < next[1].at)) next = entry
      }
      if (!next) break
      this.timers.delete(next[0])
      this.now = next[1].at
      next[1].fn()
    }
    this.now = end
  }

  // Moves time in small steps and lets promises settle in between, for code that awaits between
  // timers (a reconnect attempt, then a pause, then another attempt).
  async run(ms: number, step = 50): Promise<void> {
    for (let t = 0; t < ms; t += step) {
      this.advance(Math.min(step, ms - t))
      await new Promise((resolve) => setTimeout(resolve, 0))
    }
  }
}
