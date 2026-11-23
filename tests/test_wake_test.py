import asyncio
from types import SimpleNamespace
import pytest
from alfred.wake_test import WakeTest

class Detector:
    name = 'openwakeword'
    def __init__(self): self.resets = 0
    def reset_audio(self): self.resets += 1
    def status(self): return {'score': .42, 'inferences': 4}

class Journal:
    def __init__(self): self.events = []
    def append(self, event): self.events.append(event)

class Terminal:
    def __init__(self):
        self.connected = True; self.wake_armed = True; self.wake_detector = Detector(); self.wake_test = None
    def wake_status(self): return {'receiving': True}
    def stop_wake_word(self): self.wake_armed = False

class Manager:
    owner = 'esp32'
    preferences = SimpleNamespace(values={'esp32': {'engine':'openwakeword','threshold':.3}}, phrases=lambda _: ['Jarvis'])
    def occupied(self): return False

def test_guided_trials_and_duplicate_results():
    async def run():
        terminal = Terminal(); journal = Journal(); test = WakeTest(terminal,Manager(),journal)
        await test.start(); test.phase = 'placement'; test.ready()
        test.observe((1000).to_bytes(2,'little',signed=True)*1280)
        test.detected()
        assert test.results[0]['outcome'] == 'detected'
        assert test.results[0]['score_max'] == .42
        with pytest.raises(ValueError): test.record('missed')
        test.phase = 'trial'; test.record('missed')
        assert len(test.results) == 2
        await test.finish('arrete'); await asyncio.sleep(.1)
        assert terminal.wake_test is None and terminal.wake_armed
        assert any(e['event'] == 'fin' for e in journal.events)
    asyncio.run(run())

def test_skipped_distance_is_not_a_missed_call():
    async def run():
        t=Terminal(); test=WakeTest(t,Manager(),Journal()); await test.start()
        test.phase='placement'; test.skip()
        assert len(test.results)==5 and all(r['outcome']=='skipped' for r in test.results)
        await test.finish('arrete'); await asyncio.sleep(.05)
    asyncio.run(run())


def test_stt_diagnostics_are_limited_to_active_trial_and_saved():
    async def run():
        terminal = Terminal(); journal = Journal(); test = WakeTest(terminal, Manager(), journal)
        await test.start()
        test.observe_stt('parole hors essai', False, True, 200)
        test.phase = 'placement'; test.ready()
        test.observe_stt('Al frais', False, True, 250)
        test.record('missed')
        test.observe_stt('parole tardive', False, True, 250)
        assert test.results[0]['stt_observations'] == [
            {'text': 'Al frais', 'matched': False, 'final': True, 'duration_ms': 250}]
        await test.finish('arrete')
        assert any(e.get('event') == 'fin' and e['results'][0]['stt_observations'] for e in journal.events)
    asyncio.run(run())
