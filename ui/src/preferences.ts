export type Preferences = {
  theme: 'dark' | 'light' | 'system'
  voice: string
  speechRate: number
  wakeWord: string
  dialogue: boolean
  readReplies: boolean
  webSearch: 'when-needed' | 'on-request'
  musicCategory: MusicCategory
  musicPlayer: string
  timerTone: TimerTone
}

export const musicCategories = ['Artistes', 'Albums', 'Titres', 'Playlists'] as const
export type MusicCategory = typeof musicCategories[number]
export const timerTones = [
  { id: 'classic', label: 'Trois bips' },
  { id: 'chime', label: 'Carillon' },
] as const
export type TimerTone = typeof timerTones[number]['id']

export const PREFERENCES_KEY = 'alfred.preferences.v1'
export const voices = [
  { id: 'server', name: 'Voix actuelle du serveur' },
  { id: 'phonon-dumby-cpu', name: 'Dumby' },
  { id: 'phonon-alfred-cpu', name: 'Alfred cloné' },
  { id: 'phonon-arnaud-cpu', name: 'Arnaud' },
  { id: 'phonon-lucien-cpu', name: 'Lucien' },
]
export const characters = [
  { id: 'server', name: 'Personnage actuel du serveur', voice: 'server', wakeWord: '' },
  { id: 'dumby', name: 'Dumby', voice: 'phonon-dumby-cpu', wakeWord: 'Dumby' },
  { id: 'alfred', name: 'Alfred', voice: 'phonon-alfred-cpu', wakeWord: 'Alfred' },
  { id: 'arnaud', name: 'Arnaud', voice: 'phonon-arnaud-cpu', wakeWord: 'Arnaud' },
  { id: 'lucien', name: 'Lucien', voice: 'phonon-lucien-cpu', wakeWord: 'Lucien' },
]

export function selectedCharacter(preferences: Preferences) {
  return characters.find(character => character.voice === preferences.voice && character.wakeWord === preferences.wakeWord)?.id || 'custom'
}
export const defaults: Preferences = {
  theme: 'dark', voice: 'server', speechRate: 1, wakeWord: '', dialogue: true, readReplies: false,
  webSearch: 'when-needed', musicCategory: 'Artistes', musicPlayer: '', timerTone: 'classic',
}

export function parsePreferences(value: unknown): Preferences {
  if (!value || typeof value !== 'object') return { ...defaults }
  const data = value as Record<string, unknown>
  return {
    theme: ['dark', 'light', 'system'].includes(String(data.theme)) ? data.theme as Preferences['theme'] : defaults.theme,
    voice: voices.some(voice => voice.id === data.voice) ? String(data.voice) : defaults.voice,
    speechRate: typeof data.speechRate === 'number' && data.speechRate >= .8 && data.speechRate <= 1.3 ? data.speechRate : 1,
    wakeWord: typeof data.wakeWord === 'string' ? data.wakeWord.slice(0, 40) : '',
    dialogue: typeof data.dialogue === 'boolean' ? data.dialogue : defaults.dialogue,
    readReplies: typeof data.readReplies === 'boolean' ? data.readReplies : false,
    webSearch: data.webSearch === 'on-request' ? data.webSearch : defaults.webSearch,
    musicCategory: musicCategories.find(category => category === data.musicCategory) ?? defaults.musicCategory,
    musicPlayer: typeof data.musicPlayer === 'string' && /^media_player\.[a-z0-9_]+$/.test(data.musicPlayer) ? data.musicPlayer : '',
    timerTone: timerTones.find(tone => tone.id === data.timerTone)?.id ?? defaults.timerTone,
  }
}

export function loadPreferences() {
  try { return { preferences: parsePreferences(JSON.parse(localStorage.getItem(PREFERENCES_KEY) || '{}')), error: '' } }
  catch { return { preferences: { ...defaults }, error: 'Les préférences enregistrées sont inaccessibles. Aucun réglage existant ne sera écrasé.' } }
}

export function applyAppearance(preferences: Preferences) {
  const root = document.documentElement
  const theme = preferences.theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : preferences.theme
  root.dataset.theme = theme
  // Les anciens réglages retirés de l'interface ne doivent plus rester actifs.
  delete root.dataset.motion
  root.style.setProperty('--text-scale', '1')
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'light' ? '#f8f8f7' : '#212121')
}
