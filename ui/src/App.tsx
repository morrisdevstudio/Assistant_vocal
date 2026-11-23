import { Component, lazy, memo, Suspense, useEffect, useRef, useState, useSyncExternalStore } from 'react'
import type { FormEvent, KeyboardEvent, ReactNode } from 'react'
import { ArrowUp, AudioLines, Globe, Menu, Pause, SquarePen, Volume2 } from 'lucide-react'
import { InstallApp } from './InstallApp'
import { AppMenu, DesktopNavigation, DesktopSettingsNavigation } from './AppMenu'
import { useNavigation } from './navigation'
import { firstSettingsSection } from './settings-sections'
import { ShoppingList } from './ShoppingList'
import { Reminders } from './Reminders'
import { Timers } from './Timers'
import { applyAppearance, loadPreferences, PREFERENCES_KEY } from './preferences'
import type { Preferences } from './preferences'
import { useChat } from './chat'
import type { ChatMessage } from './chat'
import { SharedReminders, SharedTimers } from './SharedSchedules'
import { VoiceControls, VoiceWaveform } from './VoiceControls'

const MusicPage = lazy(() => import('./MusicPage').then(module => ({ default: module.MusicPage })))
const SettingsPage = lazy(() => import('./SettingsPage').then(module => ({ default: module.SettingsPage })))
const desktopViewport = matchMedia('(min-width: 1024px)')

function subscribeToDesktopViewport(onChange: () => void) {
  desktopViewport.addEventListener('change', onChange)
  return () => desktopViewport.removeEventListener('change', onChange)
}

const isDesktopViewport = () => desktopViewport.matches

const examples = ['Quelles lumières sont allumées ?', 'Lance un minuteur de 5 minutes']
const chatStatus = {
  idle: 'Micro fermé',
  permission: 'Autorisez le microphone pour parler à Alfred.',
  recording: 'Micro ouvert',
  transcribing: 'Micro fermé · transcription en cours…',
  waiting: 'Alfred traite votre demande…',
}

class ScreenBoundary extends Component<{ children: ReactNode; active: boolean; back: () => void }> {
  state = { failed: false }

  static getDerivedStateFromError() { return { failed: true } }

  render() {
    if (!this.state.failed) return this.props.children
    return <section className="screen-loading" hidden={!this.props.active}>
      <p role="alert">Impossible de charger cette page.</p>
      <button className="icon-button settings-back" type="button" aria-label="Revenir à la page précédente" onClick={this.props.back}>←</button>
    </section>
  }
}

