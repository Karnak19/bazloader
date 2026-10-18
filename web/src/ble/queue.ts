// Runs async operations one at a time, in the order they were queued.
// Chrome throws "GATT operation already in progress" when two GATT operations overlap, so every
// read, write and startNotifications goes through one of these. A failed operation rejects its own
// promise and the queue moves on to the next one.

export type Queue = {
  run<T>(op: () => Promise<T>): Promise<T>
}

export function createQueue(): Queue {
  let tail: Promise<unknown> = Promise.resolve()
  return {
    run(op) {
      const result = tail.then(op)
      tail = result.catch(() => {})
      return result
    },
  }
}
