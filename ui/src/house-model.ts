export type Floor = 'rdc' | 'etage1'
export type HomeFloor = { name: string; level: number | null }
export type HomeRoomRegistry = { rooms: string[]; floors: Record<string, HomeFloor> }
export type Room = { id: string; name: string; floor: Floor; haName?: string }
export type Satellite = { id: string; name: string; roomId: string }
export type HouseConfiguration = { url: string; rooms: Room[]; satellites: Satellite[]; browserRoomId: string }
export const HOUSE_KEY = 'alfred.house.v1'
export const emptyHouse: HouseConfiguration = { url: '', rooms: [], satellites: [], browserRoomId: '' }
export const floorNames = { rdc: 'Rez-de-chaussée', etage1: 'Premier étage' }

export function floorFromHomeAssistant(floor?: HomeFloor): Floor | '' {
  if (!floor) return ''
  if (floor.level === 0) return 'rdc'
  if (floor.level === 1) return 'etage1'
  if (floor.level !== null) return ''
  const label = floor.name.toLocaleLowerCase('fr').normalize('NFD').replace(/\p{Diacritic}/gu, '')
    .replace(/[^a-z0-9]+/g, ' ').trim()
  if (['rez de chaussee', 'rdc', 'etage 0', 'niveau 0'].includes(label)) return 'rdc'
  if (['premier etage', '1er etage', 'etage 1', 'niveau 1', 'premier'].includes(label)) return 'etage1'
  return ''
}

export function homeAddress(value: string) {
  const text = value.trim()
  if (!text) return ''
  const url = new URL(text)
  if (!['http:', 'https:'].includes(url.protocol) || !url.hostname || url.username || url.password || url.search || url.hash) throw Error('Indiquez une adresse HTTP ou HTTPS, sans identifiant, jeton ni paramètres.')
  return url.toString().replace(/\/$/, '')
}

export function parseHouse(value: unknown): HouseConfiguration {
  if (!value || typeof value !== 'object') throw Error('Configuration invalide.')
  const data = value as Record<string, unknown>
  if (typeof data.url !== 'string' || typeof data.browserRoomId !== 'string' || !Array.isArray(data.rooms) || !Array.isArray(data.satellites)) throw Error('Configuration invalide.')
  const ids = new Set<string>()
  const linkedAreas = new Set<string>()
  const rooms: Room[] = data.rooms.map(room => {
    if (!room || typeof room.id !== 'string' || !room.id || ids.has(room.id) || typeof room.name !== 'string' || !room.name.trim() || room.name.length > 60 || !['rdc', 'etage1'].includes(room.floor)) throw Error('Pièce invalide.')
    ids.add(room.id)
    const value: Room = { id: room.id, name: room.name.trim(), floor: room.floor as Floor }
    if (room.haName !== undefined) {
      if (typeof room.haName !== 'string' || !room.haName.trim() || linkedAreas.has(room.haName)) throw Error('Pièce Home Assistant invalide.')
      linkedAreas.add(room.haName)
      value.haName = room.haName
    }
    return value
  })
  const deviceIds = new Set<string>()
  const satellites: Satellite[] = data.satellites.map(device => {
    if (!device || typeof device.id !== 'string' || !device.id || deviceIds.has(device.id) || typeof device.name !== 'string' || !device.name.trim() || device.name.length > 60 || typeof device.roomId !== 'string' || !ids.has(device.roomId)) throw Error('Satellite invalide.')
    deviceIds.add(device.id)
    return { id: device.id, name: device.name.trim(), roomId: device.roomId }
  })
  if (data.browserRoomId && !ids.has(data.browserRoomId)) throw Error('Pièce du navigateur invalide.')
  return { url: homeAddress(data.url), rooms, satellites, browserRoomId: data.browserRoomId }
}

export function loadHouse() {
  try {
    const saved = localStorage.getItem(HOUSE_KEY)
    return { config: saved ? parseHouse(JSON.parse(saved)) : { ...emptyHouse }, error: '' }
  } catch {
    return { config: { ...emptyHouse }, error: 'Les réglages enregistrés sont inaccessibles. Rouvrez l’application pour réessayer ; aucune donnée existante ne sera écrasée.' }
  }
}
