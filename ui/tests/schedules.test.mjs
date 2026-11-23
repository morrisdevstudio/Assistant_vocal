import assert from 'node:assert/strict'
import test from 'node:test'
import { clock, finishTimers, isReminder, isTimer, localDate, remaining, toggleTimer } from '../src/schedule-model.ts'

const timer = () => ({ id: 'tea', title: 'Thé', durationMs: 60000, remainingMs: 60000, endsAt: 61000, finished: false })

test('le décompte utilise la date de fin après suspension du navigateur', () => {
  const saved = JSON.parse(JSON.stringify(timer()))
  assert.equal(remaining(saved, 31000), 30000)
  assert.equal(remaining(saved, 100000), 0)
  const [expired] = finishTimers([saved], 100000)
  assert.equal(expired.finished, true)
  assert.equal(expired.endsAt, null)
  assert.equal(expired.remainingMs, 0)
})

test('la pause fige la durée, la reprise utilise le nouvel instant', () => {
  const paused = toggleTimer(timer(), 11000)
  assert.equal(remaining(paused, 900000), 50000)
  const resumed = toggleTimer(paused, 900000)
  assert.equal(resumed.endsAt, 950000)
  assert.equal(remaining(resumed, 910000), 40000)
})

test('pause à échéance et relance ne fabriquent pas de durée négative', () => {
  const expired = toggleTimer(timer(), 70000)
  assert.equal(expired.finished, true)
  const restarted = toggleTimer(expired, 80000)
  assert.equal(restarted.endsAt, 140000)
  assert.equal(restarted.finished, false)
  assert.equal(remaining(restarted, 80000), 60000)
})

test('seules les minuteries réellement échues sont terminées', () => {
  const paused = { ...timer(), id: 'paused', endsAt: null, remainingMs: 42000 }
  const future = { ...timer(), id: 'future', endsAt: 200000 }
  const result = finishTimers([timer(), paused, future], 100000)
  assert.equal(result[0].finished, true)
  assert.equal(result[1], paused)
  assert.equal(result[2], future)
  assert.deepEqual(finishTimers(result, 110000), result)
})

test('affichage sans zéro prématuré et avec heures pour les longues durées', () => {
  assert.equal(clock(1), '00:01')
  assert.equal(clock(59999), '01:00')
  assert.equal(clock(0), '00:00')
  assert.equal(clock(-1000), '00:00')
  assert.equal(clock(3661000), '01:01:01')
})

test('stockage invalide rejeté et dates de formulaire dans le fuseau local', () => {
  assert.equal(isTimer(timer()), true)
  assert.equal(isTimer({ ...timer(), endsAt: 'tomorrow' }), false)
  assert.equal(isTimer({ ...timer(), durationMs: Infinity }), false)
  assert.equal(isTimer({ ...timer(), remainingMs: -1 }), false)
  assert.equal(isReminder({ id: 'a', title: 'Sortir les poubelles', dueAt: 1800000000000, done: false }), true)
  assert.equal(isReminder({ id: 'a', title: 'Test', dueAt: NaN, done: false }), false)
  assert.equal(localDate(new Date(2026, 10, 17, 0, 30)), '2026-11-17')
})
