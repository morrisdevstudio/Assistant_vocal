import asyncio
import io
import wave

import numpy as np
import pytest

from alfred.audio_stream import StreamingFlac, speech_blocks, trim_block_edges
from alfred.terminal import DirectTerminal


def wav_second():
    output = io.BytesIO()
    pcm = (np.sin(np.arange(44100) * 2 * np.pi * 180 / 44100) * 6000).astype("<i2")
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(44100)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def encode_pcm(samples, rate=16000):
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes(np.asarray(samples, dtype="<i2").tobytes())
    return output.getvalue()


def decode_pcm(data):
    with wave.open(io.BytesIO(data), "rb") as wav:
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")


@pytest.mark.parametrize("rate", [16000, 44100, 48000])
def test_boundary_trim_preserves_weak_consonants_and_internal_pauses(rate):
    # Les consonnes faibles dépassent juste le seuil ; les marges doivent
    # aussi les protéger, sans toucher au silence naturel au milieu de la phrase.
    speech = np.concatenate([np.full(round(rate*.05), 45), np.full(rate//2, 1500),
                             np.zeros(rate//3), np.full(rate//2, -1500),
                             np.full(round(rate*.05), -45)])
    original = encode_pcm(np.concatenate([np.zeros(rate//2), speech, np.zeros(rate*7//10)]), rate)
    trimmed, removed = trim_block_edges(original)
    values = decode_pcm(trimmed)
    first = np.flatnonzero(values)[0]
    assert np.array_equal(values[first:first + len(speech)], speech)
    assert .08 <= first / rate <= .10
    assert .18 <= (len(values)-first-len(speech)) / rate <= .20
    assert removed > 850


def test_only_junction_edges_are_trimmed_and_silence_is_not_guessed():
    samples = np.concatenate([np.zeros(8000), np.full(16000, 1500), np.zeros(11200)])
    original = encode_pcm(samples)
    assert trim_block_edges(original, first=True, last=True) == (original, 0)
    first_wav, _ = trim_block_edges(original, first=True)
    assert np.array_equal(decode_pcm(first_wav)[:8000], samples[:8000])
    last_wav, _ = trim_block_edges(original, last=True)
    assert np.count_nonzero(decode_pcm(last_wav)[-11200:]) == 0
    silent = encode_pcm(np.zeros(32000))
    assert trim_block_edges(silent) == (silent, 0)


def test_speech_blocks_preserve_words_and_punctuation():
    text = ("Bonjour. Je suis Alfred, votre assistant pour la maison. "
            "Il fait 12.5 degrés. Je reste à votre disposition pour la suite.")
    blocks = speech_blocks(text)
    assert " ".join(blocks) == text
    assert len(blocks) >= 2
    assert "12.5" in " ".join(blocks)


def test_long_sentence_is_bounded_without_an_isolated_short_greeting():
    text = "Bien. " + " ".join(["consultation"] * 70) + "."
    blocks = speech_blocks(text)
    assert " ".join(blocks) == text
    assert len(blocks[0]) >= 40
    assert all(len(block) <= 220 for block in blocks)


def test_chunked_http_sends_audio_before_the_next_block_is_available():
    av = pytest.importorskip("av")
    async def scenario():
        stream = StreamingFlac()
        await asyncio.to_thread(stream.feed, wav_second())
        assert not stream.done
        terminal = DirectTerminal(None, None, None)
        terminal.peer = "127.0.0.1"
        path = terminal.tickets.put_stream(stream)
        server = await asyncio.start_server(terminal._http, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        try:
            writer.write(f"GET {path} HTTP/1.1\r\nHost: test\r\n\r\n".encode())
            await writer.drain()
            headers = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 3)
            assert b"Transfer-Encoding: chunked" in headers
            size = int((await reader.readline()).strip(), 16)
            body = bytearray(await reader.readexactly(size))
            await reader.readexactly(2)
            assert body.startswith(b"fLaC")
            assert stream.blocks == 1 and not stream.done
            # Le premier bloc a déjà quitté HTTP. Le second est encore à produire.
            await asyncio.to_thread(stream.feed, wav_second())
            await asyncio.to_thread(stream.finish)
            while True:
                size = int((await reader.readline()).strip(), 16)
                if size == 0:
                    await reader.readexactly(2)
                    break
                body.extend(await reader.readexactly(size))
                await reader.readexactly(2)
            with av.open(io.BytesIO(body)) as audio:
                frames = list(audio.decode(audio=0))
                assert sum(frame.samples for frame in frames) == 96000
                assert all(frame.sample_rate == 48000 for frame in frames)
            assert terminal.tickets.downloads == 1
        finally:
            writer.close();await writer.wait_closed()
            server.close();await server.wait_closed()
    asyncio.run(scenario())


def test_cancelling_progressive_reply_discards_pending_audio_and_closes_voice():
    pytest.importorskip("av")
    import threading
    from alfred.terminal import TerminalConfig
    async def scenario():
        computing = threading.Event()
        release = threading.Event()
        closed = threading.Event()
        def generate(blocks):
            try:
                yield wav_second(), 1
                computing.set()
                release.wait(5)
                yield wav_second(), 1
                pytest.fail("Aucun bloc supplémentaire après annulation")
            finally:
                closed.set()
        terminal = DirectTerminal(TerminalConfig("board.local", "00:11:22:33:44:55", "127.0.0.1"),
                                  None, None, generate)
        terminal._event = lambda *args: None
        task = asyncio.create_task(terminal._stream_reply({"text": "Une réponse assez longue pour plusieurs blocs.",
                                                           "timings": {}}, 0))
        try:
            assert await asyncio.to_thread(computing.wait, 3)
            task.cancel()
            await asyncio.sleep(0)
        finally:
            release.set()
            result = await asyncio.gather(task, return_exceptions=True)
        assert isinstance(result[0], asyncio.CancelledError)
        assert closed.is_set()
        stream = next(iter(terminal.tickets.items.values()))[1]
        assert stream.blocks == 1
        assert stream.error == "CancelledError"
    asyncio.run(scenario())
