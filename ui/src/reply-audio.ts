import { useCallback, useEffect, useRef, useState } from 'react'

type Clip = { id: string; audio: HTMLAudioElement; url: string; afterPlayback?: () => void }
type Playback = { id: string; state: 'playing' | 'error' }

function release(clip: Clip) {
  clip.audio.onplay = clip.audio.onpause = clip.audio.onended = null
  clip.audio.pause()
  URL.revokeObjectURL(clip.url)
}

export function useReplyAudio(rate: number) {
  const current = useRef<Clip | null>(null)
  const [playback, setPlayback] = useState<Playback | null>(null)
  const playbackRate = useRef(rate)
  playbackRate.current = rate

  useEffect(() => {
    if (current.current) current.current.audio.playbackRate = rate
  }, [rate])
  useEffect(() => () => {
    if (current.current) release(current.current)
    current.current = null
  }, [])

  const stop = useCallback(() => {
    if (current.current) release(current.current)
    current.current = null
    setPlayback(null)
  }, [])

  const pause = useCallback(() => {
    if (!current.current) return
    current.current.afterPlayback = undefined
    current.current.audio.pause()
  }, [])

  const play = useCallback((id: string, blob: Blob, automatic = false, afterPlayback?: () => void) => {
    if (current.current?.id !== id) {
      stop()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      const clip: Clip = { id, audio, url, afterPlayback }
      current.current = clip
      audio.playbackRate = playbackRate.current
      const sync = () => {
        if (current.current === clip) {
          setPlayback(audio.paused || audio.ended ? null : { id, state: 'playing' })
        }
      }
      audio.onplay = sync
      audio.onpause = () => {
        if (!audio.ended) clip.afterPlayback = undefined
        sync()
      }
      audio.onended = () => {
        const after = clip.afterPlayback
        clip.afterPlayback = undefined
        sync()
        if (current.current === clip) after?.()
      }
    }
    const clip = current.current
    if (!automatic && !clip.audio.paused && !clip.audio.ended) {
      clip.audio.pause()
      return
    }
    setPlayback(null)
    void clip.audio.play().catch(error => {
      clip.afterPlayback = undefined
      if (!automatic && current.current === clip && error?.name !== 'AbortError') {
        setPlayback({ id, state: 'error' })
      }
    })
  }, [stop])

  return { playback, play, pause, stop }
}
