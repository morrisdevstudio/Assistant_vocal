"""Session de test du réveil sans exécution de commande."""
import asyncio
import time
import uuid
import numpy as np

DISTANCES = [0.5]*5 + [1]*10 + [2]*5 + [3]*5

class WakeTest:
    def __init__(self, terminal, manager, journal):
        self.terminal, self.manager, self.journal = terminal, manager, journal
        self.id = uuid.uuid4().hex
        self.settings = dict(manager.preferences.values['esp32'])
        self.phrase = manager.preferences.phrases('esp32')[0]
        self.previous_armed = terminal.wake_armed
        self.phase = 'silence_initial'
        self.phase_at = self.heartbeat = time.monotonic()
        self.results = []
        self.silence_detections = 0
        self.disconnections = 0
        self.grace_until = time.monotonic() + 6
        self.closed = False
        self.reset_metrics()

    async def start(self):
        t = self.terminal
        if not t.connected or self.manager.occupied() or self.manager.owner == 'browser':
            raise ValueError('ESP32 déconnecté ou occupé ; vérifiez la connexion.')
        if not t.wake_detector:
            raise ValueError('Détecteur de réveil indisponible.')
        if not t.wake_armed:
            await t.start_wake_word()
        t.wake_test = self
        self.task = asyncio.create_task(self.monitor())
        self.log('debut')

    def log(self, event, **fields):
        payload = dict(source='wake-test', event=event, test_id=self.id,
                       settings=self.settings, phrase=self.phrase, **fields)
        async def write():
            try:
                await asyncio.to_thread(self.journal.append, payload)
            except Exception:
                import logging
                logging.getLogger('alfred').warning('Journal du test de réveil indisponible')
        asyncio.create_task(write())

    def reset_metrics(self):
        self.peak = self.rms_max = self.clipped = self.samples = 0
        self.score_max = self.score_time = None
        self.stt_observations = []

    def observe_stt(self, text, matched, final, duration):
        if self.phase != 'trial':
            return
        self.stt_observations.append(dict(text=str(text)[:80], matched=matched,
                                          final=final, duration_ms=duration))
        del self.stt_observations[:-5]

    def observe(self, data):
        if self.phase not in ('trial', 'silence_initial', 'silence_final') or not data or len(data)%2:
            return
        samples = np.frombuffer(data, dtype='<i2').astype('int32')
        if not len(samples): return
        self.peak = max(self.peak, int(np.max(np.abs(samples))))
        self.rms_max = max(self.rms_max, float(np.sqrt(np.mean(samples.astype('float64')**2))))
        self.clipped += int(np.count_nonzero(np.abs(samples) >= 32760))
        self.samples += len(samples)
        score = self.terminal.wake_detector.status().get('score')
        if score is not None and (self.score_max is None or score > self.score_max):
            self.score_max, self.score_time = score, time.time()

    def metrics(self):
        status = self.terminal.wake_detector.status()
        return dict(peak=self.peak, rms_max=round(self.rms_max, 1),
                    clipped_fraction=self.clipped/self.samples if self.samples else 0,
                    score_max=self.score_max, score_time=self.score_time,
                    stt_observations=list(self.stt_observations),
                    vad_probability=status.get('vad_probability'),
                    inferences=status.get('inferences'), error=status.get('error'))

    def detected(self):
        if self.phase in ('silence_initial', 'silence_final'):
            self.silence_detections += 1
            self.terminal.wake_detector.reset_audio()
        elif self.phase == 'trial':
            self.record('detected')
        else:
            self.terminal.wake_detector.reset_audio()

    def record(self, outcome):
        if self.phase != 'trial': raise ValueError('Aucun essai en cours.')
        result = dict(number=len(self.results)+1, distance=DISTANCES[len(self.results)],
                      outcome=outcome, **self.metrics())
        self.results.append(result)
        self.log('essai', result=result)
        self.terminal.wake_detector.reset_audio()
        self.phase, self.phase_at = 'pause', time.monotonic()

    def retry(self):
        if self.phase != 'trial': raise ValueError('Aucun essai à recommencer.')
        self.terminal.wake_detector.reset_audio()
        self.phase, self.phase_at = 'pause', time.monotonic()

    def ready(self):
        if self.phase != 'placement': raise ValueError('Placement déjà confirmé.')
        self.reset_metrics()
        self.terminal.wake_detector.reset_audio()
        self.phase, self.phase_at = 'trial', time.monotonic()

    def skip(self):
        if self.phase != 'placement': raise ValueError('Choisissez une distance avant de passer.')
        distance = DISTANCES[len(self.results)]
        while len(self.results) < len(DISTANCES) and DISTANCES[len(self.results)] == distance:
            result = dict(number=len(self.results)+1, distance=distance, outcome='skipped')
            self.results.append(result)
            self.log('essai', result=result)
        self.phase, self.phase_at = 'pause', time.monotonic()

    async def monitor(self):
        while not self.closed:
            await asyncio.sleep(.25)
            now = time.monotonic()
            if now-self.heartbeat > 30:
                await self.finish('page_absente'); return
            if not self.terminal.connected or not self.terminal.wake_armed or not self.terminal.wake_status()['receiving']:
                if now < self.grace_until:
                    self.phase_at = now
                    continue
                if self.phase != 'interrupted':
                    self.disconnections += 1
                    self.log('flux_interrompu', phase=self.phase)
                    self.phase = 'interrupted'
                continue
            if self.phase == 'interrupted':
                self.terminal.wake_detector.reset_audio()
                self.phase, self.phase_at = 'placement', now
            elif self.phase in ('silence_initial', 'silence_final') and now-self.phase_at >= 30:
                self.log(self.phase, detections=self.silence_detections, metrics=self.metrics())
                if self.phase == 'silence_final':
                    await self.finish('termine'); return
                self.silence_detections = 0
                self.phase, self.phase_at = 'placement', now
            elif self.phase == 'pause' and now-self.phase_at >= 3:
                if len(self.results) == len(DISTANCES):
                    self.reset_metrics(); self.silence_detections = 0
                    self.phase, self.phase_at = 'silence_final', now
                elif len(self.results) in (5, 15, 20):
                    self.phase, self.phase_at = 'placement', now
                else:
                    self.reset_metrics(); self.terminal.wake_detector.reset_audio()
                    self.phase, self.phase_at = 'trial', now

    async def finish(self, reason):
        if self.closed: return
        self.closed = True
        self.phase = 'termine' if reason == 'termine' else 'interrompu'
        try:
            await asyncio.to_thread(self.journal.append, dict(source='wake-test', event='fin',
                test_id=self.id, settings=self.settings, phrase=self.phrase, reason=reason,
                results=self.results, disconnections=self.disconnections))
        except Exception:
            import logging
            logging.getLogger('alfred').warning('Bilan du test de réveil indisponible')
        self.terminal.wake_detector.reset_audio()
        self.terminal.wake_test = None
        if not self.previous_armed: self.terminal.stop_wake_word()

    def snapshot(self):
        self.heartbeat = time.monotonic()
        return dict(id=self.id, phase=self.phase, phrase=self.phrase, settings=self.settings,
                    results=self.results, number=min(len(self.results)+1,len(DISTANCES)),
                    distance=DISTANCES[min(len(self.results),len(DISTANCES)-1)],
                    remaining=max(0,round(30-(time.monotonic()-self.phase_at))),
                    trial_elapsed=round(time.monotonic()-self.phase_at) if self.phase == 'trial' else 0,
                    silence_detections=self.silence_detections, metrics=self.metrics(), closed=self.closed)
