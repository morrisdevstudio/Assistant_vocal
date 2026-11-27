import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { BellRing, Pause, Play, RotateCcw, Timer, Trash2, Undo2, Volume2, VolumeX } from 'lucide-react'
import { clock, finishTimers, isTimer, remaining, toggleTimer } from './schedule-model'
import type { LocalTimer } from './schedule-model'
import { useLocalCollection } from './useLocalCollection'
import type { TimerTone } from './preferences'
import { playTimerTone } from './timer-sound'
import { TIMERS_KEY } from './local-data'
import { ScheduleScope } from './ScheduleScope'
import { newId } from './ids'

export function Timers({ active, tone, openShared }: { active: boolean; tone: TimerTone; openShared: () => void }) {
  const { items, update, current, error, blocked } = useLocalCollection(TIMERS_KEY, isTimer)
  const [now, setNow] = useState(Date.now)
  const [hours, setHours] = useState('0')
  const [minutes, setMinutes] = useState('5')
  const [seconds, setSeconds] = useState('0')
  const [title, setTitle] = useState('')
  const [notice, setNotice] = useState('')
  const [undo, setUndo] = useState<LocalTimer | null>(null)
  const [sound, setSound] = useState(false)
  const soundEnabled = useRef(false)
  const audio = useRef<AudioContext | null>(null)
  const commit = useRef(update)
  commit.current = update
  const running = items.some(timer => timer.endsAt !== null)

  useEffect(() => {
    if (!running) return
    function tick() {
      const now = Date.now()
      setNow(now)
      if (!current.current.some(timer => timer.endsAt !== null && timer.endsAt <= now)) return
      if (!commit.current(previous => finishTimers(previous, now))) return
      setNotice('Minuterie terminée.')
      if (soundEnabled.current && audio.current?.state === 'running' && !document.hidden) {
        playTimerTone(audio.current, tone)
      }
    }
    tick()
    const id = window.setInterval(tick, 1000)
    document.addEventListener('visibilitychange', tick)
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', tick) }
  }, [current, running, tone])

  useEffect(() => () => { void audio.current?.close() }, [])

  async function toggleSound() {
    if (sound) { soundEnabled.current = false; setSound(false); return }
    try {
      if (!audio.current || audio.current.state === 'closed') audio.current = new AudioContext()
      await audio.current.resume()
      soundEnabled.current = true; setSound(true)
      setNotice('Son activé pour cette session, lorsque l’application est visible.')
    } catch { setNotice('Le son n’est pas disponible sur ce navigateur.') }
  }

  function start(event: FormEvent) {
    event.preventDefault()
    const values = [hours, minutes, seconds].map(Number)
    if (values.some(value => !Number.isInteger(value) || value < 0) || values[0] > 23 || values[1] > 59 || values[2] > 59) { setNotice('Vérifiez la durée saisie.'); return }
    const durationMs = (values[0] * 3600 + values[1] * 60 + values[2]) * 1000
    if (!durationMs) { setNotice('Choisissez une durée supérieure à zéro.'); return }
    const now = Date.now()
    const timer: LocalTimer = { id: newId(), title: title.trim() || 'Minuteur', durationMs, remainingMs: durationMs, endsAt: now + durationMs, finished: false }
    if (update(previous => [...previous, timer])) { setNow(now); setTitle(''); setNotice('Minuterie démarrée.') }
  }

  function remove(timer: LocalTimer) {
    if (update(previous => previous.filter(item => item.id !== timer.id))) { setUndo(timer); setNotice('Minuterie supprimée.') }
  }

  const unfinished = items.filter(timer => !timer.finished)
  const finished = items.filter(timer => timer.finished)

  function timerCard(timer: LocalTimer) {
    return <li className={`timer-card ${timer.finished ? 'is-finished' : ''}`} key={timer.id}>
      <div className="timer-card-heading"><strong>{timer.title}</strong><span>{timer.finished ? <><BellRing size={14} />Terminé</> : timer.endsAt === null ? 'En pause' : 'En cours'}</span></div>
      <div className="timer-clock" role="timer" aria-label={`Temps restant pour ${timer.title}`} aria-live="off">{clock(remaining(timer, now))}</div>
      <div className="timer-track" aria-hidden="true"><span style={{ width: `${Math.max(0, Math.min(100, remaining(timer, now) / timer.durationMs * 100))}%` }} /></div>
      <div className="timer-controls"><button className="timer-toggle" type="button" onClick={() => { if (update(previous => previous.map(item => item.id === timer.id ? toggleTimer(item, Date.now()) : item))) { setNow(Date.now()); setNotice(timer.finished ? 'Minuterie relancée.' : timer.endsAt === null ? 'Minuterie reprise.' : 'Minuterie en pause.') } }}>{timer.endsAt !== null ? <Pause size={17} /> : <Play size={17} />}{timer.finished ? 'Relancer' : timer.endsAt === null ? 'Reprendre' : 'Pause'}</button><button className="icon-button" type="button" aria-label={`Réinitialiser ${timer.title}`} title="Réinitialiser" onClick={() => { if (update(previous => previous.map(item => item.id === timer.id ? { ...item, remainingMs: item.durationMs, endsAt: null, finished: false } : item))) setNotice('Minuterie réinitialisée, en pause.') }}><RotateCcw size={18} /></button><button className="icon-button" type="button" aria-label={`Supprimer ${timer.title}`} onClick={() => remove(timer)}><Trash2 size={18} /></button></div>
    </li>
  }

  return <section hidden={!active} className="schedule-page" aria-labelledby="timers-heading">
    <div className="schedule-scroll"><div className="schedule-content">
      <div className="schedule-heading"><span className="shopping-eyebrow"><Timer size={17} />CHAQUE MINUTE COMPTE</span><div className="timers-heading-row"><h1 id="timers-heading">Minuteries</h1><button type="button" className="icon-button" aria-label={sound ? 'Désactiver le son' : 'Activer le son'} aria-pressed={sound} title={sound ? 'Son activé' : 'Activer le son'} onClick={toggleSound}>{sound ? <Volume2 size={21} /> : <VolumeX size={21} />}</button></div><p>Pour la cuisine et les petites pauses.</p></div>
      <ScheduleScope label="Sur Alfred" local onChange={openShared} />
      {error && <p className="shopping-error" role="alert">{error}</p>}
      <div className="active-timers">
        {unfinished.length > 0 ? <ul className="timer-items" aria-label="Minuteries en cours ou en pause">{unfinished.map(timerCard)}</ul>
          : <p className="schedule-empty">Aucune minuterie active sur cet appareil.</p>}
      </div>
      <form className="schedule-form" onSubmit={start}>
        <div className="duration-fields">{[{ label: 'Heures', short: 'h', value: hours, change: setHours, max: 23, id: 'timer-hours' }, { label: 'Minutes', short: 'min', value: minutes, change: setMinutes, max: 59, id: 'timer-minutes' }, { label: 'Secondes', short: 's', value: seconds, change: setSeconds, max: 59, id: 'timer-seconds' }].map(field => <label key={field.id}><span className="sr-only">{field.label}</span><input id={field.id} type="number" inputMode="numeric" min={0} max={field.max} value={field.value} onChange={event => field.change(event.target.value)} required /><span>{field.short}</span></label>)}</div>
        <div className="schedule-chips timer-presets">{[1, 5, 10, 20].map(value => <button type="button" key={value} onClick={() => { setHours('0'); setMinutes(String(value)); setSeconds('0') }}>{value} min</button>)}</div>
        <label className="sr-only" htmlFor="timer-title">Nom de la minuterie, facultatif</label><input id="timer-title" className="schedule-input" placeholder="Un nom ? Pâtes, thé… (facultatif)" maxLength={80} value={title} onChange={event => setTitle(event.target.value)} />
        <button className="schedule-primary" type="submit" aria-describedby="local-timer-sound" disabled={blocked}><Play size={18} />Démarrer</button>
        <p id="local-timer-sound" className="timer-destination">{sound ? 'Sonnerie sur cet appareil si l’application est visible.' : 'Sonnerie désactivée sur cet appareil.'}</p>
      </form>
      {finished.length > 0 && <ul className="timer-items" aria-label="Minuteries terminées">{finished.map(timerCard)}</ul>}
    </div></div>
    <footer className="schedule-footer"><div className="shopping-notice" role="status"><span>{notice}</span>{undo && <button type="button" onClick={() => { if (update(previous => finishTimers([...previous, undo], Date.now()))) { setUndo(null); setNotice('Suppression annulée.') } }}><Undo2 size={15} />Annuler</button>}</div><p>Sur cet appareil · Alertes non garanties en arrière-plan ou application fermée.</p></footer>
  </section>
}
