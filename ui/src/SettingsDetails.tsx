import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Download, Play, RefreshCw } from 'lucide-react'
import { version } from '../package.json'
import { exportLocalData } from './local-data'
import { musicCategories, PREFERENCES_KEY, timerTones } from './preferences'
import type { Preferences } from './preferences'
import { playTimerTone } from './timer-sound'
import { backendJson, jsonPost, useRemote, useServerAction } from './backend'
import type { AlfredStatus, ServiceStatus } from './backend'

type PreferenceControls = {
  preferences: Preferences
  blocked: boolean
  save: (patch: Partial<Preferences>) => void
}

export function PreferenceGroup({ title, children }: { title: string; children: ReactNode }) {
  return <section className="preference-group"><h2>{title}</h2><div className="preference-card">{children}</div></section>
}

function SettingSelect<Value extends string>({ label, value, options, onChange, disabled }: {
  label: string
  value: Value
  options: ReadonlyArray<{ id: Value; label: string }>
  onChange: (value: Value) => void
  disabled: boolean
}) {
  return <label className="preference-select">
    <span><strong>{label}</strong></span>
    <select value={value} disabled={disabled} onChange={event => {
      const option = options.find(item => item.id === event.target.value)
      if (option) onChange(option.id)
    }}>
      {options.map(option => <option key={option.id} value={option.id}>{option.label}</option>)}
    </select>
  </label>
}

type AIStatus = ServiceStatus & { models?: string[]; model_from_environment?: boolean }

function AIModelDialog({ active, config, onUpdate, onDismiss }: {
  active: string; config: AIStatus; onUpdate: () => void; onDismiss: () => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [models, setModels] = useState(config.models ?? [active])
  const [selected, setSelected] = useState(active)
  const [draft, setDraft] = useState('')
  const [latencies, setLatencies] = useState<Record<string, number>>({})
  const [notice, setNotice] = useState('')
  const [applying, setApplying] = useState(false)
  const request = useServerAction()
  const testModel = draft.trim() || selected
  const latency = latencies[testModel]
  const disabled = request.busy || !config.configured

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    element?.querySelector<HTMLInputElement>('input:checked:enabled')?.focus()
    return () => element?.close()
  }, [])

  function dismiss() {
    dialog.current?.close()
    onDismiss()
  }

  async function addModel() {
    const model = draft.trim()
    if (disabled || !model) return
    setNotice('')
    const result = await request.run(() => backendJson<AIStatus>('ai/models', jsonPost({ action: 'add', model })))
    if (!result) return
    setModels(result.models ?? [...new Set([...models, model])])
    if (!config.model_from_environment) setSelected(model)
    setDraft('')
    setNotice('Modèle ajouté à la liste.')
    onUpdate()
  }

  async function applySelection() {
    if (selected === active) { dismiss(); return }
    if (disabled || config.model_from_environment) return
    setApplying(true)
    const result = await request.run(() => backendJson<AIStatus>('ai/models', jsonPost({ action: 'select', model: selected })))
    setApplying(false)
    if (result) { onUpdate(); dismiss() }
  }

  async function runModelTest() {
    setNotice('')
    setLatencies(({ [testModel]: _, ...remaining }) => remaining)
    const result = await request.run(() => backendJson<{ model: string; llm_ms: number }>('ai/models/test', jsonPost({ model: testModel })))
    if (result) setLatencies(previous => ({ ...previous, [result.model]: result.llm_ms }))
  }

  return <dialog ref={dialog} className="ai-model-dialog" id="ai-model-editor" aria-labelledby="ai-model-title"
    onCancel={event => { event.preventDefault(); if (!applying) dismiss() }}>
      <h2 id="ai-model-title">Modèle du serveur</h2>
      <fieldset className="ai-model-options" disabled={disabled || config.model_from_environment}>
        <legend>Modèles enregistrés</legend>
        {models.map(model => <label key={model} className="ai-model-option">
          <input type="radio" name="ai-saved-model" checked={selected === model} onChange={() => {
            setSelected(model)
            setDraft('')
            setNotice('')
          }} />
          <span>{model}</span>{model === active && <small>Actif</small>}
        </label>)}
      </fieldset>
      <div className="ai-model-add">
        <label htmlFor="ai-new-model">Nouveau modèle</label>
        <form className="ai-model-controls" onSubmit={event => { event.preventDefault(); void addModel() }}>
          <input id="ai-new-model" value={draft} maxLength={160} autoCapitalize="none" spellCheck={false}
            placeholder="fournisseur/modèle" disabled={disabled} onChange={event => setDraft(event.target.value)} />
          <button type="submit" className="house-secondary" disabled={disabled || !draft.trim()}>Ajouter</button>
          <button type="button" className="house-secondary" disabled={disabled || !testModel} onClick={() => void runModelTest()}>Tester</button>
        </form>
        {config.model_from_environment && <p className="settings-feedback">Le modèle actif est imposé par le serveur.</p>}
        <div role="status" className="settings-feedback">
          {request.busy ? 'Demande en cours…' : [notice, latency !== undefined
            ? `Réponse reçue en ${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(latency / 1000)} s.` : ''].filter(Boolean).join(' ')}
        </div>
        {request.error && <p className="shopping-error" role="alert">{request.error}</p>}
      </div>
      <div className="ai-model-actions">
        <button type="button" className="house-secondary" onClick={dismiss} disabled={applying}>Annuler</button>
        <button type="button" className="house-secondary ai-model-confirm" disabled={request.busy}
          onClick={() => void applySelection()}>Valider</button>
      </div>
  </dialog>
}

