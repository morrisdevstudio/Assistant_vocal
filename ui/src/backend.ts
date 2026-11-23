import { useEffect, useRef, useState } from 'react'
import type { Floor } from './house-model'

export type AlfredStatus = {
  version: string
  scheduler_ok: boolean
  capabilities: { home_assistant: boolean; esp32: boolean; stt: boolean; tts: boolean; music: boolean }
}
export type ServiceStatus = { configured: boolean; access_verified: boolean; model?: string }
export type TerminalStatus = { enabled: boolean; connected: boolean; room: string | null }
export type Target = { room: string; floor_id: Floor }

export function errorText(error: unknown) {
  return error instanceof Error && !(error instanceof TypeError) ? error.message : 'Connexion au serveur Alfred impossible.'
}

export async function backendRequest(path: string, init: RequestInit = {}) {
  const response = await fetch('/api/' + path, { cache: 'no-store', ...init })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(typeof body?.detail === 'string' ? body.detail : `Serveur Alfred indisponible (${response.status}).`)
  }
  return response
}

export function jsonPost(body: unknown): RequestInit {
  return { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}

export async function backendJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await backendRequest(path, init)
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Réponse inattendue du serveur Alfred.')
  return response.json()
}

export function useRemote<T>(path: string | null, interval = 0, delay = 0) {
  const [result, setResult] = useState<{ path: string; data: T | null; error: string }>()
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    let pending = false
    let timer: number
    async function load() {
      if (!path || pending || controller.signal.aborted || document.hidden) return
      pending = true
      try {
        const data = await backendJson<T>(path, { signal: controller.signal })
        if (!controller.signal.aborted) setResult({ path, data, error: '' })
      } catch (error) {
        if (!controller.signal.aborted) setResult({ path, data: null, error: errorText(error) })
      } finally {
        pending = false
        if (interval && !controller.signal.aborted && !document.hidden) {
          timer = window.setTimeout(load, interval)
        }
      }
    }
    function onVisibilityChange() {
      window.clearTimeout(timer)
      if (!document.hidden && !pending) timer = window.setTimeout(load, delay)
    }
    if (!document.hidden) timer = window.setTimeout(load, delay)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      controller.abort()
      window.clearTimeout(timer)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [path, interval, delay, revision])
  const current = path && result?.path === path ? result : null
  return { data: current?.data ?? null, error: current?.error ?? '', reload: () => setRevision(value => value + 1) }
}

export function useServerAction() {
  const lock = useRef(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function run<T>(action: () => Promise<T>) {
    if (lock.current) return undefined
    lock.current = true
    setBusy(true)
    setError('')
    try { return await action() }
    catch (error) { setError(errorText(error)); return undefined }
    finally { lock.current = false; setBusy(false) }
  }
  return { busy, error, run }
}
