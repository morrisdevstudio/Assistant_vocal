import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ChevronDown, DoorOpen, House, MapPinOff, Pencil, RefreshCw, Search } from 'lucide-react'
import { backendJson, errorText, useServerAction } from './backend'
import type { HomeFloor, HomeRoomRegistry } from './house-model'

type DeviceSettings = {
  alfred_name: string
  alfred_area: string
  aliases: string[]
  allowed: boolean
  confirmation_required: boolean
  light_type?: 'main' | 'secondary'
}
type HomeDevice = DeviceSettings & {
  id: string
  name: string
  ha_name: string
  device: string | null
  area: string | null
  ha_area: string | null
  domain: string
  unavailable: boolean
  supported: boolean
  capabilities: string[]
  ha_aliases: string[]
}
type DeviceDirectory = { items: HomeDevice[]; ha_rooms: string[]; ha_room_floors?: Record<string, HomeFloor> }
type SortKey = 'name' | 'area' | 'domain'
type Room = HomeDevice['area']
type RoomGroup = { room: Room; items: HomeDevice[] }
const path = 'home/devices'
const directory = path + '?editable=true'
const collator = new Intl.Collator('fr', { sensitivity: 'base', numeric: true })
const columns = [['name', 'Nom'], ['area', 'Pièce'], ['domain', 'Type']] as const
const deviceTypes: Record<string, string> = {
  light: 'Lumière', switch: 'Interrupteur', media_player: 'Lecteur multimédia', sensor: 'Capteur',
  binary_sensor: 'Capteur binaire', climate: 'Thermostat', vacuum: 'Aspirateur', todo: 'Liste',
  cover: 'Volet', fan: 'Ventilateur', scene: 'Scène', input_button: 'Bouton',
  input_boolean: 'Interrupteur virtuel', input_datetime: 'Date et heure', input_number: 'Nombre',
  input_select: 'Sélecteur', input_text: 'Texte',
}
const typeName = (domain: string) => deviceTypes[domain] ?? domain.replaceAll('_', ' ')
const roomName = (room: Room) => room ?? 'Sans pièce'
const roomFilterValue = (room: Room) => JSON.stringify(room)
const searchText = (value: string) => value.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('fr')

function sortRooms(a: Room, b: Room, direction = 1) {
  if (a === b) return 0
  if (a === null) return 1
  if (b === null) return -1
  return direction * collator.compare(a, b)
}