export function AISettings({ preferences, blocked, save }: PreferenceControls) {
  const ai = useRemote<AIStatus>('ai/config')
  const internet = useRemote<ServiceStatus & { quota_blocked: boolean }>('internet/config')
  const [editing, setEditing] = useState(false)
  const active = ai.data?.model ?? ''
  const status = (service: { data: ServiceStatus | null; error: string }) => service.error ? 'Indisponible' : !service.data ? 'Chargement…'
    : service.data.access_verified ? 'Accès vérifié' : service.data.configured ? 'Configuré, accès à vérifier' : 'À configurer'

  return <>
    <PreferenceGroup title="Services">
      <dl className="settings-facts">
        <div><dt>Command Code</dt><dd>{status(ai)}</dd></div>
        {active && <div className="ai-model-row"><dt>Modèle du serveur</dt><dd>
          <span>{active}</span>
          <button type="button" className="house-secondary" aria-haspopup="dialog" onClick={() => setEditing(true)}>Modifier</button>
        </dd></div>}
        <div><dt>Recherche Internet</dt><dd>{internet.data?.quota_blocked ? 'Quota atteint' : status(internet)}</dd></div>
      </dl>
    </PreferenceGroup>
    {editing && active && ai.data && <AIModelDialog active={active} config={ai.data} onUpdate={ai.reload} onDismiss={() => setEditing(false)} />}
    <PreferenceGroup title="Préférence de recherche">
      <SettingSelect label="Chercher sur Internet" value={preferences.webSearch} disabled={blocked}
        options={[{ id: 'when-needed', label: 'Si nécessaire' }, { id: 'on-request', label: 'Sur demande' }]}
        onChange={webSearch => save({ webSearch })} />
      <p className="settings-card-note">En mode « Sur demande », activez le globe avant l’envoi pour autoriser une recherche sur cet échange.</p>
    </PreferenceGroup>
  </>
}

export function MusicSettings({ preferences, blocked, save }: PreferenceControls) {
  const music = useRemote<{ configured_player: string | null; current: { state: string } | null; error?: string }>('music/config')
  return <>
    <PreferenceGroup title="Service">
      <dl className="settings-facts"><div><dt>Lecteur Music Assistant</dt><dd>{music.error || music.data?.error ? 'Indisponible' : music.data?.configured_player ?? (music.data ? 'À configurer sur Alfred' : 'Chargement…')}</dd></div></dl>
    </PreferenceGroup>
    <PreferenceGroup title="Favoris">
      <SettingSelect label="Catégorie par défaut" value={preferences.musicCategory} disabled={blocked}
        options={musicCategories.map(id => ({ id, label: id }))}
        onChange={musicCategory => save({ musicCategory })} />
    </PreferenceGroup>
  </>
}

