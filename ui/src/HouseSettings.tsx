import { useState } from 'react'
import type { FormEvent } from 'react'
import { Check, DoorOpen, House, Info, Pencil, Plus, Radio, Smartphone, Trash2, Undo2, X } from 'lucide-react'
import { floorFromHomeAssistant, floorNames, homeAddress, HOUSE_KEY, loadHouse, parseHouse } from './house-model'
import type { Floor, HomeFloor, HomeRoomRegistry, HouseConfiguration, Room, Satellite } from './house-model'
import { useRemote } from './backend'
import type { TerminalStatus } from './backend'
import { HomeDeviceTable } from './HomeDeviceTable'

type Removed = { kind: 'room'; item: Room } | { kind: 'satellite'; item: Satellite }
type ListedRoom = { name: string; local: Room | null; haName?: string }
const roomCollator = new Intl.Collator('fr', { numeric: true })
const roomKey = (name: string) => name.trim().normalize('NFC').toLocaleLowerCase('fr')

function listRooms(localRooms: Room[], registryRooms: string[]): ListedRoom[] {
  const rooms: ListedRoom[] = localRooms.map(local => ({ name: local.name, local, haName: local.haName }))
  for (const name of registryRooms) {
    if (localRooms.some(room => room.haName === name)) continue
    const matches = rooms.filter(room => room.local && !room.haName && roomKey(room.name) === roomKey(name))
    if (matches.length === 1) matches[0].haName = name
    else rooms.push({ name, local: null, haName: name })
  }
  return rooms.sort((a, b) => roomCollator.compare(a.name, b.name))
}