const MessageBubble = memo(function MessageBubble({ message, playing, audioError, play }: {
  message: ChatMessage
  playing: boolean
  audioError: boolean
  play: (id: string, audio: Blob) => void
}) {
  const user = message.author === 'user'
  const audio = message.audio
  const audioLabel = playing ? 'Mettre la réponse en pause' : 'Écouter la réponse'
  return <article className={user ? 'message' : 'message message-assistant'} aria-label={user ? 'Votre message' : 'Réponse d’Alfred'}>
    <div className={user ? 'user-bubble' : 'assistant-bubble'}>
      {message.text}
      {!!message.sources?.length && <ul className="chat-sources" aria-label="Sources">{message.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer noopener">{source.title}</a></li>)}</ul>}
      {audio && <button className="icon-button reply-audio-button" type="button" aria-label={audioLabel} title={audioLabel}
        onClick={() => play(message.id, audio)}>
        {playing ? <Pause size={18} aria-hidden="true" /> : <Volume2 size={18} aria-hidden="true" />}
      </button>}
      {audioError && <p className="reply-audio-error" role="status">Lecture audio impossible. Réessayez.</p>}
    </div>
  </article>
})

export function App() {
  const [initialPreferences] = useState(loadPreferences)
  const [preferences, setPreferences] = useState(initialPreferences.preferences)
  const [preferencesError, setPreferencesError] = useState(initialPreferences.error)
  useEffect(() => {
    const apply = () => applyAppearance(preferences)
    apply()
    const systemTheme = matchMedia('(prefers-color-scheme: light)')
    systemTheme.addEventListener('change', apply)
    return () => systemTheme.removeEventListener('change', apply)
  }, [preferences])
  function changePreferences(patch: Partial<Preferences>) {
    if (initialPreferences.error) return false
    const next = { ...preferences, ...patch }
    try {
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(next))
      setPreferences(next)
      applyAppearance(next)
      setPreferencesError('')
      return true
    } catch { setPreferencesError('Enregistrement impossible sur cet appareil. Le réglage précédent est conservé.'); return false }
  }
  const navigation = useNavigation()
  const { screen, menuOpen: mobileMenuEntry, back } = navigation
  const desktop = useSyncExternalStore(subscribeToDesktopViewport, isDesktopViewport)
  const menuOpen = !desktop && mobileMenuEntry
  const page = screen.page
  const settingsSection = screen.page === 'settings'
    ? desktop && screen.section === 'home' ? firstSettingsSection : screen.section
    : undefined
  const [musicOpened, setMusicOpened] = useState(page === 'music')
  if (page === 'music' && !musicOpened) setMusicOpened(true)
  const local = 'local' in screen && !!screen.local
  const menuTrigger = useRef<HTMLButtonElement>(null)
  const settingsTrigger = useRef<HTMLButtonElement>(null)
  const closingMenuForDesktop = useRef(false)
  const previousPage = useRef(page)
  const [draft, setDraft] = useState('')
  const chat = useChat(page === 'conversation', preferences)
  const { messages } = chat
  const hasMessages = messages.length > 0
  const waiting = chat.phase === 'transcribing' || chat.phase === 'waiting'
  const textarea = useRef<HTMLTextAreaElement>(null)
  const conversation = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // En grand écran, revenir à la page sous le menu transitoire.
    if (!desktop || !mobileMenuEntry) {
      closingMenuForDesktop.current = false
    } else if (!closingMenuForDesktop.current) {
      closingMenuForDesktop.current = true
      back()
    }
  }, [desktop, mobileMenuEntry, back])

  useEffect(() => {
    if (previousPage.current === 'settings' && page !== 'settings' && !menuOpen) {
      const trigger = desktop ? settingsTrigger : menuTrigger
      trigger.current?.focus({ preventScroll: true })
    }
    previousPage.current = page
  }, [page, menuOpen, desktop])

  useEffect(() => {
    if (!textarea.current) return
    textarea.current.style.height = 'auto'
    textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 200)}px`
  }, [draft, page, desktop])

  useEffect(() => {
    // Ne pas faire défiler les ancêtres/document avec scrollIntoView : cela
    // peut pousser le bandeau hors du viewport à l'ouverture du clavier.
    const scroller = conversation.current
    if (!scroller || page !== 'conversation' || !(messages.length || chat.error || chat.phase !== 'idle')) return
    const frame = requestAnimationFrame(() => { scroller.scrollTop = scroller.scrollHeight })
    return () => cancelAnimationFrame(frame)
  }, [messages, chat.error, chat.phase, page])

  function newChat() {
    void chat.reset()
    setDraft('')
    textarea.current?.focus({ preventScroll: true })
  }

  function send(event?: FormEvent) {
    event?.preventDefault()
    const text = draft.trim()
    if (!text || chat.phase !== 'idle') return
    void chat.talk(text)
    setDraft('')
    textarea.current?.focus({ preventScroll: true })
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      send()
    }
  }

  function focusDraft() {
    textarea.current?.focus({ preventScroll: true })
  }

  return (
    <div className={desktop ? 'app is-desktop' : 'app'}>
      <a className="skip-link" inert={menuOpen} href={{ conversation: '#message', music: '#music-search-input', shopping: '#shopping-add-input', reminders: local ? '#reminder-title' : '#shared-reminder-title', timers: local ? '#timer-hours' : '#shared-timer-hours', settings: '#settings-heading' }[page]} onClick={event => {
        event.preventDefault()
        document.querySelector<HTMLElement>(event.currentTarget.hash)?.focus()
      }}>Aller au contenu</a>
      {desktop && (settingsSection && settingsSection !== 'home'
        ? <DesktopSettingsNavigation section={settingsSection} onExit={navigation.exitSettings}
          onOpen={section => { if (section !== settingsSection) navigation.go({ page: 'settings', section }) }} />
        : <DesktopNavigation activePage={page} settingsRef={settingsTrigger}
          onNavigate={next => { if (next !== page) navigation.openPage(next) }} />)}
      <main className="main" inert={menuOpen}>
        <header className="header" hidden={page === 'settings'}>
          <div className="header-left">
            {!desktop && <button ref={menuTrigger} className="icon-button" type="button" aria-label="Ouvrir le menu" title="Ouvrir le menu" aria-expanded={menuOpen} aria-controls="app-menu" aria-haspopup="dialog" onClick={() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); navigation.openMenu() }}><Menu size={23} /></button>}
            <span className="app-name">Alfred<span className="header-caption">{{ conversation: 'Votre assistant personnel', music: 'Votre musique', shopping: 'Vos courses', reminders: 'Vos rappels', timers: 'Vos minuteries', settings: 'Vos paramètres' }[page]}</span></span>
          </div>
          <div className="header-actions">
            <InstallApp />
            {page === 'conversation' && <button className="icon-button" aria-label="Nouvelle conversation" title="Nouvelle conversation" onClick={newChat}><SquarePen size={21} /></button>}
          </div>
        </header>

        <div hidden={page !== 'conversation'} className="conversation">
          <div className="conversation-scroll" ref={conversation}>
            {hasMessages ? (
              <section className="message-list" aria-label="Messages" role="log" aria-live="polite" aria-relevant="additions">
                <div className="session-label">Aujourd’hui</div>
                {messages.map(message => <MessageBubble key={message.id} message={message} play={chat.play}
                  playing={chat.playback?.id === message.id && chat.playback.state === 'playing'}
                  audioError={chat.playback?.id === message.id && chat.playback.state === 'error'} />)}
              </section>
            ) : (
              <div className="welcome">
                <VoiceControls chat={chat} primary />
                <span className="welcome-symbol" aria-hidden="true">
                  {chat.analyser ? <VoiceWaveform analyser={chat.analyser} /> : <AudioLines size={33} strokeWidth={1.5} />}
                </span>
                <h1>Comment puis-je vous aider ?</h1>
                <div className="chat-examples">
                  {examples.map(example => <button key={example} type="button" disabled={chat.phase !== 'idle'}
                    onClick={() => { setDraft(example); focusDraft() }}>{example}</button>)}
                </div>
              </div>
            )}
          </div>
          <div className="composer-area">
            {hasMessages && chat.analyser && <div className="composer-waveform"><VoiceWaveform analyser={chat.analyser} /></div>}
            <p className="chat-notice" role="status">{chatStatus[chat.phase]}</p>
            {chat.error && <div className="chat-error">
              <p className="chat-notice" role="alert">{chat.error}</p>
              {chat.microphoneDenied && <button className="voice-secondary" type="button" onClick={focusDraft}>Écrire à Alfred</button>}
            </div>}
            <form className="composer" onSubmit={send}>
              <label className="sr-only" htmlFor="message">Votre message à Alfred</label>
              <textarea id="message" ref={textarea} value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={onKeyDown} placeholder="Écrivez à Alfred…" rows={1} maxLength={4000} />
              <div className="composer-tools">
                {hasMessages && <VoiceControls chat={chat} />}
                <div className="composer-actions">
                  {preferences.webSearch === 'on-request' && <button className="icon-button microphone-button chat-web" type="button" aria-label="Autoriser la recherche Internet pour cette demande" title="Autoriser la recherche Internet pour cette demande" aria-pressed={chat.webOverride} disabled={chat.phase !== 'idle'} onClick={() => chat.setWebOverride(!chat.webOverride)}><Globe size={19} /></button>}
                  {waiting
                    ? <button className="voice-secondary" type="button" onClick={chat.cancel}>Interrompre</button>
                    : <button className="send-button" type="submit" aria-label="Envoyer le message" title="Envoyer le message" disabled={chat.phase !== 'idle' || !draft.trim()}><ArrowUp size={21} strokeWidth={2.5} /></button>}
                </div>
              </div>
            </form>
          </div>
        </div>
        {musicOpened && <ScreenBoundary active={page === 'music'} back={back}>
          <Suspense fallback={<p className="screen-loading" hidden={page !== 'music'} role="status">Chargement de Musique…</p>}>
            <MusicPage active={page === 'music'} defaultCategory={preferences.musicCategory}
              selectedPlayer={preferences.musicPlayer} onSelectPlayer={musicPlayer => changePreferences({ musicPlayer })} />
          </Suspense>
        </ScreenBoundary>}
        <ShoppingList active={page === 'shopping'} shared={page !== 'shopping' || !local}
          onModeChange={shared => shared ? back() : navigation.go({ page: 'shopping', local: true })} />
        <Reminders active={page === 'reminders' && local} openShared={back} />
        <SharedReminders active={page === 'reminders' && !local} openLocal={() => navigation.go({ page: 'reminders', local: true })} />
        <Timers active={page === 'timers' && local} tone={preferences.timerTone} openShared={back} />
        <SharedTimers active={page === 'timers' && !local} openLocal={() => navigation.go({ page: 'timers', local: true })} />
        {settingsSection && <ScreenBoundary key={settingsSection} active back={desktop ? navigation.exitSettings : back}>
          <Suspense fallback={<div className="screen-loading">{!desktop && <button className="icon-button settings-back" type="button" aria-label="Revenir à la page précédente" onClick={back}>←</button>}<p role="status">Chargement des paramètres…</p></div>}>
            <SettingsPage key={settingsSection} section={settingsSection}
              preferences={preferences} onChange={changePreferences} error={preferencesError} blocked={!!initialPreferences.error}
              onOpen={section => navigation.go({ page: 'settings', section })}
              onBack={desktop ? undefined : settingsSection === 'home' ? back : navigation.backToSettingsHome} />
          </Suspense>
        </ScreenBoundary>}
      </main>
      {!desktop && <AppMenu open={menuOpen} onClose={back} triggerRef={menuTrigger} activePage={page} onNavigate={navigation.openPage} />}
    </div>
  )
}
