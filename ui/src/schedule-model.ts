export type Reminder = { id: string; title: string; dueAt: number; done: boolean }
export type LocalTimer = { id: string; title: string; durationMs: number; remainingMs: number; endsAt: number | null; finished: boolean }
export type TimerPreset = { title: string; durationSeconds: number }

export function remaining(timer: LocalTimer, now: number) {
  return timer.endsAt === null ? timer.remainingMs : Math.max(0, timer.endsAt - now)
}

export function toggleTimer(timer: LocalTimer, now: number): LocalTimer {
  if (timer.finished) return { ...timer, remainingMs: timer.durationMs, endsAt: now + timer.durationMs, finished: false }
  if (timer.endsAt === null) return { ...timer, endsAt: now + timer.remainingMs }
  const rest = remaining(timer, now)
  return { ...timer, remainingMs: rest, endsAt: null, finished: rest === 0 }
}

export function finishTimers(timers: LocalTimer[], now: number) {
  return timers.map(timer => timer.endsAt !== null && timer.endsAt <= now ? { ...timer, endsAt: null, remainingMs: 0, finished: true } : timer)
}

export function clock(ms: number) {
  const seconds = Math.max(0, Math.ceil(ms / 1000))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor(seconds / 60) % 60
  return `${hours ? `${String(hours).padStart(2, '0')}:` : ''}${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}

export function localDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object'
export function isTimerPreset(value: unknown): value is TimerPreset {
  return record(value) && typeof value.title === 'string' && !!value.title.trim() && value.title.length <= 160 &&
    typeof value.durationSeconds === 'number' && Number.isInteger(value.durationSeconds) &&
    value.durationSeconds > 0 && value.durationSeconds < 86400
}

export function isReminder(value: unknown): value is Reminder {
  return record(value) && typeof value.id === 'string' && typeof value.title === 'string' && typeof value.dueAt === 'number' && Number.isFinite(value.dueAt) && typeof value.done === 'boolean'
}
export function isTimer(value: unknown): value is LocalTimer {
  return record(value) && typeof value.id === 'string' && typeof value.title === 'string' && typeof value.durationMs === 'number' && Number.isFinite(value.durationMs) && value.durationMs > 0 && typeof value.remainingMs === 'number' && Number.isFinite(value.remainingMs) && value.remainingMs >= 0 && (value.endsAt === null || (typeof value.endsAt === 'number' && Number.isFinite(value.endsAt))) && typeof value.finished === 'boolean'
}
