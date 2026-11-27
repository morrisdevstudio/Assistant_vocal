// Identifiants locaux (minuteurs, courses, rappels, sessions de conversation).
// `crypto.randomUUID` n'existe qu'en contexte sécurisé : sans HTTPS ni
// localhost, l'appel lève une exception et l'écran reste vide. Un repli sur
// `crypto.getRandomValues` garde l'interface utilisable sur un accès HTTP du
// réseau local, qui reste sans micro ni service worker.

type RandomSource = Pick<Crypto, 'randomUUID'> & Partial<Pick<Crypto, 'getRandomValues'>>

function fallbackId(source: RandomSource): string {
  const bytes = new Uint8Array(16)
  if (typeof source.getRandomValues === 'function') source.getRandomValues(bytes)
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256)
  // Version 4 et variante RFC 4122, comme `crypto.randomUUID`.
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

export function newId(source: RandomSource | undefined = globalThis.crypto): string {
  if (source && typeof source.randomUUID === 'function') return source.randomUUID()
  return fallbackId(source ?? ({} as RandomSource))
}
