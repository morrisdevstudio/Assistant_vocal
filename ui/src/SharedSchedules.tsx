import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { BellRing, CalendarDays, Play, Plus, Trash2 } from 'lucide-react'
import { backendJson, jsonPost, useRemote, useServerAction } from './backend'
import type { Target } from './backend'
import { floorNames, loadHouse } from './house-model'
import type { Floor } from './house-model'
import { clock, isTimerPreset, localDate } from './schedule-model'
import type { TimerPreset } from './schedule-model'
import { TIMER_PRESETS_KEY } from './local-data'
import { useLocalCollection } from './useLocalCollection'
import { ScheduleScope } from './ScheduleScope'

type Props = { active: boolean; openLocal: () => void }

function SharedControls({ label, openLocal, reload, busy }: { label: string; openLocal: () => void; reload: () => void; busy: boolean }) {
  return <div className="schedule-scope-row">
    <ScheduleScope label={label} onChange={openLocal} busy={busy} />
    <button className="timer-toggle" type="button" onClick={reload} disabled={busy}>Actualiser</button>
  </div>
}

type SharedTimer = { id: string; title: string; due_at: string; status: string }

export function SharedTimers({ active, openLocal }: Props) {
  const [floor, setFloor] = useState<Floor>(() => {
    const { config } = loadHouse()
    return config.rooms.find(room => room.id === config.browserRoomId)?.floor ?? 'rdc'
  })
  const [hours, setHours] = useState('0')
  const [minutes, setMinutes] = useState('5')
  const [seconds, setSeconds] = useState('0')
  const [title, setTitle] = useState('')
  const [now, setNow] = useState(Date.now)
  const [notice, setNotice] = useState('')
  const presets = useLocalCollection(TIMER_PRESETS_KEY, isTimerPreset)
  const remote = useRemote<{ items: SharedTimer[] }>(active ? `timers?floor_id=${floor}` : null, 3000)
  const server = useServerAction()
  const duration = Number(hours) * 3600 + Number(minutes) * 60 + Number(seconds)
  const validDuration = [hours, minutes, seconds].every((value, index) =>
    value !== '' && Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= (index === 0 ? 23 : 59)) && duration > 0
  const counting = !!remote.data?.items.some(timer => timer.status !== 'ringing')
  useEffect(() => {
    if (!active || !counting) return
    function tick() { if (!document.hidden) setNow(Date.now()) }
    tick()
    const interval = window.setInterval(tick, 1000)
    document.addEventListener('visibilitychange', tick)
    return () => {
      window.clearInterval(interval)
      document.removeEventListener('visibilitychange', tick)
    }
  }, [active, counting])

  async function start(event: FormEvent) {
    event.preventDefault()
    if (!validDuration) { setNotice('Vérifiez la durée de la minuterie.'); return }
    setNotice('')
    const result = await server.run(() => backendJson<SharedTimer>('timers', jsonPost({
      floor_id: floor, duration_seconds: duration, title: title.trim() || 'Minuteur',
    })))
    remote.reload()
    if (result) { setTitle(''); setNotice('Minuterie démarrée sur Alfred.') }
  }

  function savePreset() {
    const preset = { title: title.trim(), durationSeconds: duration }
    if (!validDuration || !isTimerPreset(preset)) { setNotice('Renseignez un nom et une durée valides.'); return }
    if (presets.update(items => {
      const index = items.findIndex(item => item.title.toLocaleLowerCase('fr') === preset.title.toLocaleLowerCase('fr'))
      return index < 0 ? [...items, preset] : items.map((item, position) => position === index ? preset : item)
    })) setNotice(`Modèle « ${preset.title} » enregistré sur cet appareil.`)
  }

  function loadPreset(preset: TimerPreset) {
    setTitle(preset.title)
    setHours(String(Math.floor(preset.durationSeconds / 3600)))
    setMinutes(String(Math.floor(preset.durationSeconds / 60) % 60))
    setSeconds(String(preset.durationSeconds % 60))
    setNotice('')
  }

  async function cancel(timer: SharedTimer) {
    setNotice('')
    const result = await server.run(() => backendJson<SharedTimer>(`timers/${encodeURIComponent(timer.id)}/cancel`, jsonPost({})))
    remote.reload()
    if (result) setNotice(result.status !== 'cancelled' ? 'Cette minuterie était déjà terminée.'
      : timer.status === 'ringing' ? 'Arrêt de la sonnerie demandé.' : 'Minuterie annulée.')
  }

  return <section className="schedule-page" hidden={!active} aria-labelledby="shared-timers-heading">
    <div className="schedule-scroll"><div className="schedule-content">
      <div className="schedule-heading"><h1 id="shared-timers-heading">Minuteries</h1></div>
      <SharedControls label="Sur Alfred" openLocal={openLocal} reload={remote.reload} busy={server.busy} />
      <label className="house-floor-label">Étage<select value={floor} disabled={server.busy} onChange={event => { setFloor(event.target.value as Floor); setNotice('') }}>
        {Object.entries(floorNames).map(([id, name]) => <option value={id} key={id}>{name}</option>)}
      </select></label>
      {(server.error || remote.error || presets.error) && <p role="alert" className="shopping-error">{server.error || remote.error || presets.error}</p>}
      <div className="active-timers">
        {remote.data ? remote.data.items.length ? <ul className="timer-items" aria-label="Minuteries de l’étage">
          {remote.data.items.map(timer => <li className="timer-card" key={timer.id}>
            <div className="timer-card-heading"><strong>{timer.title}</strong><span>{timer.status === 'ringing' ? 'Sonnerie' : 'En cours'}</span></div>
            <div className="timer-clock" role="timer" aria-label={`Temps restant pour ${timer.title}`}>{clock(timer.status === 'ringing' ? 0 : Date.parse(timer.due_at) - now)}</div>
            <div className="timer-controls"><button className="timer-toggle" type="button" disabled={server.busy} onClick={() => void cancel(timer)}>{timer.status === 'ringing' ? 'Arrêter la sonnerie' : 'Annuler la minuterie'}</button></div>
          </li>)}
        </ul> : <p className="schedule-empty">Aucune minuterie active à cet étage.</p> : !remote.error && <p role="status">Chargement des minuteries…</p>}
      </div>
      <form className="schedule-form" onSubmit={start}>
        <div className="duration-fields">
          {[{ id: 'shared-timer-hours', label: 'Heures', short: 'h', value: hours, change: setHours, max: 23 },
            { id: 'shared-timer-minutes', label: 'Minutes', short: 'min', value: minutes, change: setMinutes, max: 59 },
            { id: 'shared-timer-seconds', label: 'Secondes', short: 's', value: seconds, change: setSeconds, max: 59 }].map(field =>
            <label key={field.id}><span className="sr-only">{field.label}</span><input id={field.id} type="number" inputMode="numeric" min={0} max={field.max} value={field.value} required onChange={event => field.change(event.target.value)} /><span>{field.short}</span></label>)}
        </div>
        <div className="schedule-chips timer-presets">{[1, 5, 10, 20].map(value => <button type="button" key={value} onClick={() => { setHours('0'); setMinutes(String(value)); setSeconds('0') }}>{value} min</button>)}</div>
        <label className="sr-only" htmlFor="shared-timer-title">Nom de la minuterie</label><input className="schedule-input" id="shared-timer-title" placeholder="Nom (facultatif)" maxLength={160} value={title} onChange={event => setTitle(event.target.value)} />
        <div className="timer-form-actions">
          <button className="schedule-primary" aria-describedby="shared-timer-sound" disabled={!remote.data || server.busy}><Play size={18} />Démarrer</button>
          <button type="button" className="timer-toggle" disabled={presets.blocked || server.busy || !title.trim() || !validDuration} onClick={savePreset}>Enregistrer le modèle</button>
        </div>
        <p id="shared-timer-sound" className="timer-destination">Sonnerie Alfred · {floorNames[floor]}</p>
      </form>
      {!!presets.items.length && <ul className="timer-items" aria-label="Modèles de minuterie sur cet appareil">
        {presets.items.map(preset => <li className="timer-preset-card" key={preset.title}>
          <button type="button" className="timer-toggle" disabled={server.busy} onClick={() => loadPreset(preset)}>
            {preset.title} <span>{clock(preset.durationSeconds * 1000)}</span>
          </button>
          <button type="button" className="icon-button" aria-label={`Supprimer le modèle ${preset.title}`} onClick={() => {
            if (presets.update(items => items.filter(item => item.title !== preset.title))) setNotice(`Modèle « ${preset.title} » supprimé.`)
          }}><Trash2 size={17} /></button>
        </li>)}
      </ul>}
    </div></div>
    <footer className="schedule-footer"><p role="status">{notice}</p></footer>
  </section>
}

