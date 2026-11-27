import { useEffect, useRef, useState } from 'react'
import { decodeAudioBase64, encodeWav } from '../../alfred/static/audio-utils.mjs'
import { readConversation } from '../../alfred/static/conversation-stream.mjs'
import { SpeechTurn } from '../../alfred/static/speech-turn.mjs'
import recorderUrl from '../../alfred/static/recorder-worklet.js?url'
import { backendJson, backendRequest, errorText, jsonPost } from './backend'
import { loadHouse } from './house-model'
import type { Preferences } from './preferences'
import { useReplyAudio } from './reply-audio'
import { newId } from './ids'

export type ChatMessage = { id: string; author: 'user' | 'assistant'; text: string; sources?: Source[]; audio?: Blob }
type Source = { url: string; title: string }
type ChatEvent = { type: string; text?: string; sources?: Source[]; audio_base64?: string; needs_reply?: boolean }
type Phase = 'idle' | 'permission' | 'recording' | 'transcribing' | 'waiting'
type Turn = { controller: AbortController; finish?: () => void; answerReceived?: boolean }

function browserFloor() {
  const { config } = loadHouse()
  return config.rooms.find(room => room.id === config.browserRoomId)?.floor
}

function sourcesFrom(sources: Source[] | undefined) {
  return sources?.filter(source => {
    try { return typeof source.title === 'string' && ['http:', 'https:'].includes(new URL(source.url).protocol) }
    catch { return false }
  })
}

async function captureVoice(turn: Turn, onRecord: (analyser: AnalyserNode) => void, deadline?: number): Promise<ArrayBuffer | undefined> {
  const { signal } = turn.controller
  if (!navigator.mediaDevices?.getUserMedia) throw new Error('Le micro exige un navigateur compatible et une connexion sécurisée.')
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
  let context: AudioContext | undefined
  let recorder: AudioWorkletNode | undefined
  let limit: number | undefined
  let flushLimit: number | undefined
  let speechPoll: number | undefined
  try {
    signal.throwIfAborted()
    context = new AudioContext({ sampleRate: 48000 })
    await context.audioWorklet.addModule(recorderUrl)
    signal.throwIfAborted()
    recorder = new AudioWorkletNode(context, 'alfred-recorder')
    const source = context.createMediaStreamSource(stream)
    const analyser = context.createAnalyser()
    analyser.fftSize = 1024
    source.connect(analyser).connect(recorder).connect(context.destination)
    await context.resume()
    signal.throwIfAborted()
    const rate = context.sampleRate
    const gate = deadline === undefined ? null : new SpeechTurn({ sampleRate: rate, deadline })
    const chunks: Float32Array[] = []
    let frames = 0
    await new Promise<void>((resolve, reject) => {
      const node = recorder!
      const stop = () => reject(signal.reason)
      signal.addEventListener('abort', stop, { once: true })
      turn.finish = () => {
        if (gate) {
          gate.finish()
          resolve()
          return
        }
        if (flushLimit !== undefined) return
        node.port.postMessage('flush')
        flushLimit = window.setTimeout(() => reject(new Error('Le micro n’a pas terminé l’enregistrement.')), 1000)
      }
      node.port.onmessage = ({ data }) => {
        if (data === 'flushed') { signal.removeEventListener('abort', stop); resolve(); return }
        if (!(data instanceof Float32Array)) return
        if (gate) {
          if (gate.push(data, performance.now()).done) resolve()
          return
        }
        const chunk = data.subarray(0, rate * 30 - frames)
        if (chunk.length) { chunks.push(chunk); frames += chunk.length }
        if (frames >= rate * 30) turn.finish?.()
      }
      for (const track of stream.getAudioTracks()) track.addEventListener('ended', () => reject(new Error('Le microphone a été déconnecté.')), { once: true })
      if (gate) {
        if (gate.poll(performance.now()).done) { resolve(); return }
        speechPoll = window.setInterval(() => {
          if (gate.poll(performance.now()).done) resolve()
        }, 50)
      } else {
        limit = window.setTimeout(turn.finish, 30000)
      }
      onRecord(analyser)
    })
    signal.throwIfAborted()
    if (gate) return gate.hasSpeech ? encodeWav(gate.audioChunks(), rate) : undefined
    if (!frames) throw new Error('Aucun son enregistré.')
    return encodeWav(chunks, rate)
  } finally {
    window.clearTimeout(limit)
    window.clearTimeout(flushLimit)
    window.clearInterval(speechPoll)
    recorder?.port.close()
    stream.getTracks().forEach(track => track.stop())
    if (context) await context.close().catch(() => {})
  }
}

