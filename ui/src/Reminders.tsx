import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Bell, CalendarDays, Check, ChevronDown, Pencil, Plus, Trash2, Undo2, X } from 'lucide-react'
import { isReminder, localDate } from './schedule-model'
import type { Reminder } from './schedule-model'
import { useLocalCollection } from './useLocalCollection'
import { REMINDERS_KEY } from './local-data'
import { ScheduleScope } from './ScheduleScope'
import { newId } from './ids'

export function Reminders({ active, openShared }: { active: boolean; openShared: () => void }) {
  const { items, update, error, blocked } = useLocalCollection(REMINDERS_KEY, isReminder)
  const [title, setTitle] = useState('')
  const [date, setDate] = useState(() => localDate(new Date()))
  const [time, setTime] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const [undo, setUndo] = useState<Reminder | null>(null)
  const [showDone, setShowDone] = useState(false)
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    if (!active) return
    const refresh = () => setNow(Date.now())
    refresh()
    const id = window.setInterval(refresh, 30000)
    document.addEventListener('visibilitychange', refresh)
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', refresh) }
  }, [active])
  const pending = items.filter(item => !item.done).sort((a, b) => a.dueAt - b.dueAt)
  const done = items.filter(item => item.done).sort((a, b) => b.dueAt - a.dueAt)

  function reset() { setTitle(''); setTime(''); setEditing(null) }
  function save(event: FormEvent) {
    event.preventDefault()
    const dueAt = new Date(`${date}T${time}`).getTime()
    if (!title.trim() || !Number.isFinite(dueAt) || dueAt <= Date.now()) { setNotice('Choisissez un titre et une date à venir.'); return }
    const id = editing || newId()
    const value: Reminder = { id, title: title.trim(), dueAt, done: false }
    if (update(previous => editing ? previous.map(item => item.id === id ? value : item) : [...previous, value])) { setNotice(editing ? 'Rappel modifié.' : 'Rappel enregistré sur cet appareil.'); reset() }
  }
  function toggle(item: Reminder) {
    if (update(previous => previous.map(entry => entry.id === item.id ? { ...entry, done: !entry.done } : entry))) setNotice(item.done ? 'Rappel remis à faire.' : 'Rappel terminé.')
  }
  function remove(item: Reminder) {
    if (update(previous => previous.filter(entry => entry.id !== item.id))) { setUndo(item); setNotice('Rappel supprimé.'); if (editing === item.id) reset() }
  }
  function edit(item: Reminder) {
    const date = new Date(item.dueAt)
    setTitle(item.title); setDate(localDate(date)); setTime(`${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`); setEditing(item.id)
    document.getElementById('reminder-title')?.focus({ preventScroll: true })
  }
  function chooseDay(offset: number) { const day = new Date(); day.setDate(day.getDate() + offset); setDate(localDate(day)) }
  function row(item: Reminder) {
    const overdue = !item.done && item.dueAt < now
    return <li className={`reminder-card ${item.done ? 'is-done' : ''}`} key={item.id}>
      <button type="button" className="reminder-check" role="checkbox" aria-checked={item.done} aria-label={`${item.done ? 'Remettre à faire' : 'Terminer'} : ${item.title}`} onClick={() => toggle(item)}>{item.done && <Check size={17} />}</button>
      <div className="reminder-info"><strong>{item.title}</strong><span className={overdue ? 'is-overdue' : ''}><CalendarDays size={13} />{new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(item.dueAt)}{overdue && ' · À faire'}</span></div>
      <div className="reminder-actions">{!item.done && <button type="button" className="icon-button" aria-label={`Modifier ${item.title}`} onClick={() => edit(item)}><Pencil size={16} /></button>}<button type="button" className="icon-button" aria-label={`Supprimer ${item.title}`} onClick={() => remove(item)}><Trash2 size={16} /></button></div>
    </li>
  }
  return <section hidden={!active} className="schedule-page" aria-labelledby="reminders-heading">
    <div className="schedule-scroll"><div className="schedule-content">
      <div className="schedule-heading"><span className="shopping-eyebrow"><Bell size={17} />AU BON MOMENT</span><h1 id="reminders-heading">Rappels</h1><p>{pending.length ? `${pending.length} rappel${pending.length > 1 ? 's' : ''} à faire` : 'Gardez l’esprit libre.'}</p></div>
      <ScheduleScope label="Calendrier familial" local onChange={openShared} />
      <form className="schedule-form" onSubmit={save}>
        <div className="schedule-form-title"><strong>{editing ? 'Modifier le rappel' : 'Un nouveau rappel'}</strong>{editing && <button type="button" className="icon-button" aria-label="Annuler la modification" onClick={reset}><X size={18} /></button>}</div>
        <label htmlFor="reminder-title" className="sr-only">Que faut-il rappeler ?</label><input id="reminder-title" className="schedule-input" placeholder="À quoi faut-il penser ?" value={title} onChange={event => setTitle(event.target.value)} maxLength={200} required disabled={blocked} />
        <div className="schedule-chips"><button type="button" onClick={() => chooseDay(0)}>Aujourd’hui</button><button type="button" onClick={() => chooseDay(1)}>Demain</button></div>
        <div className="schedule-datetime"><label>Date<input type="date" value={date} min={localDate(new Date())} onChange={event => setDate(event.target.value)} required /></label><label>Heure<input type="time" value={time} onChange={event => setTime(event.target.value)} required /></label></div>
        <button type="submit" className="schedule-primary" disabled={blocked || !title.trim() || !date || !time}>{editing ? <Check size={18} /> : <Plus size={18} />}{editing ? 'Enregistrer' : 'Ajouter le rappel'}</button>
      </form>
      {error && <p className="shopping-error" role="alert">{error}</p>}
      {pending.length ? <ul className="reminder-items" aria-label="Rappels à faire">{pending.map(row)}</ul> : <div className="schedule-empty"><Bell size={29} strokeWidth={1.5} /><h2>Rien à ne pas oublier.</h2><p>Vos prochains rappels apparaîtront ici.</p></div>}
      {done.length > 0 && <div className="reminders-done"><button type="button" className="shopping-completed-toggle" aria-expanded={showDone} aria-controls="done-reminders" onClick={() => setShowDone(value => !value)}><ChevronDown size={17} />Terminés · {done.length}</button><ul id="done-reminders" className="reminder-items" hidden={!showDone}>{done.map(row)}</ul></div>}
    </div></div>
    <footer className="schedule-footer"><div className="shopping-notice" role="status"><span>{notice}</span>{undo && <button type="button" onClick={() => { if (update(previous => [...previous, undo])) { setUndo(null); setNotice('Suppression annulée.') } }}><Undo2 size={15} />Annuler</button>}</div><p>Les rappels de cet appareil restent dans le navigateur.</p></footer>
  </section>
}
