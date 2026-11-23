import type { TimerTone } from './preferences'

export function playTimerTone(context: AudioContext, tone: TimerTone) {
  const notes = tone === 'chime' ? [523, 659, 784] : [740, 740, 740]
  const startTime = context.currentTime
  notes.forEach((frequency, index) => {
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.connect(gain)
    gain.connect(context.destination)
    oscillator.frequency.value = frequency
    const start = startTime + index * .32
    gain.gain.setValueAtTime(0, start)
    gain.gain.linearRampToValueAtTime(.12, start + .02)
    gain.gain.exponentialRampToValueAtTime(.001, start + .22)
    oscillator.onended = () => { oscillator.disconnect(); gain.disconnect() }
    oscillator.start(start)
    oscillator.stop(start + .25)
  })
}
