import { useEffect, useRef } from 'react'
import { ArrowUp, Mic } from 'lucide-react'
import type { useChat } from './chat'

export function VoiceWaveform({ analyser }: { analyser: AnalyserNode }) {
  const line = useRef<SVGPathElement>(null)

  useEffect(() => {
    const path = line.current
    if (!path) return
    const samples = new Float32Array(analyser.fftSize)
    const columns = 24
    const samplesPerColumn = Math.floor(samples.length / columns)
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
    let frame: number

    function draw() {
      if (!path) return
      if (reducedMotion.matches) {
        path.setAttribute('d', 'M3 20H141')
        return
      }
      analyser.getFloatTimeDomainData(samples)
      let waveform = ''
      for (let column = 0; column < columns; column++) {
        const start = column * samplesPerColumn
        let peak = 0
        for (let index = start; index < start + samplesPerColumn; index++) {
          peak = Math.max(peak, Math.abs(samples[index]))
        }
        const height = Math.min(18, 0.5 + peak * 40)
        waveform += `M${3 + column * 6} ${20 - height}v${2 * height}`
      }
      path.setAttribute('d', waveform)
      frame = requestAnimationFrame(draw)
    }

    function restart() {
      cancelAnimationFrame(frame)
      draw()
    }
    draw()
    reducedMotion.addEventListener('change', restart)
    return () => {
      cancelAnimationFrame(frame)
      reducedMotion.removeEventListener('change', restart)
    }
  }, [analyser])

  return <svg className="voice-waveform" viewBox="0 0 144 40" aria-hidden="true">
    <path ref={line} d="M3 20H141" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
}

export function VoiceControls({ chat, primary = false }: {
  chat: Pick<ReturnType<typeof useChat>, 'phase' | 'microphone' | 'cancel'>
  primary?: boolean
}) {
  const recording = chat.phase === 'recording'
  const permission = chat.phase === 'permission'
  const roundMicrophone = primary && !recording
  return <div className="voice-controls">
    <button className={roundMicrophone ? 'voice-primary voice-microphone' : recording ? 'voice-primary' : 'voice-secondary'} type="button"
      aria-label={roundMicrophone ? 'Parler' : undefined}
      disabled={chat.phase !== 'idle' && !recording} onClick={chat.microphone}>
      {recording ? <ArrowUp size={20} aria-hidden="true" /> : <Mic size={roundMicrophone ? 40 : 20} aria-hidden="true" />}
      {!roundMicrophone && (recording ? 'Terminer et envoyer' : 'Parler')}
    </button>
    {(recording || permission) && <button className="voice-secondary" type="button" onClick={chat.cancel}>Annuler</button>}
  </div>
}
