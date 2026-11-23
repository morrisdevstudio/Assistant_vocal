import { useCallback, useEffect, useState } from 'react'

export type AppPage = 'conversation' | 'music' | 'shopping' | 'reminders' | 'timers' | 'settings'
export type SettingsSection = 'home' | 'appearance' | 'voice' | 'house' | 'ai' | 'music' | 'notifications' | 'privacy' | 'diagnostic'

type Screen =
  | { page: 'conversation' | 'music' }
  | { page: 'shopping' | 'reminders' | 'timers'; local?: boolean }
  | { page: 'settings'; section: SettingsSection }
type Entry = { screen: Screen; menuOpen: boolean; settingsDepth?: number }
const home: Entry = { screen: { page: 'conversation' }, menuOpen: false }

export function useNavigation() {
  const [entry, setEntry] = useState<Entry>(() => history.state?.alfred ?? home)

  useEffect(() => {
    if (!history.state?.alfred) history.replaceState({ alfred: home }, '')
    function restore(event: PopStateEvent) {
      setEntry(event.state?.alfred ?? home)
    }
    window.addEventListener('popstate', restore)
    return () => window.removeEventListener('popstate', restore)
  }, [])

  function go(screen: Screen, menuOpen = false) {
    // Le menu sert de choix transitoire. La page choisie prend sa place dans l'historique.
    const replace = entry.menuOpen && !menuOpen
    const next: Entry = { screen, menuOpen }
    if (screen.page === 'settings') {
      next.settingsDepth = entry.screen.page === 'settings'
        ? entry.settingsDepth && entry.settingsDepth + (replace ? 0 : 1)
        : 1
    }
    if (replace) history.replaceState({ alfred: next }, '')
    else history.pushState({ alfred: next }, '')
    setEntry(next)
  }

  const back = useCallback(() => history.back(), [])
  function openPage(page: AppPage) {
    if (page === entry.screen.page) back()
    else go(page === 'settings' ? { page, section: 'home' } : { page })
  }

  function exitSettings() {
    if (entry.settingsDepth) history.go(-entry.settingsDepth)
    else go(home.screen)
  }

  function backToSettingsHome() {
    if (entry.settingsDepth && entry.settingsDepth > 1) history.go(1 - entry.settingsDepth)
    else back()
  }

  return { ...entry, go, back, openPage, exitSettings, backToSettingsHome, openMenu: () => go(entry.screen, true) }
}