export function useChat(active: boolean, preferences: Preferences) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState('')
  const [microphoneDenied, setMicrophoneDenied] = useState(false)
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null)
  const { playback, play, pause, stop } = useReplyAudio(preferences.speechRate)
  const [webOverride, setWebOverride] = useState(false)
  const [session] = useState(() => ({ id: newId() }))
  const turn = useRef<Turn | null>(null)
  const visible = useRef(active)
  visible.current = active
  const dialogueEnabled = useRef(preferences.dialogue)
  dialogueEnabled.current = preferences.dialogue

  useEffect(() => {
    if (!active) {
      pause()
      if (turn.current?.finish || phase === 'permission') cancel()
    }
  }, [active, phase])
  useEffect(() => () => {
    turn.current?.controller.abort()
  }, [])
  useEffect(() => {
    function suspendCapture() {
      if (!document.hidden) return
      pause()
      if (turn.current?.finish || phase === 'permission') cancel()
    }
    document.addEventListener('visibilitychange', suspendCapture)
    return () => document.removeEventListener('visibilitychange', suspendCapture)
  }, [phase])

  function cancel() {
    turn.current?.controller.abort()
    turn.current = null
    setPhase('idle')
    setAnalyser(null)
    stop()
  }

  async function talk(input?: string, deadline?: number) {
    if (turn.current) return
    const current: Turn = { controller: new AbortController() }
    turn.current = current
    setError('')
    setMicrophoneDenied(false)
    stop()
    setPhase(input ? 'waiting' : 'permission')
    const user = newId()
    const assistant = newId()
    const signal = current.controller.signal
    const floor = browserFloor()
    const allowInternet = preferences.webSearch === 'when-needed' || (deadline === undefined && webOverride)
    setWebOverride(false)
    if (input) setMessages(previous => [...previous, { id: user, author: 'user', text: input }])
    let permissionLimit: number | undefined
    try {
      let response: Response
      if (input) {
        response = await backendRequest('conversation/text', {
          ...jsonPost({ text: input, session_id: session.id, floor_id: floor, speak: preferences.readReplies, allow_internet: allowInternet }), signal,
        })
      } else {
        if (deadline !== undefined) {
          permissionLimit = window.setTimeout(() => {
            if (turn.current === current) cancel()
          }, Math.max(0, deadline - performance.now()))
        }
        const wav = await captureVoice(current, node => {
          window.clearTimeout(permissionLimit)
          setAnalyser(node)
          setPhase('recording')
        }, deadline)
        signal.throwIfAborted()
        if (!wav) return
        current.finish = undefined
        setAnalyser(null)
        setPhase('transcribing')
        const headers: Record<string, string> = {
          'Content-Type': 'audio/wav',
          'X-Alfred-Session': session.id,
          'X-Alfred-Allow-Internet': String(allowInternet),
        }
        if (floor) headers['X-Alfred-Floor'] = floor
        response = await backendRequest('conversation/voice', { method: 'POST', body: wav, headers, signal })
      }
      if (!response.headers.get('content-type')?.includes('application/x-ndjson')) throw new Error('Réponse inattendue du serveur Alfred.')
      let replyAudio: Blob | undefined
      let needsReply = false
      await readConversation(response, (event: ChatEvent) => {
        if (signal.aborted) return
        if (event.type === 'answer' && event.text) current.answerReceived = true
        if (event.type === 'transcript' && event.text) {
          setMessages(previous => [...previous, { id: user, author: 'user', text: event.text! }])
        }
        if (['transcript', 'delta', 'answer'].includes(event.type)) setPhase('waiting')
        const audio = event.type === 'done' && event.audio_base64 && (!input || preferences.readReplies)
          ? decodeAudioBase64(event.audio_base64)
          : undefined
        if ((event.text || audio) && ['delta', 'answer', 'done'].includes(event.type)) {
          setMessages(previous => {
            const existing = previous.find(message => message.id === assistant)
            const text = event.type === 'delta' ? (existing?.text ?? '') + event.text : event.text || existing?.text
            if (!text) return previous
            const answer: ChatMessage = { id: assistant, author: 'assistant', text, sources: sourcesFrom(event.sources) ?? existing?.sources, audio: audio ?? existing?.audio }
            return existing ? previous.map(message => message.id === assistant ? answer : message) : [...previous, answer]
          })
        }
        if (audio) {
          replyAudio = audio
          needsReply = !input && event.needs_reply === true
        }
      })
      if (replyAudio && visible.current && !document.hidden && !signal.aborted) {
        play(assistant, replyAudio, true, needsReply ? () => {
          if (visible.current && !document.hidden && dialogueEnabled.current) {
            void talk(undefined, performance.now() + 8000)
          }
        } : undefined)
      }
    } catch (error) {
      if (!signal.aborted) {
        const denied = !input && error instanceof DOMException && error.name === 'NotAllowedError'
        setMicrophoneDenied(denied)
        const message = denied ? 'Accès au micro refusé. Vérifiez les autorisations du navigateur.' : errorText(error)
        // Les erreurs de synthèse du serveur peuvent inclure la réponse déjà affichée.
        const voiceNotice = current.answerReceived && message.match(/(?:^|\s)(Lecture vocale impossible\s*;|La lecture vocale a échoué\.)/u)
        setError(voiceNotice ? message.slice(voiceNotice.index).trimStart() : message)
      }
    } finally {
      window.clearTimeout(permissionLimit)
      if (turn.current === current) {
        turn.current = null
        setAnalyser(null)
        setPhase('idle')
      }
    }
  }

  async function reset() {
    cancel()
    setMessages([])
    setWebOverride(false)
    setError('')
    setMicrophoneDenied(false)
    const previous = session.id
    session.id = newId()
    const current = session.id
    try { await backendJson('conversation/reset', jsonPost({ session_id: previous })) }
    catch {
      if (session.id === current && !turn.current) setError('Nouvelle conversation ouverte. Le serveur n’a pas confirmé l’effacement de l’ancien contexte.')
    }
  }

  return { messages, phase, error, microphoneDenied, analyser, talk, cancel, reset, playback, play, webOverride, setWebOverride,
    microphone: () => turn.current?.finish ? turn.current.finish() : void talk() }
}
