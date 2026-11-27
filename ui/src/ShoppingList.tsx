import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Check, ChevronDown, Pencil, Plus, ShoppingBasket, Trash2, Undo2, X } from 'lucide-react'
import { SHOPPING_KEY } from './local-data'
import { backendJson, jsonPost, useRemote, useServerAction } from './backend'
import { newId } from './ids'

type Item = { id: string; name: string; checked: boolean }

function load(): { items: Item[]; error: string } {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(SHOPPING_KEY) || '[]')
    if (!Array.isArray(stored) || !stored.every(item => item && typeof item.id === 'string' && typeof item.name === 'string' && typeof item.checked === 'boolean')) throw Error()
    return { items: stored, error: '' }
  } catch {
    return { items: [], error: 'La liste enregistrée sur cet appareil est inaccessible. Réessayez après avoir rouvert l’application.' }
  }
}

export function ShoppingList({ active, shared, onModeChange }: {
  active: boolean; shared: boolean; onModeChange: (shared: boolean) => void
}) {
  const [initial] = useState(load)
  const [localItems, setItems] = useState<Item[]>(initial.items)
  const remote = useRemote<{ items: Item[] }>(active && shared ? 'shopping/items?all_statuses=true' : null)
  const server = useServerAction()
  const [error, setError] = useState(initial.error)
  const [draft, setDraft] = useState('')
  const [showChecked, setShowChecked] = useState(true)
  const [editing, setEditing] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [undo, setUndo] = useState<Item[] | null>(null)
  const [notice, setNotice] = useState('')
  const [lastMode, setLastMode] = useState(shared)
  if (lastMode !== shared) {
    setLastMode(shared)
    setEditing(null)
    setNotice('')
    setDraft('')
  }
  const input = useRef<HTMLInputElement>(null)
  const items = shared ? remote.data?.items ?? [] : localItems
  const blocked = shared ? !remote.data || server.busy : !!initial.error
  const displayedError = shared ? server.error || remote.error : error
  const pending = items.filter(item => !item.checked)
  const checked = items.filter(item => item.checked)

  function save(next: Item[]) {
    if (initial.error) return false
    try {
      localStorage.setItem(SHOPPING_KEY, JSON.stringify(next))
      setItems(next)
      setError('')
      return true
    } catch {
      setError('Enregistrement impossible sur cet appareil. La liste n’a pas été modifiée.')
      return false
    }
  }

  async function sharedAction(path: string, body: unknown) {
    const result = await server.run(() => backendJson<{ message: string }>('shopping/items' + path, jsonPost(body)))
    remote.reload()
    if (!result) return false
    setNotice(result.message)
    return true
  }

  async function add(event: FormEvent) {
    event.preventDefault()
    const name = draft.trim()
    if (!name || blocked) return
    if (shared) {
      if (await sharedAction('', { item: name })) { setDraft(''); input.current?.focus({ preventScroll: true }) }
      return
    }
    const existing = items.find(item => item.name.toLocaleLowerCase('fr') === name.toLocaleLowerCase('fr'))
    const next = existing ? items.map(item => item.id === existing.id ? { ...item, checked: false } : item) : [...items, { id: newId(), name, checked: false }]
    if (save(next)) {
      setDraft('')
      setNotice(existing ? (existing.checked ? `${name} remis dans les courses.` : `${name} est déjà dans la liste.`) : `${name} ajouté.`)
      input.current?.focus({ preventScroll: true })
    }
  }

  function toggle(item: Item) {
    if (blocked) return
    if (shared) { void sharedAction(item.checked ? '/restore' : '/complete', { item: item.name }); return }
    if (save(items.map(entry => entry.id === item.id ? { ...entry, checked: !entry.checked } : entry))) setNotice(item.checked ? `${item.name} remis à acheter.` : `${item.name} coché.`)
  }

  function remove(ids: Set<string>) {
    if (blocked) return
    if (shared) {
      const item = items.find(item => ids.has(item.id))
      if (item && window.confirm(`Supprimer définitivement « ${item.name} » dans Home Assistant ?`)) {
        void sharedAction('/delete', { item: item.name, confirm_delete: true }).then(ok => { if (ok) setEditing(null) })
      }
      return
    }
    if (save(items.filter(item => !ids.has(item.id)))) {
      setUndo(items.filter(item => ids.has(item.id)))
      setEditing(null)
      setNotice(ids.size > 1 ? 'Articles cochés retirés.' : 'Article retiré.')
    }
  }

  function restore() {
    if (!undo) return
    const missing = undo.filter(item => !items.some(current => current.id === item.id || current.name.toLocaleLowerCase('fr') === item.name.toLocaleLowerCase('fr')))
    if (save([...items, ...missing])) { setUndo(null); setNotice('Suppression annulée.') }
  }

  async function finishEdit(event: FormEvent) {
    event?.preventDefault()
    const name = editName.trim()
    if (!name || blocked) return
    if (shared) {
      const item = items.find(item => item.id === editing)
      if (item && await sharedAction('/rename', { item: item.name, new_name: name })) setEditing(null)
      return
    }
    if (items.some(item => item.id !== editing && item.name.toLocaleLowerCase('fr') === name.toLocaleLowerCase('fr'))) { setError('Cet article existe déjà dans la liste.'); return }
    if (save(items.map(item => item.id === editing ? { ...item, name } : item))) { setEditing(null); setNotice('Article modifié.'); input.current?.focus({ preventScroll: true }) }
  }

  function row(item: Item) {
    return <li key={item.id} className={`shopping-row ${item.checked ? 'is-checked' : ''}`}>
      {editing === item.id ? <form className="shopping-edit" onSubmit={finishEdit}>
        <label htmlFor="edit-item" className="sr-only">Modifier l’article</label>
        <input id="edit-item" value={editName} maxLength={shared ? 120 : 200} onChange={event => setEditName(event.target.value)} autoFocus onFocus={event => event.target.select()} onKeyDown={event => { if (event.key === 'Escape') { setEditing(null); input.current?.focus({ preventScroll: true }) } }} />
        <button className="icon-button" type="submit" aria-label="Enregistrer l’article" disabled={!editName.trim() || blocked}><Check size={20} /></button>
        <button className="icon-button" type="button" disabled={blocked} aria-label={`Supprimer ${item.name}`} onClick={() => remove(new Set([item.id]))}><Trash2 size={18} /></button>
        <button className="icon-button" type="button" aria-label="Annuler la modification" onClick={() => { setEditing(null); input.current?.focus({ preventScroll: true }) }}><X size={19} /></button>
      </form> : <>
        <label className="shopping-check-label">
          <input type="checkbox" checked={item.checked} disabled={blocked} onChange={() => toggle(item)} />
          <span className="shopping-checkbox" aria-hidden="true">{item.checked && <Check size={16} strokeWidth={2.5} />}</span>
          <span className="shopping-item-name">{item.name}</span>
        </label>
        {shared && item.checked
          ? <button type="button" className="icon-button shopping-edit-button" aria-label={`Supprimer ${item.name}`} disabled={blocked} onClick={() => remove(new Set([item.id]))}><Trash2 size={16} /></button>
          : <button type="button" className="icon-button shopping-edit-button" aria-label={`Modifier ${item.name}`} disabled={blocked} onClick={() => { setEditing(item.id); setEditName(item.name) }}><Pencil size={16} /></button>}
      </>}
    </li>
  }

  return <section className="shopping-page" hidden={!active} aria-labelledby="shopping-title">
    <div className="shopping-scroll">
      <div className="shopping-content">
        <div className="shopping-heading">
          <span className="shopping-eyebrow"><ShoppingBasket size={17} />LES ESSENTIELS DU QUOTIDIEN</span>
          <h1 id="shopping-title">Liste de courses</h1>
          <p>{pending.length ? `${pending.length} article${pending.length > 1 ? 's' : ''} à acheter` : checked.length ? 'Tout est dans le panier.' : 'Pour ne rien oublier.'}</p>
        </div>
        <div className="schedule-chips server-modes" role="group" aria-label="Liste de courses">
          {[true, false].map(value => <button key={String(value)} type="button" aria-pressed={shared === value} disabled={server.busy} onClick={() => { if (shared !== value) onModeChange(value) }}>{value ? 'Liste familiale' : 'Sur cet appareil'}</button>)}
          {shared && <button type="button" onClick={remote.reload} disabled={server.busy}>Actualiser</button>}
        </div>
        <form className="shopping-add" onSubmit={add}>
          <label className="sr-only" htmlFor="shopping-add-input">Ajouter un article</label>
          <input id="shopping-add-input" ref={input} placeholder="Ajouter un article…" value={draft} maxLength={shared ? 120 : 200} onChange={event => setDraft(event.target.value)} enterKeyHint="done" autoComplete="off" disabled={blocked} />
          <button type="submit" aria-label="Ajouter l’article" disabled={!draft.trim() || blocked}><Plus size={22} /></button>
        </form>
        {displayedError && <p className="shopping-error" role="alert">{displayedError}</p>}
        {shared && !remote.data && !remote.error && <p role="status">Chargement de la liste familiale…</p>}
        {pending.length > 0 && <ul className="shopping-items" aria-label="À acheter">{pending.map(row)}</ul>}
        {pending.length === 0 && (!shared || !!remote.data) && <div className="shopping-empty">
          <span className="shopping-empty-icon">{checked.length ? <Check size={29} strokeWidth={1.5} /> : <ShoppingBasket size={29} strokeWidth={1.5} />}</span>
          <h2>{checked.length ? 'Les courses sont faites.' : 'On fait les courses ?'}</h2>
          <p>{checked.length ? 'Ajoutez ce qu’il vous manque pour la prochaine fois.' : 'Ajoutez votre premier article, puis cochez-le une fois dans le panier.'}</p>
        </div>}
        {checked.length > 0 && <div className="shopping-completed">
          <div className="shopping-completed-header">
            <button className="shopping-completed-toggle" type="button" aria-expanded={showChecked} aria-controls="checked-items" onClick={() => setShowChecked(value => !value)}><ChevronDown size={17} className={showChecked ? '' : 'is-collapsed'} />Dans le panier <span>{checked.length}</span></button>
            {!shared && <button className="icon-button" type="button" aria-label="Retirer les articles cochés" title="Retirer les articles cochés" onClick={() => remove(new Set(checked.map(item => item.id)))}><Trash2 size={17} /></button>}
          </div>
          <ul id="checked-items" className="shopping-items" hidden={!showChecked} aria-label="Dans le panier">{checked.map(row)}</ul>
        </div>}
      </div>
    </div>
    <div className="shopping-footer">
      <div className="shopping-notice" role="status"><span>{notice || (shared ? 'Liste familiale Home Assistant' : 'Enregistrée sur cet appareil')}</span>{!shared && undo && <button type="button" onClick={restore}><Undo2 size={15} />Annuler la suppression</button>}</div>
    </div>
  </section>
}
