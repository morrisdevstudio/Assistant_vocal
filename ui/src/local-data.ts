import { HOUSE_KEY } from './house-model'
import { PREFERENCES_KEY } from './preferences'

export const SHOPPING_KEY = 'alfred.shopping.v1'
export const REMINDERS_KEY = 'alfred.reminders.v1'
export const TIMERS_KEY = 'alfred.timers.v1'
export const TIMER_PRESETS_KEY = 'alfred.timer-presets.v1'

const collections = {
  preferences: PREFERENCES_KEY,
  maison: HOUSE_KEY,
  courses: SHOPPING_KEY,
  rappels: REMINDERS_KEY,
  minuteries: TIMERS_KEY,
  modelesMinuteries: TIMER_PRESETS_KEY,
}

export function exportLocalData(storage: Pick<Storage, 'getItem'>) {
  const data = Object.fromEntries(Object.entries(collections).map(([name, key]) => {
    const value = storage.getItem(key)
    return [name, value === null ? null : JSON.parse(value)]
  }))
  return JSON.stringify({ format: 1, donnees: data }, null, 2)
}