export function NotificationSettings({ preferences, blocked, save }: PreferenceControls) {
  const calendar = useRemote<{ available: boolean }>('calendar-reminders/status')
  const [testing, setTesting] = useState(false)
  const [error, setError] = useState('')
  const preview = useRef<AudioContext | null>(null)
  const endPreview = useRef<number | undefined>(undefined)

  useEffect(() => () => {
    window.clearTimeout(endPreview.current)
    if (preview.current) void preview.current.close().catch(() => {})
    preview.current = null
  }, [])

  async function testSound() {
    setTesting(true)
    setError('')
    const tone = preferences.timerTone
    try {
      const context = preview.current ?? new AudioContext()
      preview.current = context
      await context.resume()
      if (preview.current !== context) return
      playTimerTone(context, tone)
      endPreview.current = window.setTimeout(() => setTesting(false), 950)
    } catch {
      setError('Impossible de lire la sonnerie sur ce navigateur.')
      setTesting(false)
    }
  }

  return <>
    <PreferenceGroup title="Minuteries">
      <SettingSelect label="Sonnerie de fin" options={timerTones} value={preferences.timerTone} disabled={blocked || testing}
        onChange={timerTone => save({ timerTone })} />
      <div className="settings-card-action">
        <button className="house-secondary" type="button" onClick={testSound} disabled={testing}><Play size={16} />{testing ? 'Lecture en cours…' : 'Écouter la sonnerie'}</button>
      </div>
      <p className="settings-card-note">Pour les minuteries de cet appareil, activez le son à chaque session lorsque l’application est visible. Les minuteries partagées utilisent la sonnerie du serveur Alfred.</p>
    </PreferenceGroup>
    <PreferenceGroup title="Rappels">
      <dl className="settings-facts">
        <div><dt>Service d’annonces du calendrier</dt><dd>{calendar.error ? 'Indisponible' : calendar.data ? calendar.data.available ? 'Configuré sur Alfred' : 'À configurer sur Alfred' : 'Chargement…'}</dd></div>
        <div><dt>Notifications sur cet appareil</dt><dd>À raccorder</dd></div>
      </dl>
    </PreferenceGroup>
    {error && <p className="shopping-error" role="alert">{error}</p>}
  </>
}

export function PrivacySettings() {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  function downloadData() {
    setMessage('')
    setError('')
    try {
      const data = exportLocalData(localStorage)
      const url = URL.createObjectURL(new Blob([data], { type: 'application/json' }))
      const link = document.createElement('a')
      link.href = url
      link.download = 'alfred-donnees-locales.json'
      document.body.append(link)
      try { link.click() }
      finally {
        link.remove()
        window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      }
      setMessage('Export préparé au format JSON.')
    } catch {
      setError('Impossible de lire ou d’exporter les données locales.')
    }
  }

  return <>
    <PreferenceGroup title="Données de l’application">
      <dl className="settings-facts">
        <div><dt>Préférences, maison, courses, rappels et minuteries</dt><dd>Sur cet appareil</dd></div>
        <div><dt>Conversation et brouillon affichés</dt><dd>En mémoire jusqu’au rechargement</dd></div>
        <div><dt>Échanges envoyés</dt><dd>Traités par Alfred et ses services selon la demande</dd></div>
      </dl>
    </PreferenceGroup>
    <PreferenceGroup title="Export">
      <p className="settings-card-note settings-card-intro">Téléchargez un fichier JSON des données enregistrées dans ce navigateur. Il peut contenir des informations personnelles comme vos rappels et les noms de vos pièces.</p>
      <div className="settings-card-action"><button className="house-secondary" type="button" onClick={downloadData}><Download size={17} />Exporter les données locales</button></div>
    </PreferenceGroup>
    {error && <p className="shopping-error" role="alert">{error}</p>}
    {message && <p className="settings-feedback" role="status">{message}</p>}
  </>
}

function readDiagnosis() {
  let storage = 'Accessible en lecture'
  try { localStorage.getItem(PREFERENCES_KEY) }
  catch { storage = 'Inaccessible' }
  const worker = window.isSecureContext && 'serviceWorker' in navigator
    ? navigator.serviceWorker.controller ? 'Actif pour cette page' : 'Page non contrôlée'
    : 'Indisponible'
  return {
    mode: matchMedia('(display-mode: standalone)').matches ? 'Application installée' : 'Navigateur',
    secure: window.isSecureContext ? 'Sécurisé' : 'Non sécurisé',
    network: navigator.onLine ? 'En ligne selon le navigateur' : 'Hors ligne selon le navigateur',
    storage,
    worker,
  }
}

type UpdateStatus = {
  available: boolean
  auto_enabled?: boolean
  installed?: string
  candidate?: string
  phase?: 'idle' | 'queued' | 'running' | 'failed'
  message?: string
}

