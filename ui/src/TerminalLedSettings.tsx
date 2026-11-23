import { useState } from 'react'
import { backendJson, jsonPost, useRemote, useServerAction } from './backend'
import { PreferenceGroup } from './SettingsDetails'

const states = [
  ['standby', 'Veille'],
  ['listening', 'Écoute'],
  ['processing', 'Traitement'],
  ['speaking', 'Réponse parlée'],
  ['error', 'Erreur'],
] as const

type Phase = typeof states[number][0]
const effectLabels = { solid: 'Fixe', rotation: 'Rotation', comet: 'Comète', breathing: 'Respiration', scan: 'Balayage' } as const
type Effect = keyof typeof effectLabels
type Colors = Record<Phase, string | null>
type Effects = Record<Phase, Effect>
type LedSettings = {
  colors: Colors; defaults: Colors; effects: Effects; effect_options: Effect[];
  connected: boolean; supported: boolean
}

export function TerminalLedSettings() {
  const remote = useRemote<LedSettings>('terminal/leds')
  const action = useServerAction()
  const [saved, setSaved] = useState<LedSettings>()
  const [changes, setChanges] = useState<Partial<Colors>>({})
  const [effects, setEffects] = useState<Partial<Effects>>({})
  const dirty = Object.keys(changes).length > 0 || Object.keys(effects).length > 0
  const data = saved ?? remote.data

  function change(phase: Phase, color: string | null) {
    const next = { ...changes }
    if (color === data?.colors[phase]) delete next[phase]
    else next[phase] = color
    setChanges(next)
  }

  function changeEffect(phase: Phase, effect: Effect) {
    const next = { ...effects }
    if (effect === data?.effects[phase]) delete next[phase]
    else next[phase] = effect
    setEffects(next)
  }

  async function save() {
    if (!dirty) return
    const response = await action.run(() => backendJson<LedSettings>('terminal/leds', jsonPost({ colors: changes, effects })))
    if (response) {
      setSaved(response)
      setChanges({})
      setEffects({})
    }
  }

  return <PreferenceGroup title="LED du satellite ESP32">
    {remote.error && !data && <p className="settings-card-intro" role="alert">{remote.error}</p>}
    {!remote.error && !data && <p className="settings-card-intro" role="status">Chargement des réglages…</p>}
    {data && <form onSubmit={event => { event.preventDefault(); void save() }}>
      <p className="settings-card-intro">Les couleurs et effets sont enregistrés sur le serveur Alfred.</p>
      {!data.connected && <p className="settings-card-intro">Satellite déconnecté. Les réglages s’appliqueront à sa reconnexion.</p>}
      {data.connected && !data.supported && <p className="settings-card-intro">Anneau RGB indisponible sur ce satellite.</p>}
      {states.map(([phase, label]) => {
        const color = (phase in changes ? changes[phase] : data.colors[phase]) ?? null
        const swatch = color ?? data.defaults[phase] ?? '#FFFFFF'
        const effect = effects[phase] ?? data.effects[phase]
        return <div className="terminal-led-row" key={phase}>
          <label htmlFor={`led-${phase}`}>{label}</label>
          <input id={`led-${phase}`} type="color" value={swatch} disabled={action.busy}
            onChange={event => change(phase, event.target.value === '#000000' ? null : event.target.value.toUpperCase())} />
          <label className="terminal-led-toggle">
            <input type="checkbox" aria-label={`Allumer la LED en mode ${label.toLowerCase()}`} checked={color !== null}
              disabled={action.busy} onChange={event => change(phase, event.target.checked ? swatch : null)} />
            {color ? 'Allumé' : 'Éteint'}
          </label>
          <select aria-label={`Effet en mode ${label.toLowerCase()}`} value={effect} disabled={action.busy}
            onChange={event => changeEffect(phase, event.target.value as Effect)}>
            {!data.effect_options.includes(effect) && <option disabled value={effect}>{effectLabels[effect]} · indisponible</option>}
            {data.effect_options.map(option => <option key={option} value={option}>{effectLabels[option]}</option>)}
          </select>
        </div>
      })}
      <div className="settings-card-action">
        <button className="timer-toggle" type="submit" disabled={action.busy || !dirty}>
          {action.busy ? 'Enregistrement…' : 'Enregistrer les réglages LED'}
        </button>
      </div>
      {action.error && <p className="settings-card-intro" role="alert">{action.error}</p>}
      {saved && !dirty && <p className="settings-card-intro" role="status">Réglages LED enregistrés.</p>}
    </form>}
  </PreferenceGroup>
}
