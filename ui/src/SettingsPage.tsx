import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, Check, ChevronRight, Info, Monitor, Moon, Sun } from 'lucide-react'
import type { Preferences } from './preferences'
import { characters, selectedCharacter, voices } from './preferences'
import { HouseSettings } from './HouseSettings'
import { TerminalLedSettings } from './TerminalLedSettings'
import { AISettings, DiagnosticSettings, MusicSettings, NotificationSettings, PreferenceGroup, PrivacySettings } from './SettingsDetails'
import { useRemote } from './backend'
import type { SettingsSection } from './navigation'
import { settingsSections } from './settings-sections'

function Toggle({ label, description, checked, onChange, disabled }: { label: string; description: string; checked: boolean; onChange: (value: boolean) => void; disabled: boolean }) {
  return <label className="preference-toggle-row"><span><strong>{label}</strong><small>{description}</small></span><input type="checkbox" role="switch" checked={checked} onChange={event => onChange(event.target.checked)} disabled={disabled} /><span className="preference-switch" aria-hidden="true" /></label>
}

export function SettingsPage({ section, preferences, onChange, error, blocked, onOpen, onBack }: { section: SettingsSection; preferences: Preferences; onChange: (patch: Partial<Preferences>) => boolean; error: string; blocked: boolean; onOpen: (section: SettingsSection) => void; onBack?: () => void }) {
  const voice = useRemote<{ tts_available: boolean; tts_voice: string }>(section === 'voice' ? 'voice/status' : null)
  const [notice, setNotice] = useState('')
  const scroller = useRef<HTMLDivElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = 0
    heading.current?.focus({ preventScroll: true })
  }, [section])

  function save(patch: Partial<Preferences>) {
    if (onChange(patch)) setNotice('Préférence enregistrée sur cet appareil.')
  }
  const title = settingsSections.find(item => item.page === section)?.title ?? 'Paramètres'
  const controls = { preferences, blocked, save }

  return <section className="settings-page" data-section={section} aria-labelledby="settings-heading">
    <div className="settings-scroll" ref={scroller}><div className="settings-content">
      <div className="settings-heading">
        {onBack && <button className="icon-button settings-back" type="button" aria-label={section === 'home' ? 'Revenir à la page précédente' : 'Revenir aux paramètres'} title="Retour" onClick={onBack}><ArrowLeft size={23} /></button>}
        <h1 id="settings-heading" ref={heading} tabIndex={-1}>{title}</h1>
      </div>
      {section === 'house' && <HouseSettings />}
      {section === 'home' && <nav className="settings-sections" aria-label="Rubriques des paramètres">
        {settingsSections.map(({ title, icon: Icon, page }) => <button key={page} type="button" className="settings-section" onClick={() => onOpen(page)}>
          <span className="settings-section-icon"><Icon size={22} strokeWidth={1.6} /></span>
          <span className="settings-section-label"><strong>{title}</strong></span><ChevronRight size={18} />
        </button>)}
      </nav>}
      {section === 'ai' && <AISettings {...controls} />}
      {section === 'music' && <MusicSettings {...controls} />}
      {section === 'notifications' && <NotificationSettings {...controls} />}
      {section === 'privacy' && <PrivacySettings />}
      {section === 'diagnostic' && <DiagnosticSettings />}
      {section === 'appearance' && <PreferenceGroup title="Thème">
        <div className="theme-options" role="group" aria-label="Thème de l’application">{[{ id: 'dark', label: 'Sombre', icon: Moon }, { id: 'light', label: 'Clair', icon: Sun }, { id: 'system', label: 'Système', icon: Monitor }].map(({ id, label, icon: Icon }) => <button type="button" key={id} aria-pressed={preferences.theme === id} disabled={blocked} onClick={() => save({ theme: id as Preferences['theme'] })}><Icon size={25} strokeWidth={1.5} /><span>{label}</span>{preferences.theme === id && <Check size={14} className="theme-selected" />}</button>)}</div>
      </PreferenceGroup>}
      {section === 'voice' && <>
        <p className="settings-voice-note"><Info size={18} /><span>La lecture et le débit s’appliquent dans le navigateur. Le serveur fournit sa voix actuelle. Personnage, mot de réveil et écoute enchaînée restent des préférences locales.</span></p>
        <PreferenceGroup title="Synthèse du serveur">
          <dl className="settings-facts"><div><dt>Voix utilisée par Alfred</dt><dd>{voice.error ? 'Indisponible' : voice.data ? voice.data.tts_available ? voice.data.tts_voice : 'Synthèse indisponible' : 'Chargement…'}</dd></div></dl>
        </PreferenceGroup>
        <PreferenceGroup title="Personnage">
          <div className="character-choice">
            <label className="sr-only" htmlFor="character-choice">Choisir un personnage</label>
            <select id="character-choice" value={selectedCharacter(preferences)} disabled={blocked} onChange={event => { const character = characters.find(item => item.id === event.target.value); if (character) save({ voice: character.voice, wakeWord: character.wakeWord }) }}>
              {selectedCharacter(preferences) === 'custom' && <option value="custom" disabled>Réglage existant personnalisé</option>}
              {characters.map(character => <option key={character.id} value={character.id}>{character.name}</option>)}
            </select>
            <dl className="character-details"><div><dt>Voix</dt><dd>{voices.find(voice => voice.id === preferences.voice)?.name || 'Voix du serveur'}</dd></div><div><dt>Mot de réveil</dt><dd>{preferences.wakeWord || 'Celui du serveur'}</dd></div></dl>
          </div>
          <label className="preference-range"><span><strong>Débit de lecture</strong><output>{preferences.speechRate.toFixed(2).replace('.', ',')}×</output></span><input type="range" min={.8} max={1.3} step={.05} value={preferences.speechRate} disabled={blocked} onChange={event => save({ speechRate: Number(event.target.value) })} /><span className="range-labels"><small>Plus posé</small><small>Plus rapide</small></span></label>
        </PreferenceGroup>
        <PreferenceGroup title="Conversation">
          <Toggle label="Lire les réponses écrites" description="Essaie de lire la réponse à un message écrit. L’icône sous la réponse permet aussi de la réécouter." checked={preferences.readReplies} onChange={value => save({ readReplies: value })} disabled={blocked} />
          <Toggle label="Mode dialogue" description="Rouvre le micro pendant 8 secondes quand Alfred attend une confirmation ou une précision à l’oral." checked={preferences.dialogue} onChange={value => save({ dialogue: value })} disabled={blocked} />
        </PreferenceGroup>
        <TerminalLedSettings />
      </>}
      {error && <p className="shopping-error" role="alert">{error}</p>}
      <p className="settings-feedback" role="status">{notice}</p>
    </div></div>
    <footer className="settings-footer">Préférences enregistrées sur cet appareil</footer>
  </section>
}
