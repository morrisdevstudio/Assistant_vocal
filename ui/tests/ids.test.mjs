import assert from 'node:assert/strict'
import test from 'node:test'
import { newId } from '../src/ids.ts'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/

test('un identifiant est produit sans crypto.randomUUID', () => {
  const id = newId({ getRandomValues: bytes => { bytes.fill(7); return bytes } })
  assert.equal(id, '07070707-0707-4707-8707-070707070707')
})

test('sans aucune source cryptographique, un identifiant reste produit', () => {
  assert.match(newId(null), UUID)
})

test('crypto.randomUUID reste utilisé quand il existe', () => {
  assert.equal(newId({ randomUUID: () => 'fourni' }), 'fourni')
  assert.match(newId(undefined), UUID)
})
