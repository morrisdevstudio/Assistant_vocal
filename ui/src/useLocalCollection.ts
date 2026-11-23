import { useRef, useState } from 'react'

export function useLocalCollection<T>(key: string, validate: (value: unknown) => value is T) {
  const [initial] = useState(() => {
    try {
      const value: unknown = JSON.parse(localStorage.getItem(key) || '[]')
      if (!Array.isArray(value) || !value.every(validate)) throw Error()
      return { items: value as T[], error: '' }
    } catch {
      return { items: [] as T[], error: 'Les données enregistrées sur cet appareil sont inaccessibles. Rouvrez l’application pour réessayer.' }
    }
  })
  const [items, setItems] = useState(initial.items)
  const current = useRef(initial.items)
  const [error, setError] = useState(initial.error)
  function update(change: (previous: T[]) => T[]) {
    if (initial.error) return false
    try {
      const next = change(current.current)
      localStorage.setItem(key, JSON.stringify(next))
      current.current = next
      setItems(next)
      setError('')
      return true
    } catch {
      setError('Enregistrement impossible. La dernière modification n’a pas été sauvegardée.')
      return false
    }
  }
  return { items, update, error, blocked: !!initial.error, current }
}
