// Adapté de Kieirra/murmure 1.11.3 audio/{chunking,pipeline}.rs.
// AGPL-3.0-or-later. Sans UI ni prévisualisation ; prises bornées à 30 s.
use crate::clean::strip_fillers_and_repeats;
use crate::dictionary::{correct_transcription, sync_boost_words};
use crate::engine::transcription_engine::TranscriptionEngine;
use crate::engine::ParakeetEngine;
use crate::formatting_rules::{formatter::apply_formatting, types::FormattingSettings};
use crate::vad::{AdaptiveVad, VoiceActivity};

pub fn split_chunks(samples: &[f32]) -> Vec<Vec<f32>> {
    let mut vad = AdaptiveVad::new();
    let mut chunks = Vec::new();
    let mut pending = Vec::new();
    let mut silence_run = 0;
    let mut last_tick_len = 0;
    // Murmure's headless API: ticks of 33 ms, arm at 15 s, cut after 500 ms silence.
    // Alfred's 30 s bound makes the upstream 60 s forced/overlap branch unreachable.
    for window in samples.chunks(16000 * 33 / 1000) {
        pending.extend_from_slice(window);
        let rms = (window.iter().map(|v| v * v).sum::<f32>() / window.len() as f32).sqrt();
        let activity = vad.update(rms);
        if pending.len() < 15 * 16000 {
            last_tick_len = pending.len();
            continue;
        }
        let delta = pending.len().saturating_sub(last_tick_len);
        last_tick_len = pending.len();
        match activity {
            VoiceActivity::Silent => {
                silence_run += delta;
                if silence_run >= 8000 {
                    chunks.push(std::mem::take(&mut pending));
                    vad.reset_speech_state();
                    silence_run = 0;
                    last_tick_len = 0;
                }
            }
            VoiceActivity::Active => silence_run = 0,
            VoiceActivity::NotStarted => {}
        }
    }
    if !pending.is_empty() {
        chunks.push(pending);
    }
    chunks
}

pub fn transcribe(
    engine: &mut ParakeetEngine,
    samples: &[f32],
    dictionary: &[String],
    formatting: &FormattingSettings,
) -> Result<(String, usize), Box<dyn std::error::Error>> {
    sync_boost_words(engine, dictionary);
    let chunks = split_chunks(samples);
    let count = chunks.len();
    let mut texts = Vec::new();
    for chunk in chunks {
        let mut padded = vec![0.0; 4000]; // 250 ms on both sides, as in Murmure.
        padded.extend(chunk);
        padded.resize(padded.len() + 4000, 0.0);
        let result = engine.transcribe_samples(padded, None)?;
        let corrected = correct_transcription(result.text.trim(), dictionary, &result.word_confidences);
        if !corrected.trim().is_empty() {
            texts.push(corrected.trim().to_string());
        }
    }
    let joined = texts.join(" ");
    if joined.trim().is_empty() {
        return Ok((String::new(), count));
    }
    let cleaned = strip_fillers_and_repeats(&joined);
    Ok((apply_formatting(cleaned, formatting).trim().to_string(), count))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn short_input_keeps_every_sample() {
        let input = vec![0.1; 16000 * 3];
        assert_eq!(split_chunks(&input), vec![input]);
    }
    #[test]
    fn silence_after_fifteen_seconds_cuts_without_losing_samples() {
        let mut input = vec![0.1; 16000 * 16];
        input.extend(vec![0.0; 16000 * 2]);
        input.extend(vec![0.1; 16000 * 5]);
        let chunks = split_chunks(&input);
        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks.concat(), input);
    }
    #[test]
    fn same_cleanup_keeps_double_words_but_removes_fillers_and_excess_repeats() {
        assert_eq!(strip_fillers_and_repeats("je euh veux veux veux du pain"), "je veux veux du pain");
    }
}
