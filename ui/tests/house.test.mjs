import assert from 'node:assert/strict'
import test from 'node:test'
import { emptyHouse, floorFromHomeAssistant, homeAddress, loadHouse, parseHouse } from '../src/house-model.ts'

const house = () => ({ url: 'http://homeassistant.local:8123/', rooms: [{ id: 'r1', name: 'Bureau', floor: 'rdc' }], satellites: [{ id: 's1', name: 'Satellite test', roomId: 'r1' }], browserRoomId: 'r1' })

test('les étages Home Assistant compatibles préremplissent l’étage Alfred', () => {
  assert.equal(floorFromHomeAssistant({ name: 'Bas', level: 0 }), 'rdc')
  assert.equal(floorFromHomeAssistant({ name: 'Haut', level: 1 }), 'etage1')
  assert.equal(floorFromHomeAssistant({ name: '1er étage', level: null }), 'etage1')
  assert.equal(floorFromHomeAssistant({ name: 'Sous-sol', level: -1 }), '')
  assert.equal(floorFromHomeAssistant(), '')
})

test('adresse Home Assistant normalisée sans stocker de secrets dans l’URL', () => {
  assert.equal(homeAddress(' http://homeassistant.local:8123/ '), 'http://homeassistant.local:8123')
  assert.equal(homeAddress('https://example.test/ha/'), 'https://example.test/ha')
  for (const url of ['file:///a', 'javascript:alert(1)', 'https://user:password@example.test', 'https://example.test/?token=secret', 'https://example.test/#secret']) assert.throws(() => homeAddress(url))
})

test('pièces et affectations survivent à une sauvegarde/relecture', () => {
  const saved = parseHouse(JSON.parse(JSON.stringify(house())))
  assert.equal(saved.url, 'http://homeassistant.local:8123')
  assert.equal(saved.satellites[0].roomId, saved.rooms[0].id)
  assert.equal(saved.browserRoomId, 'r1')
})

test('affectations orphelines et identifiants dupliqués refusés', () => {
  assert.throws(() => parseHouse({ ...house(), rooms: [] }))
  assert.throws(() => parseHouse({ ...house(), browserRoomId: 'unknown' }))
  assert.throws(() => parseHouse({ ...house(), rooms: [house().rooms[0], house().rooms[0]] }))
  assert.throws(() => parseHouse({ ...house(), satellites: [house().satellites[0], house().satellites[0]] }))
})

test('une pièce Home Assistant renommée garde sa référence et son affectation locale', () => {
  const config = house()
  config.rooms[0] = { ...config.rooms[0], name: 'Mon bureau', haName: 'Bureau', floor: 'etage1' }
  assert.deepEqual(parseHouse(JSON.parse(JSON.stringify(config))).rooms, config.rooms)
  assert.equal(parseHouse(config).browserRoomId, 'r1')
  assert.throws(() => parseHouse({ ...config, rooms: [...config.rooms, { ...config.rooms[0], id: 'r2' }] }))
})

test('aucun faux appareil au premier lancement, stockage corrompu protégé', () => {
  globalThis.localStorage = { getItem: () => null }
  assert.deepEqual(loadHouse().config, emptyHouse)
  globalThis.localStorage = { getItem: () => '{invalid' }
  assert.notEqual(loadHouse().error, '')
})