export function HouseSettings() {
  const home = useRemote<{ configured: boolean; verified: boolean; base_url: string | null }>('home/config')
  const terminal = useRemote<TerminalStatus>('terminal/status')
  const [initial] = useState(loadHouse)
  const [config, setConfig] = useState(initial.config)
  const [registryRooms, setRegistryRooms] = useState<HomeRoomRegistry | null>()
  const [url, setUrl] = useState(initial.config.url)
  const [error, setError] = useState(initial.error)
  const [notice, setNotice] = useState('')
  const [roomName, setRoomName] = useState('')
  const [floor, setFloor] = useState<Floor | ''>('rdc')
  const [editRoom, setEditRoom] = useState<{ id?: string; haName?: string } | null>(null)
  const [deviceForm, setDeviceForm] = useState(false)
  const [deviceName, setDeviceName] = useState('')
  const [deviceRoom, setDeviceRoom] = useState('')
  const [editDevice, setEditDevice] = useState<string | null>(null)
  const [removed, setRemoved] = useState<Removed | null>(null)
  const blocked = !!initial.error
  const rooms = listRooms(config.rooms, registryRooms?.rooms ?? [])
  const roomLabels = new Map(rooms.flatMap(room => room.haName && room.local ? [[room.haName, room.name] as const] : []))
  const localRoomNames = rooms.flatMap(room => room.local && !room.haName ? [room.name] : [])

  function getHomeFloor(haName?: string): HomeFloor | undefined {
    if (haName && registryRooms && Object.hasOwn(registryRooms.floors, haName)) return registryRooms.floors[haName]
    return undefined
  }

  const sourceFloor = getHomeFloor(editRoom?.haName)

  function save(next: HouseConfiguration, message: string) {
    if (blocked) return false
    try {
      const valid = parseHouse(next)
      localStorage.setItem(HOUSE_KEY, JSON.stringify(valid))
      setConfig(valid); setError(''); setNotice(message)
      return true
    } catch (error) { setError(error instanceof Error && error.message !== 'Configuration invalide.' ? error.message : 'Enregistrement impossible. Les réglages précédents sont conservés.'); return false }
  }

  function saveUrl(event: FormEvent) {
    event.preventDefault()
    try {
      const address = homeAddress(url)
      if (save({ ...config, url: address }, 'Adresse de référence enregistrée sur cet appareil.')) setUrl(address)
    } catch { setError('Indiquez une adresse HTTP ou HTTPS, sans identifiant, jeton ni paramètres.') }
  }

  function saveRoom(event: FormEvent) {
    event.preventDefault()
    const name = roomName.trim()
    if (!name || !floor) return
    const id = editRoom?.id
    if (config.rooms.some(room => room.id !== id && roomKey(room.name) === roomKey(name) && room.floor === floor)) { setError('Cette pièce existe déjà à cet étage.'); return }
    const value: Room = { id: id || crypto.randomUUID(), name, floor }
    if (editRoom?.haName) value.haName = editRoom.haName
    const nextRooms = id ? config.rooms.map(room => room.id === id ? value : room) : [...config.rooms, value]
    if (save({ ...config, rooms: nextRooms }, editRoom ? 'Pièce modifiée dans Alfred.' : 'Pièce ajoutée.')) resetRoomForm()
  }

  function resetRoomForm() {
    setEditRoom(null)
    setRoomName('')
    if (!floor) setFloor('rdc')
  }

  function startRoomEdit({ name, local, haName }: ListedRoom) {
    setEditRoom({ id: local?.id, haName })
    setRoomName(name)
    setFloor(local?.floor ?? floorFromHomeAssistant(getHomeFloor(haName)))
    setError('')
    document.getElementById('house-room-name')?.focus()
  }

  function removeRoom(room: Room) {
    if (config.satellites.some(device => device.roomId === room.id) || config.browserRoomId === room.id) { setError('Cette pièce est affectée à un appareil. Changez son affectation avant de la supprimer.'); return }
    if (save({ ...config, rooms: config.rooms.filter(item => item.id !== room.id) }, 'Pièce supprimée.')) { setRemoved({ kind: 'room', item: room }); if (editRoom?.id === room.id) resetRoomForm(); if (deviceRoom === room.id) setDeviceRoom('') }
  }

  function resetDevice() { setDeviceForm(false); setDeviceName(''); setDeviceRoom(''); setEditDevice(null) }
  function saveDevice(event: FormEvent) {
    event.preventDefault()
    const name = deviceName.trim()
    if (!name || !deviceRoom) return
    if (config.satellites.some(device => device.id !== editDevice && device.name.toLocaleLowerCase('fr') === name.toLocaleLowerCase('fr'))) { setError('Un satellite porte déjà ce nom.'); return }
    const value: Satellite = { id: editDevice || crypto.randomUUID(), name, roomId: deviceRoom }
    if (save({ ...config, satellites: editDevice ? config.satellites.map(device => device.id === editDevice ? value : device) : [...config.satellites, value] }, editDevice ? 'Affectation modifiée.' : 'Satellite ajouté au répertoire local.')) resetDevice()
  }

  function restore() {
    if (!removed) return
    if (removed.kind === 'room') {
      const restored = removed.item
      if (config.rooms.some(room => room.id === restored.id || (restored.haName && room.haName === restored.haName) || (roomKey(room.name) === roomKey(restored.name) && room.floor === restored.floor))) { setError('Cette pièce existe déjà.'); return }
      if (save({ ...config, rooms: [...config.rooms, removed.item] }, 'Suppression annulée.')) setRemoved(null)
    } else {
      if (!config.rooms.some(room => room.id === (removed.item as Satellite).roomId)) { setError('Rétablissez d’abord la pièce de ce satellite.'); return }
      if (config.satellites.some(device => device.id === removed.item.id || device.name.toLocaleLowerCase('fr') === removed.item.name.toLocaleLowerCase('fr'))) { setError('Ce satellite existe déjà.'); return }
      if (save({ ...config, satellites: [...config.satellites, removed.item] }, 'Suppression annulée.')) setRemoved(null)
    }
  }

  return <div className="house-settings">
    <p className="settings-voice-note"><Info size={18} /><span>La pièce de ce navigateur donne son étage aux conversations avec Alfred. Les pièces ajoutées ici et le répertoire des satellites sont enregistrés sur cet appareil.</span></p>
    <section className="preference-group"><h2>Home Assistant</h2><div className="preference-card">
      <div className="house-connection"><span className="settings-section-icon"><House size={23} strokeWidth={1.6} /></span><strong>Home Assistant</strong><span className="house-status">{home.error ? 'Indisponible' : !home.data ? 'Chargement…' : home.data.verified ? 'Accès vérifié' : home.data.configured ? 'Configuré sur Alfred' : 'Non configuré'}</span></div>
      <form className="house-address" onSubmit={saveUrl}><label htmlFor="home-address">Adresse de référence locale</label><div><input id="home-address" type="url" inputMode="url" placeholder={home.data?.base_url ?? 'http://homeassistant.local:8123'} value={url} onChange={event => setUrl(event.target.value)} autoComplete="off" spellCheck={false} disabled={blocked} /><button className="icon-button" type="submit" aria-label="Enregistrer l’adresse" disabled={blocked}><Check size={20} /></button></div></form>
    </div></section>

    <HomeDeviceTable configured={!!home.data?.configured} registryRooms={registryRooms} onRegistryRooms={setRegistryRooms}
      roomLabels={roomLabels} localRoomNames={localRoomNames}
      setupMessage={home.error ? 'Connexion à Alfred indisponible.' : home.data && !home.data.configured ? 'Home Assistant doit être configuré sur Alfred.' : ''} />

    <section className="preference-group"><h2>Cet appareil</h2><div className="preference-card"><label className="preference-select"><span className="house-browser-label"><Smartphone size={21} /><strong>Pièce du navigateur</strong></span><select aria-label="Pièce du navigateur" value={config.browserRoomId} disabled={blocked || !config.rooms.length} onChange={event => save({ ...config, browserRoomId: event.target.value }, 'Pièce du navigateur enregistrée localement.')}><option value="">Non affecté</option>{config.rooms.map(room => <option key={room.id} value={room.id}>{room.name} · {floorNames[room.floor]}</option>)}</select></label></div></section>

    <section className="preference-group"><h2>Pièces</h2><div className="preference-card">
      <form className="house-room-form" onSubmit={saveRoom}>
        {editRoom?.haName && <p className="house-room-origin">Home Assistant · {editRoom.haName}
          {sourceFloor && ` · ${sourceFloor.name}`} · Personnalisation dans Alfred</p>}
        <div className="house-field-row">
          <label className="sr-only" htmlFor="house-room-name">Nom de la pièce</label>
          <input id="house-room-name" placeholder={editRoom ? 'Modifier la pièce' : 'Ajouter une pièce…'}
            value={roomName} onChange={event => setRoomName(event.target.value)} maxLength={60} required disabled={blocked} />
          <button className="icon-button" type="submit" aria-label={editRoom ? 'Enregistrer la pièce' : 'Ajouter la pièce'}
            disabled={blocked || !roomName.trim() || !floor}>{editRoom ? <Check size={20} /> : <Plus size={20} />}</button>
          {editRoom && <button className="icon-button" type="button" aria-label="Annuler la modification" onClick={resetRoomForm}><X size={18} /></button>}
        </div>
        <div className="house-floor-label">
          <label htmlFor="house-room-floor">Étage</label>
          <select id="house-room-floor" value={floor} onChange={event => setFloor(event.target.value as Floor | '')} disabled={blocked} required>
            {editRoom?.haName && !editRoom.id && <option value="" disabled>Choisir un étage</option>}
            <option value="rdc">Rez-de-chaussée</option><option value="etage1">Premier étage</option>
          </select>
        </div>
      </form>
      {rooms.length > 0 && <ul className="house-items" aria-label="Pièces">
        {rooms.map(room => {
          const haFloor = getHomeFloor(room.haName)
          const detail = [room.local && floorNames[room.local.floor], room.haName && 'Home Assistant',
            room.haName !== room.name && room.haName,
            haFloor && (!room.local || floorFromHomeAssistant(haFloor) !== room.local.floor) && haFloor.name,
            !room.local && room.haName && !haFloor && 'Étage non renseigné']
            .filter(Boolean).join(' · ')
          return <li key={room.haName ? `ha:${room.haName}` : `local:${room.local?.id}`}>
            <DoorOpen size={21} strokeWidth={1.6} aria-hidden="true" />
            <div><strong>{room.name}</strong><span>{detail}</span></div>
            <button type="button" className="icon-button" aria-label={`Modifier la pièce ${room.name}`}
              disabled={blocked} onClick={() => startRoomEdit(room)}><Pencil size={16} /></button>
            {room.local && <button type="button" className="icon-button"
              aria-label={room.haName ? `Retirer la personnalisation de ${room.name}` : `Supprimer la pièce ${room.name}`}
              disabled={blocked} onClick={() => { if (room.local) removeRoom(room.local) }}><Trash2 size={16} /></button>}
          </li>
        })}
      </ul>}
      {home.data?.configured && registryRooms === undefined
        ? <p className="house-empty" role="status">Chargement des pièces Home Assistant…</p>
        : (registryRooms === null || home.error)
          ? <p className="house-empty" role="status">Pièces Home Assistant indisponibles.</p>
          : !rooms.length && <p className="house-empty">Aucune pièce configurée.</p>}
    </div></section>

    <section className="preference-group"><h2>Satellites</h2><div className="preference-card">
      {terminal.data?.enabled && <div className="house-connection"><span className="settings-section-icon"><Radio size={20} /></span><strong>ESP32{terminal.data.room ? ` · ${terminal.data.room}` : ''}</strong><span className="house-status">{terminal.data.connected ? 'Connecté' : 'Déconnecté'}</span></div>}
      {config.satellites.length ? <ul className="house-items" aria-label="Satellites vocaux">{config.satellites.map(device => { const room = config.rooms.find(room => room.id === device.roomId); return <li key={device.id}><Radio size={22} strokeWidth={1.6} /><div><strong>{device.name}</strong><span>{room?.name} · {room ? floorNames[room.floor] : ''}</span></div><button className="icon-button" type="button" aria-label={`Modifier le satellite ${device.name}`} onClick={() => { setDeviceForm(true); setEditDevice(device.id); setDeviceName(device.name); setDeviceRoom(device.roomId) }}><Pencil size={16} /></button><button className="icon-button" type="button" aria-label={`Supprimer le satellite ${device.name}`} onClick={() => { if (save({ ...config, satellites: config.satellites.filter(item => item.id !== device.id) }, 'Satellite retiré du répertoire local.')) { setRemoved({ kind: 'satellite', item: device }); if (editDevice === device.id) resetDevice() } }}><Trash2 size={16} /></button></li> })}</ul> : <p className="house-empty">Aucun satellite ajouté au répertoire.</p>}
      {deviceForm ? <form className="house-device-form" onSubmit={saveDevice}><label htmlFor="satellite-name">Nom du satellite<input id="satellite-name" placeholder="Nom du satellite" value={deviceName} maxLength={60} onChange={event => setDeviceName(event.target.value)} required disabled={blocked} /></label><label>Pièce<select value={deviceRoom} onChange={event => setDeviceRoom(event.target.value)} required disabled={blocked}><option value="" disabled>Choisir une pièce</option>{config.rooms.map(room => <option key={room.id} value={room.id}>{room.name} · {floorNames[room.floor]}</option>)}</select></label><div className="house-device-actions"><button className="house-secondary" type="button" onClick={resetDevice}>Annuler</button><button className="house-secondary" type="submit" disabled={blocked || !deviceName.trim() || !deviceRoom}><Check size={17} />Enregistrer</button></div></form> : <button className="house-add-device" type="button" disabled={blocked || !config.rooms.length} onClick={() => { setDeviceForm(true); setDeviceRoom(config.rooms[0]?.id || '') }}><Plus size={19} />Ajouter un satellite</button>}
      {!config.rooms.length && <p className="house-empty house-empty-hint">Ajoutez d’abord une pièce pour y affecter un satellite.</p>}
    </div></section>
    {error && <p className="shopping-error" role="alert">{error}</p>}
    <div className="shopping-notice" role="status"><span>{notice}</span>{removed && <button type="button" onClick={restore}><Undo2 size={15} />Annuler la suppression</button>}</div>
  </div>
}