type SharedReminder = { id: string; title: string; room: string; due_at: string }

export function SharedReminders({ active, openLocal }: Props) {
  const remote = useRemote<{ items: SharedReminder[]; targets: Target[] }>(active ? 'calendar-reminders/family' : null)
  const server = useServerAction()
  const [title, setTitle] = useState('')
  const [date, setDate] = useState(() => localDate(new Date()))
  const [time, setTime] = useState('')
  const [destination, setDestination] = useState('')
  const [notice, setNotice] = useState('')
  const targets = remote.data?.targets ?? []
  const targetKey = (target: Target) => JSON.stringify([target.floor_id, target.room])
  const target = targets.find(item => targetKey(item) === destination)

  async function save(event: FormEvent) {
    event.preventDefault()
    const due = new Date(`${date}T${time}`)
    if (!target || !title.trim() || !Number.isFinite(due.getTime()) || due.getTime() <= Date.now()) {
      setNotice('Choisissez un titre, une pièce et une date à venir.')
      return
    }
    setNotice('')
    const result = await server.run(() => backendJson<{ message: string }>('calendar-reminders/family', jsonPost({
      title: title.trim(), due_at: due.toISOString(), target_room: target.room, floor_id: target.floor_id,
    })))
    remote.reload()
    if (result) { setNotice(result.message); setTitle(''); setTime('') }
  }

  return <section className="schedule-page" hidden={!active} aria-labelledby="shared-reminders-heading">
    <div className="schedule-scroll"><div className="schedule-content">
      <div className="schedule-heading"><h1 id="shared-reminders-heading">Rappels</h1></div>
      <SharedControls label="Calendrier familial" openLocal={openLocal} reload={remote.reload} busy={server.busy} />
      <form className="schedule-form" onSubmit={save}>
        <label className="sr-only" htmlFor="shared-reminder-title">Titre du rappel</label><input id="shared-reminder-title" className="schedule-input" placeholder="À quoi faut-il penser ?" value={title} maxLength={160} required onChange={event => setTitle(event.target.value)} />
        <div className="schedule-datetime">
          <label>Date<input type="date" value={date} min={localDate(new Date())} required onChange={event => setDate(event.target.value)} /></label>
          <label>Heure<input type="time" value={time} required onChange={event => setTime(event.target.value)} /></label>
        </div>
        <label className="house-floor-label">Pièce d’annonce<select value={target ? destination : ''} required onChange={event => setDestination(event.target.value)}>
          <option value="">{targets.length ? 'Choisir une pièce' : 'Aucune pièce disponible'}</option>
          {targets.map(item => <option key={targetKey(item)} value={targetKey(item)}>{item.room} · {floorNames[item.floor_id]}</option>)}
        </select></label>
        <button className="schedule-primary" disabled={server.busy || !target || !title.trim() || !date || !time}><Plus size={18} />Ajouter au calendrier</button>
      </form>
      {(server.error || remote.error) && <p role="alert" className="shopping-error">{server.error || remote.error}</p>}
      {remote.data ? remote.data.items.length ? <ul className="reminder-items" aria-label="Rappels familiaux à venir">
        {remote.data.items.map(item => <li key={item.id} className="reminder-card"><CalendarDays size={17} /><div className="reminder-info">
          <strong>{item.title}</strong><span>{new Date(item.due_at).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })}</span><span><BellRing size={13} />{item.room}</span>
        </div></li>)}
      </ul> : <p className="schedule-empty">Aucun rappel familial à venir.</p> : !remote.error && <p role="status">Chargement du calendrier…</p>}
    </div></div>
    <footer className="schedule-footer"><p role="status">{notice}</p><p>Rappels Alfred à venir dans le calendrier familial Home Assistant.</p></footer>
  </section>
}
