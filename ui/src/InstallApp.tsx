import { useEffect, useState } from 'react'
import { Download, X } from 'lucide-react'

interface InstallPrompt extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function InstallApp() {
  const [prompt, setPrompt] = useState<InstallPrompt | null>(null)
  const [installed, setInstalled] = useState(() => matchMedia('(display-mode: standalone)').matches)
  const [help, setHelp] = useState(false)
  const [busy, setBusy] = useState(false)
  const [workerError, setWorkerError] = useState(false)

  useEffect(() => {
    const ready = (event: Event) => {
      event.preventDefault()
      setPrompt(event as InstallPrompt)
      setWorkerError(false)
    }
    const done = () => { setInstalled(true); setPrompt(null); setHelp(false) }
    const error = () => setWorkerError(true)
    window.addEventListener('beforeinstallprompt', ready)
    window.addEventListener('appinstalled', done)
    window.addEventListener('alfred-pwa-registration-error', error)
    return () => {
      window.removeEventListener('beforeinstallprompt', ready)
      window.removeEventListener('appinstalled', done)
      window.removeEventListener('alfred-pwa-registration-error', error)
    }
  }, [])

  async function install() {
    if (!prompt) { setHelp(value => !value); return }
    setBusy(true)
    try {
      await prompt.prompt()
      const choice = await prompt.userChoice
      if (choice.outcome === 'accepted') setHelp(false)
    } catch {
      setHelp(true)
    } finally {
      setPrompt(null)
      setBusy(false)
    }
  }

  if (installed) return null
  return <div className="install-area">
    <button type="button" className="install-button" onClick={install} disabled={busy} aria-expanded={help} aria-controls="install-help"><Download size={17} /><span>Installer</span></button>
    {help && <section className="install-help" id="install-help" aria-label="Installer Alfred">
      <div className="install-help-title"><strong>Installer Alfred sur Android</strong><button type="button" className="icon-button" aria-label="Fermer l’aide d’installation" onClick={() => setHelp(false)}><X size={18} /></button></div>
      <p>Dans Chrome, ouvrez le menu ⋮ puis <strong>Ajouter à l’écran d’accueil</strong> ou <strong>Installer l’application</strong>.</p>
      {!prompt && <p>L’invitation automatique n’est pas encore disponible. Restez quelques instants sur cette page, puis réessayez.</p>}
      {(workerError || !window.isSecureContext || !prompt) && <details>
        <summary>Si Chrome affiche une erreur de certificat</summary>
        <p>Le réseau local utilise un certificat privé. Pour installer la PWA, Android doit reconnaître l’autorité de certification d’Alfred.</p>
        <ol>
          <li><a href="/alfred-local-ca.crt" download="alfred-local-ca.crt">Télécharger le certificat public Alfred</a>.</li>
          <li>Dans les paramètres Android, recherchez « Installer un certificat », puis choisissez « Certificat CA ». Les intitulés varient selon le téléphone.</li>
          <li>Choisissez le fichier téléchargé, puis fermez et rouvrez Chrome sur cette page.</li>
        </ol>
        <p>Installer cette autorité permet à votre téléphone de faire confiance aux certificats signés par ce PC. Sa clé privée reste sur le PC.</p>
      </details>}
    </section>}
  </div>
}