function DeviceEditor({ item, rooms, localRoomNames, roomLabels, directoryError, close, saved }: {
  item: HomeDevice
  rooms: string[]
  localRoomNames: string[]
  roomLabels: ReadonlyMap<string, string>
  directoryError: string
  close: () => void
  saved: (settings: DeviceSettings) => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const action = useServerAction()
  const [name, setName] = useState(item.alfred_name)
  const originalRoom = item.ha_area
  const initialRoom = item.alfred_area === originalRoom ? '' : item.alfred_area
  const [room, setRoom] = useState(initialRoom)
  const [aliasText, setAliasText] = useState(item.aliases.join(', '))
  const [allowed, setAllowed] = useState(item.allowed)
  const [confirmation, setConfirmation] = useState(item.confirmation_required)
  const [lightType, setLightType] = useState<NonNullable<DeviceSettings['light_type']>>(item.light_type ?? 'main')
  const aliases = [...new Set(aliasText.split(',').map(alias => alias.trim()).filter(Boolean))]
  const valid = aliases.length <= 20 && aliases.every(alias => alias.length <= 80)
  const allRooms = new Set([...rooms, ...localRoomNames])
  const oldRoom = initialRoom && !allRooms.has(initialRoom)
  const label = (name: string) => roomLabels.get(name) ?? name
  const roomOptions = [...allRooms].filter(value => value !== originalRoom)
    .sort((a, b) => collator.compare(label(a), label(b)))
  const draft: DeviceSettings = { alfred_name: name.trim(), alfred_area: room, aliases,
    allowed, confirmation_required: confirmation, ...(item.domain === 'light' ? { light_type: lightType } : {}) }
  const changes = Object.fromEntries(Object.entries(draft).filter(([key, value]) =>
    JSON.stringify(value) !== JSON.stringify(key === 'alfred_area' ? initialRoom :
      key === 'light_type' ? item.light_type ?? 'main' : item[key as keyof DeviceSettings])))

  useEffect(() => {
    const element = dialog.current
    if (element && !element.open) element.showModal()
  }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!valid || action.busy || !Object.keys(changes).length) return
    const localRoom = room && changes.alfred_area === room && localRoomNames.includes(room) && !rooms.includes(room) ? room : undefined
    const result = await action.run(() => backendJson<{ settings: DeviceSettings }>(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: item.id, settings: changes, local_room: localRoom }),
    }))
    if (result) {
      saved(result.settings)
      dialog.current?.close()
    }
  }

  return <dialog ref={dialog} className="ai-model-dialog house-device-dialog" aria-labelledby="house-device-editor-title"
    onClose={close} onCancel={event => { if (action.busy) event.preventDefault() }}>
    <h2 id="house-device-editor-title">Modifier {item.name}</h2>
    <form className="house-device-form" onSubmit={submit}>
      {directoryError && <p className="shopping-error" role="status">Actualisation des pièces indisponible. Dernière liste chargée affichée.</p>}
      <label>Nom pour Alfred
        <input autoFocus value={name} placeholder={item.ha_name} maxLength={80} disabled={action.busy}
          onChange={event => setName(event.target.value)} />
        <small>Home Assistant · {item.ha_name}</small>
      </label>
      <label>Pièce pour Alfred
        <span className="house-device-room-field">
          <select value={room} disabled={action.busy} onChange={event => setRoom(event.target.value)}
            aria-describedby={originalRoom ? 'house-device-original-room' : undefined}>
            <option value="">{originalRoom ? label(originalRoom) : 'Sans pièce'}</option>
            {oldRoom && <option value={initialRoom}>{label(initialRoom)} · ancienne affectation</option>}
            {roomOptions.map(value => <option key={value} value={value}>{label(value)}</option>)}
          </select>
          {!room && originalRoom && <span title="Pièce définie dans Home Assistant" aria-hidden="true"><House size={17} /></span>}
        </span>
      </label>
      {originalRoom && <span id="house-device-original-room" hidden>Pièce Home Assistant · {originalRoom}</span>}
      {item.domain === 'light' && <label>Type d’éclairage
        <select value={lightType} disabled={action.busy}
          onChange={event => setLightType(event.target.value as NonNullable<DeviceSettings['light_type']>)}>
          <option value="main">Principal</option><option value="secondary">Secondaire</option>
        </select>
      </label>}
      <label className="home-catalog-check"><input type="checkbox" checked={allowed} disabled={action.busy}
        onChange={event => setAllowed(event.target.checked)} />Autoriser l’accès dans Alfred</label>
      <label className="home-catalog-check"><input type="checkbox" checked={confirmation} disabled={action.busy}
        onChange={event => setConfirmation(event.target.checked)} />Demander confirmation avant de modifier l’appareil</label>
      <label>Alias Alfred
        <input value={aliasText} disabled={action.busy} aria-invalid={!valid}
          onChange={event => setAliasText(event.target.value)} />
        <small>{valid ? 'Séparez les alias par des virgules.' : 'Jusqu’à 20 alias de 80 caractères chacun.'}</small>
        <small>Alias Home Assistant · {item.ha_aliases.join(', ') || 'Aucun'}</small>
      </label>
      {action.error && <p className="shopping-error" role="alert">{action.error}</p>}
      <div className="house-device-actions">
        <button className="house-secondary" type="button" disabled={action.busy}
          onClick={() => dialog.current?.close()}>Annuler</button>
        <button className="house-secondary" type="submit" disabled={action.busy || !valid || !Object.keys(changes).length}>
          {action.busy ? 'Enregistrement…' : 'Valider'}</button>
      </div>
    </form>
  </dialog>
}

