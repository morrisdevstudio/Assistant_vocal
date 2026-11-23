import { useEffect, useRef } from 'react'
import type { RefObject } from 'react'
import type { AppPage } from './navigation'
import { ArrowLeft, ArrowUpRight, Bell, ListTodo, MessageCircle, Music2, Settings, Timer, X } from 'lucide-react'
import { settingsSections } from './settings-sections'
import type { SettingsDetail } from './settings-sections'

type Props = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  open: boolean
  onClose: () => void
  triggerRef: RefObject<HTMLButtonElement | null>
}

const pages = [
  { name: 'Conversation', icon: MessageCircle, page: 'conversation' as const },
  { name: 'Musique', icon: Music2, page: 'music' as const },
  { name: 'Listes', icon: ListTodo, page: 'shopping' as const },
  { name: 'Rappels', icon: Bell, page: 'reminders' as const },
  { name: 'Minuteries', icon: Timer, page: 'timers' as const },
]
const settings = { name: 'Paramètres', icon: Settings, page: 'settings' as const }

type NavigationProps = Pick<Props, 'activePage' | 'onNavigate'>

function PageButton({ item: { name, icon: Icon, page }, activePage, onNavigate, buttonRef }: NavigationProps & {
  item: typeof pages[number] | typeof settings
  buttonRef?: RefObject<HTMLButtonElement | null>
}) {
  const current = page === activePage
  return <button ref={buttonRef} type="button" className={`menu-page ${current ? 'is-current' : ''}`} onClick={() => onNavigate(page)} aria-current={current ? 'page' : undefined}>
    <Icon size={page === 'settings' ? 23 : 24} strokeWidth={1.6} aria-hidden="true" />
    <span>{name}</span>
    {current && <ArrowUpRight className="menu-current-arrow" size={20} aria-hidden="true" />}
  </button>
}

export function DesktopNavigation({ settingsRef, ...props }: NavigationProps & { settingsRef: RefObject<HTMLButtonElement | null> }) {
  return <nav className="desktop-navigation" aria-label="Pages de l’application">
    <div className="menu-header"><span className="app-name">Alfred</span></div>
    <div className="menu-pages">
      {pages.map(item => <PageButton key={item.page} item={item} {...props} />)}
    </div>
    <div className="menu-footer"><PageButton item={settings} buttonRef={settingsRef} {...props} /></div>
  </nav>
}

export function DesktopSettingsNavigation({ section, onOpen, onExit }: {
  section: SettingsDetail
  onOpen: (section: SettingsDetail) => void
  onExit: () => void
}) {
  return <nav className="desktop-navigation desktop-settings-navigation" aria-label="Rubriques des paramètres">
    <div className="menu-header">
      <button className="menu-page" type="button" onClick={onExit}>
        <ArrowLeft size={20} aria-hidden="true" /><span>Retour au menu principal</span>
      </button>
    </div>
    <div className="menu-pages">
      {settingsSections.map(({ title, icon: Icon, page }) => <button key={page} type="button"
        className={`menu-page ${section === page ? 'is-current' : ''}`}
        aria-current={section === page ? 'page' : undefined} onClick={() => onOpen(page)}>
        <Icon size={20} strokeWidth={1.6} aria-hidden="true" /><span>{title}</span>
      </button>)}
    </div>
  </nav>
}

export function AppMenu({ open, onClose, triggerRef, activePage, onNavigate }: Props) {
  const panel = useRef<HTMLElement>(null)
  const closeButton = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    closeButton.current?.focus({ preventScroll: true })
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') { event.preventDefault(); onClose(); return }
      if (event.key !== 'Tab') return
      const buttons = panel.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')
      if (!buttons?.length) return
      const first = buttons[0]
      const last = buttons[buttons.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    const trigger = triggerRef.current
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      trigger?.focus({ preventScroll: true })
    }
  }, [open, onClose, triggerRef])

  return <section ref={panel} id="app-menu" className={`app-menu ${open ? 'is-open' : ''}`} role="dialog" aria-modal={open ? true : undefined} aria-labelledby="app-menu-title" aria-hidden={!open} inert={!open}>
    <div className="menu-header">
      <span className="app-name">Alfred</span>
      <button ref={closeButton} type="button" className="icon-button" onClick={onClose} aria-label="Fermer le menu" title="Fermer le menu"><X size={23} /></button>
    </div>
    <div className="menu-content">
      <h2 id="app-menu-title">Votre espace</h2>
      <nav className="menu-pages" aria-label="Pages de l’application">
        {pages.map(item => <PageButton key={item.page} item={item} activePage={activePage} onNavigate={onNavigate} />)}
      </nav>
    </div>
    <footer className="menu-footer">
      <PageButton item={settings} activePage={activePage} onNavigate={onNavigate} />
    </footer>
  </section>
}