function UpdateSettings() {
  const status = useRemote<UpdateStatus>('updates', 2000)
  const action = useServerAction()
  const [key, setKey] = useState('')
  const value = status.data
  const disabled = action.busy || !key.trim() || !window.isSecureContext || !value?.available
    || value.phase === 'queued' || value.phase === 'running'

  async function request(operation: 'check' | 'install' | 'auto-on' | 'auto-off') {
    await action.run(() => backendJson('updates/' + operation, {
      ...jsonPost({}),
      headers: { 'Content-Type': 'application/json', 'X-Alfred-Update-Key': key.trim() },
    }))
    status.reload()
  }

  return <PreferenceGroup title="Mises à jour d’Alfred">
    {value?.available ? <>
      <dl className="settings-facts">
        <div><dt>Version installée</dt><dd>{value.installed || '—'}</dd></div>
        <div><dt>Version candidate</dt><dd>{value.candidate || '—'}</dd></div>
      </dl>
      <label className="preference-select"><span><strong>Code d’administration</strong></span>
        <input type="password" maxLength={128} autoComplete="off" spellCheck={false} value={key} onChange={event => setKey(event.target.value)} />
      </label>
      <label className="preference-toggle-row"><span><strong>Mises à jour automatiques</strong><small>Chaque jour à 4 h, heure du serveur.</small></span>
        <input type="checkbox" role="switch" checked={Boolean(value.auto_enabled)} disabled={disabled} onChange={event => request(event.target.checked ? 'auto-on' : 'auto-off')} />
        <span className="preference-switch" aria-hidden="true" />
      </label>
      <div className="settings-card-action update-actions">
        <button type="button" className="house-secondary" disabled={disabled} onClick={() => request('check')}>Rechercher des mises à jour</button>
        <button type="button" className="house-secondary" disabled={disabled} onClick={() => {
          if (window.confirm('Installer maintenant la dernière version disponible ? Alfred pourra redémarrer.')) request('install')
        }}>Forcer la mise à jour</button>
      </div>
    </> : <p className="settings-card-intro">{status.error || (value ? 'Disponible avec le paquet Debian alfred-home.' : 'Chargement…')}</p>}
    <p className="settings-card-intro" role="status">{action.error || (value?.available && !window.isSecureContext ? 'Ouvrez Alfred en HTTPS pour effectuer une opération.' : value?.message)}</p>
  </PreferenceGroup>
}

export function DiagnosticSettings() {
  const backend = useRemote<AlfredStatus>('status')
  const [diagnosis, setDiagnosis] = useState(readDiagnosis)
  const [updated, setUpdated] = useState('')

  return <>
    <PreferenceGroup title="Alfred">
      <dl className="settings-facts">
        <div><dt>Version de l’application</dt><dd>{version}</dd></div>
        <div><dt>Affichage</dt><dd>{diagnosis.mode}</dd></div>
        <div><dt>Serveur Alfred</dt><dd>{backend.error ? 'Indisponible' : backend.data ? `${backend.data.version} · ${backend.data.scheduler_ok ? 'Opérationnel' : 'Dégradé'}` : 'Chargement…'}</dd></div>
        {backend.data && <>
          <div><dt>Reconnaissance et synthèse vocales</dt><dd>{backend.data.capabilities.stt && backend.data.capabilities.tts ? 'Disponibles' : 'Fonctionnement partiel'}</dd></div>
          <div><dt>Satellite ESP32</dt><dd>{backend.data.capabilities.esp32 ? 'Connecté' : 'Déconnecté'}</dd></div>
        </>}
      </dl>
    </PreferenceGroup>
    <UpdateSettings />
    <PreferenceGroup title="Diagnostic local">
      <dl className="settings-facts">
        <div><dt>Contexte de navigation</dt><dd>{diagnosis.secure}</dd></div>
        <div><dt>Réseau</dt><dd>{diagnosis.network}</dd></div>
        <div><dt>Stockage local</dt><dd>{diagnosis.storage}</dd></div>
        <div><dt>Service worker</dt><dd>{diagnosis.worker}</dd></div>
      </dl>
      <div className="settings-card-action">
        <button className="house-secondary" type="button" onClick={() => {
          setDiagnosis(readDiagnosis())
          backend.reload()
          setUpdated(new Date().toLocaleTimeString('fr-FR'))
        }}><RefreshCw size={17} />Actualiser le diagnostic</button>
      </div>
    </PreferenceGroup>
    {updated && <p className="settings-feedback" role="status">Diagnostic actualisé à {updated}.</p>}
  </>
}