export function HomeDeviceTable({ configured, setupMessage, registryRooms, onRegistryRooms, roomLabels, localRoomNames }: {
  configured: boolean
  setupMessage: string
  registryRooms: HomeRoomRegistry | null | undefined
  onRegistryRooms: (rooms: HomeRoomRegistry | null) => void
  roomLabels: ReadonlyMap<string, string>
  localRoomNames: string[]
}) {
  const [devices, setDevices] = useState<HomeDevice[] | null>(null)
  const [loadError, setLoadError] = useState('')
  const [notice, setNotice] = useState('')
  const [query, setQuery] = useState('')
  const [area, setArea] = useState<Room>()
  const [domain, setDomain] = useState('')
  const [sort, setSort] = useState<{ key: SortKey; direction: number }>({ key: 'area', direction: 1 })
  const [expandedRooms, setExpandedRooms] = useState(() => new Set<Room>())
  const [filteredRooms, setFilteredRooms] = useState<{ filterKey: string; collapsed: Set<Room> }>()
  const [editing, setEditing] = useState<HomeDevice | null>(null)
  const search = useRef<HTMLInputElement>(null)
  const opener = useRef<HTMLButtonElement>(null)
  const action = useServerAction()

  const applyDirectory = useCallback((data: DeviceDirectory) => {
    setDevices(data.items)
    onRegistryRooms({ rooms: [...(data.ha_rooms ?? [])].sort(collator.compare), floors: data.ha_room_floors ?? {} })
    setLoadError('')
  }, [onRegistryRooms])

  useEffect(() => {
    if (!configured) return
    const controller = new AbortController()
    backendJson<DeviceDirectory>(directory, { signal: controller.signal }).then(
      data => { if (!controller.signal.aborted) applyDirectory(data) },
      error => {
        if (controller.signal.aborted) return
        onRegistryRooms(null)
        setLoadError(errorText(error))
      },
    )
    return () => controller.abort()
  }, [applyDirectory, configured, onRegistryRooms])

  const areas = useMemo(() => [...new Set(devices?.map(item => item.area))].sort(sortRooms), [devices])
  const domains = useMemo(() => [...new Set(devices?.map(item => item.domain))]
    .sort((a, b) => collator.compare(typeName(a), typeName(b))), [devices])
  const needle = searchText(query.trim())
  const selectedArea = area === undefined ? '' : roomFilterValue(area)
  const filtering = !!(selectedArea || domain || needle)
  const filterKey = JSON.stringify([selectedArea, domain, needle])
  const results = useMemo(() => {
    if (!devices) return null
    const visible = devices.filter(item => (area === undefined || item.area === area) && (!domain || item.domain === domain)
      && (!needle || [item.name, item.ha_name, item.id, item.device, roomName(item.area), typeName(item.domain), ...item.aliases, ...item.ha_aliases]
        .some(text => text && searchText(text).includes(needle))))
    const sortValue = (item: HomeDevice) => sort.key === 'domain' ? typeName(item.domain) : item.name
    const direction = sort.key === 'area' ? 1 : sort.direction
    visible.sort((a, b) => direction * collator.compare(sortValue(a), sortValue(b))
      || collator.compare(a.name, b.name) || collator.compare(a.id, b.id))
    const groups = new Map<Room, RoomGroup>()
    for (const item of visible) {
      const group = groups.get(item.area)
      if (group) group.items.push(item)
      else groups.set(item.area, { room: item.area, items: [item] })
    }
    return { count: visible.length, groups: [...groups.values()].sort((a, b) =>
      sortRooms(a.room, b.room, sort.key === 'area' ? sort.direction : 1)) }
  }, [area, devices, domain, needle, sort])

  function isRoomOpen(room: Room) {
    if (!filtering) return expandedRooms.has(room)
    return filteredRooms?.filterKey !== filterKey || !filteredRooms.collapsed.has(room)
  }

  function toggleRoom(room: Room) {
    if (filtering) {
      setFilteredRooms(previous => {
        const collapsed = new Set(previous?.filterKey === filterKey ? previous.collapsed : [])
        if (collapsed.has(room)) collapsed.delete(room)
        else collapsed.add(room)
        return { filterKey, collapsed }
      })
    } else {
      setExpandedRooms(previous => {
        const expanded = new Set(previous)
        if (expanded.has(room)) expanded.delete(room)
        else expanded.add(room)
        return expanded
      })
    }
  }

  async function refresh() {
    setNotice('')
    const data = await action.run(() => backendJson<DeviceDirectory>(directory))
    if (!data) return
    applyDirectory(data)
    if (!data.items.some(item => item.area === area)) setArea(undefined)
    if (!data.items.some(item => item.domain === domain)) setDomain('')
    return data
  }

  async function openEditor(item: HomeDevice, button: HTMLButtonElement) {
    opener.current = button
    const data = await refresh()
    const current = data ? data.items.find(device => device.id === item.id) : item
    if (current) setEditing(current)
    else setNotice('Cet appareil ne figure plus dans le catalogue.')
  }

  function saved(item: HomeDevice, settings: DeviceSettings) {
    const updated = { ...item, ...settings, name: settings.alfred_name || item.ha_name,
      area: settings.alfred_area || item.ha_area }
    setDevices(previous => previous?.map(device => device.id === item.id ? updated : device) ?? null)
    if (updated.area !== item.area) setExpandedRooms(previous => new Set(previous).add(updated.area))
    setNotice('Réglages enregistrés.')
  }

  function closeEditor() {
    setEditing(null)
    requestAnimationFrame(() => {
      const button = opener.current
      if (button?.isConnected && button.getClientRects().length) button.focus()
      else search.current?.focus()
    })
  }

  function editButton(item: HomeDevice) {
    return <button className="icon-button house-device-edit" type="button" aria-haspopup="dialog"
      aria-label={`Modifier ${item.name}`} title={`Modifier ${item.name}`} disabled={action.busy}
      onClick={event => { void openEditor(item, event.currentTarget) }}>
      <Pencil size={16} aria-hidden="true" />
    </button>
  }

  function roomButton({ room, items }: RoomGroup, open: boolean) {
    const Icon = room === null ? MapPinOff : DoorOpen
    return <button className="house-room-toggle" type="button" aria-expanded={open} onClick={() => toggleRoom(room)}>
      <span className="house-room-icon"><Icon size={19} strokeWidth={1.7} aria-hidden="true" /></span>
      <strong>{roomName(room)}</strong><small>{items.length} {items.length === 1 ? 'entité' : 'entités'}</small>
      <ChevronDown className="house-room-chevron" size={17} aria-hidden="true" />
    </button>
  }

  return <details className="preference-group house-catalog" open>
    <summary><h2>Appareils Home Assistant</h2><ChevronDown size={16} aria-hidden="true" /></summary>
    <div className="house-catalog-panel">
      {configured && <div className="house-catalog-toolbar">
        <div className="house-catalog-controls">
          <div className="house-field-row"><Search size={17} aria-hidden="true" />
            <input ref={search} aria-label="Rechercher un appareil" type="search" placeholder="Nom, pièce, type ou alias…" value={query} onChange={event => setQuery(event.target.value)} />
            <button className="icon-button" type="button" aria-label="Actualiser les appareils" disabled={action.busy || (!devices && !loadError)}
              onClick={() => void refresh()}><RefreshCw size={17} /></button>
          </div>
          <div className="house-catalog-filters">
            <label>Pièce<select value={selectedArea} onChange={event => {
              const value = event.target.value
              setArea(value ? areas.find(room => roomFilterValue(room) === value) : undefined)
            }}><option value="">Toutes les pièces</option>
              {area !== undefined && !areas.includes(area) && <option value={selectedArea}>{roomName(area)}</option>}
              {areas.map(room => <option key={roomFilterValue(room)} value={roomFilterValue(room)}>{roomName(room)}</option>)}
            </select></label>
            <label>Type<select value={domain} onChange={event => setDomain(event.target.value)}><option value="">Tous les types</option>
              {domains.map(name => <option key={name} value={name}>{typeName(name)}</option>)}
            </select></label>
          </div>
          <label className="house-mobile-sort">Trier par
            <select value={`${sort.key}:${sort.direction}`} onChange={event => {
              const option = columns.find(([key]) => event.target.value.startsWith(key + ':'))
              if (option) setSort({ key: option[0], direction: event.target.value.endsWith(':-1') ? -1 : 1 })
            }}>
              {columns.flatMap(([key, label]) => [1, -1].map(direction =>
                <option key={`${key}:${direction}`} value={`${key}:${direction}`}>{label} · {direction === 1 ? 'A–Z' : 'Z–A'}</option>,
              ))}
            </select>
          </label>
        </div>
        {devices && <p role="status">{filtering ? `${results?.count ?? 0} sur ` : ''}{devices.length} entités exposées à Assist</p>}
        {(action.error || loadError) && <p className="shopping-error" role="alert">{action.error || loadError}</p>}
        {notice && <p role="status">{notice}</p>}
      </div>}
      {setupMessage ? <p className="house-empty" role="status">{setupMessage}</p> : !results
        ? !loadError && <p className="house-empty" role="status">Chargement des appareils…</p>
        : results.count ? <>
          <div className="house-room-list">
            {results.groups.map(group => {
              const open = isRoomOpen(group.room)
              return <div className="house-room-card" key={roomFilterValue(group.room)}>
                {roomButton(group, open)}
                {open && <ul className="house-device-list" aria-label={roomName(group.room)}>
                  {group.items.map(item => <li key={item.id} className="house-device-summary">
                    <div><strong>{item.name}</strong>
                      <small>{typeName(item.domain)}</small>
                      <small>Accès {item.allowed ? 'autorisé' : 'exclu'} · Confirmation {item.confirmation_required ? 'activée' : 'désactivée'}</small>
                      <small>Alias · {item.aliases.join(', ') || 'Aucun'}</small>
                      {item.unavailable && <small>Indisponible dans Home Assistant</small>}
                    </div>
                    {editButton(item)}
                  </li>)}
                </ul>}
              </div>
            })}
          </div>
          <div className="house-catalog-scroll" tabIndex={0} role="region" aria-label="Tableau des entités, défilement horizontal">
            <table aria-label="Entités Home Assistant">
              <thead><tr>
                {columns.map(([key, label]) => <th key={key} scope="col"
                  aria-sort={sort.key === key ? sort.direction === 1 ? 'ascending' : 'descending' : undefined}>
                  <button type="button" onClick={() => setSort({ key, direction: sort.key === key ? -sort.direction : 1 })}>
                    {label} <span aria-hidden="true">{sort.key === key ? sort.direction === 1 ? '↑' : '↓' : '↕'}</span>
                  </button>
                </th>)}
                <th scope="col">Accès</th><th scope="col">Confirmation</th><th scope="col">Alias</th>
                <th scope="col"><span className="sr-only">Modifier</span></th>
              </tr></thead>
              {results.groups.map(group => {
                const open = isRoomOpen(group.room)
                return <tbody className="house-room-card" key={roomFilterValue(group.room)}>
                  <tr className="house-room-row"><th scope="rowgroup" colSpan={7}>{roomButton(group, open)}</th></tr>
                  {open && group.items.map(item => <tr key={item.id}>
                    <th scope="row" title={item.id}>{item.name}
                      {item.unavailable && <small>Indisponible dans Home Assistant</small>}
                    </th>
                    <td>{roomName(item.area)}</td><td>{typeName(item.domain)}</td>
                    <td><span className="house-device-access" data-allowed={item.allowed}>{item.allowed ? 'Autorisé' : 'Exclu'}</span></td>
                    <td>{item.confirmation_required ? 'Activée' : 'Désactivée'}</td>
                    <td>{item.aliases.join(', ') || 'Aucun'}</td>
                    <td className="house-device-edit-cell">{editButton(item)}</td>
                  </tr>)}
                </tbody>
              })}
            </table>
          </div>
        </> : <p className="house-empty">Aucune entité correspondante.</p>}
    </div>
    {editing && <DeviceEditor item={editing} rooms={registryRooms?.rooms ?? []} localRoomNames={localRoomNames} roomLabels={roomLabels}
      directoryError={action.error} close={closeEditor} saved={settings => saved(editing, settings)} />}
  </details>
}
