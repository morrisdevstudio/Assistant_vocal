import assert from 'node:assert/strict'
import test from 'node:test'
import { applyAppearance, characters, defaults, loadPreferences, parsePreferences, selectedCharacter } from '../src/preferences.ts'

test('un personnage associe sa voix et son réveil, sans requalifier un ancien réglage différent', () => {
  for (const character of characters) {
    const saved = parsePreferences(JSON.parse(JSON.stringify({ ...defaults, voice: character.voice, wakeWord: character.wakeWord })))
    assert.equal(selectedCharacter(saved), character.id)
  }
  const existing = parsePreferences({ ...defaults, voice: 'phonon-dumby-cpu', wakeWord: 'Alfredo' })
  assert.equal(selectedCharacter(existing), 'custom')
  assert.equal(existing.wakeWord, 'Alfredo')
})

test('les préférences anciennes ou incomplètes gardent des valeurs utilisables', () => {
  assert.deepEqual(parsePreferences(null), defaults)
  const result = parsePreferences({ theme: 'light', voice: 'retired-engine', speechRate: Infinity, textSize: 'huge' })
  assert.equal(result.theme, 'light')
  assert.equal(result.voice, 'server')
  assert.equal(result.speechRate, 1)
  assert.equal('textSize' in result, false)
  assert.equal('reducedMotion' in parsePreferences({ reducedMotion: true }), false)
  assert.equal(result.webSearch, 'when-needed')
  assert.equal(result.musicCategory, 'Artistes')
  assert.equal(result.timerTone, 'classic')
})

test('les nouveaux réglages sont restaurés et les valeurs inconnues sont ignorées', () => {
  const chosen = { webSearch: 'on-request', musicCategory: 'Playlists', musicPlayer: 'media_player.bureau', timerTone: 'chime' }
  assert.deepEqual(parsePreferences(JSON.parse(JSON.stringify(chosen))), { ...defaults, ...chosen })
  assert.deepEqual(parsePreferences({ webSearch: 'always', musicCategory: 'Autre', musicPlayer: 'light.bureau', timerTone: 'absent' }), defaults)
})

test('le thème système suit le téléphone et le thème explicite prime', () => {
  const properties = new Map()
  const root = { dataset: { motion: 'reduced' }, style: { setProperty: (key, value) => properties.set(key, value) } }
  let themeColor
  globalThis.document = { documentElement: root, querySelector: () => ({ setAttribute: (_, value) => { themeColor = value } }) }
  globalThis.matchMedia = () => ({ matches: true })
  applyAppearance({ ...defaults, theme: 'system' })
  assert.equal(root.dataset.theme, 'light')
  assert.equal(themeColor, '#f8f8f7')
  assert.equal(root.dataset.motion, undefined)
  assert.equal(properties.get('--text-scale'), '1')
  applyAppearance({ ...defaults, theme: 'dark' })
  assert.equal(root.dataset.theme, 'dark')
  assert.equal(themeColor, '#212121')
})

test('les préférences enregistrées reviennent sans écriture lors du chargement', () => {
  globalThis.localStorage = { getItem: () => JSON.stringify({ ...defaults, textSize: 'extra-large', voice: 'phonon-dumby-cpu', followupSeconds: 12 }) }
  const loaded = loadPreferences()
  assert.equal(loaded.error, '')
  assert.equal(loaded.preferences.voice, 'phonon-dumby-cpu')
  assert.equal(loaded.preferences.dialogue, true)
  assert.equal(parsePreferences({ dialogue: false }).dialogue, false)
  assert.equal('textSize' in loaded.preferences, false)
})

test('stockage refusé ou corrompu : repli explicite sans écrasement', () => {
  globalThis.localStorage = { getItem: () => { throw Error('denied') } }
  assert.notEqual(loadPreferences().error, '')
  globalThis.localStorage = { getItem: () => '{invalid' }
  const loaded = loadPreferences()
  assert.notEqual(loaded.error, '')
  assert.deepEqual(loaded.preferences, defaults)
})
