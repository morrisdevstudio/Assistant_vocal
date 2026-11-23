// SPDX-License-Identifier: AGPL-3.0-or-later
// Alfred headless adapter; upstream notices and exact revision: ../UPSTREAM.json.
#![allow(dead_code)]
mod clean;
mod dictionary;
mod engine;
mod formatting_rules;
mod pipeline;
mod vad;

use base64::{engine::general_purpose::STANDARD, Engine};
use engine::ParakeetEngine;
use formatting_rules::types::FormattingSettings;
use serde::Deserialize;
use serde_json::{json, Value};
use std::io::{Read, Write};
use std::path::PathBuf;
use std::time::Instant;

const MAX_FRAME: usize = 1_400_000;

#[derive(Deserialize)]
struct Config {
    #[serde(default)]
    dictionary: Vec<String>,
    formatting: FormattingSettings,
}

#[derive(Deserialize)]
struct Request {
    pcm_base64: String,
}

fn read_frame(input: &mut impl Read) -> std::io::Result<Option<Vec<u8>>> {
    let mut header = [0; 4];
    // EOF between requests is a normal, clean shutdown.
    if input.read(&mut header[..1])? == 0 {
        return Ok(None);
    }
    input.read_exact(&mut header[1..])?;
    let length = u32::from_le_bytes(header) as usize;
    if length == 0 || length > MAX_FRAME {
        return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "invalid frame"));
    }
    let mut body = vec![0; length];
    input.read_exact(&mut body)?;
    Ok(Some(body))
}

fn send(output: &mut impl Write, value: Value) -> std::io::Result<()> {
    let bytes = serde_json::to_vec(&value)?;
    output.write_all(&(bytes.len() as u32).to_le_bytes())?;
    output.write_all(&bytes)?;
    output.flush()
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 3 { return Err("expected models, tokenizer, config".into()); }
    let models = PathBuf::from(&args[0]);
    let tokenizer = PathBuf::from(&args[1]);
    let config: Config = serde_json::from_slice(&std::fs::read(&args[2])?)?;
    if config.dictionary.len() > 10000 { return Err("dictionary limit".into()); }
    let mut engine = ParakeetEngine::load_int8(&models, Some(tokenizer))?;
    let mut output = std::io::stdout().lock();
    let mut input = std::io::stdin().lock();
    send(&mut output, json!({"ready": true, "upstream": "murmure-1.11.3"}))?;
    while let Some(frame) = read_frame(&mut input)? {
        let started = Instant::now();
        let result = (|| -> Result<Value, Box<dyn std::error::Error>> {
            let request: Request = serde_json::from_slice(&frame)?;
            let bytes = STANDARD.decode(request.pcm_base64)?;
            if bytes.is_empty() || bytes.len() % 2 != 0 || bytes.len() > 30 * 16000 * 2 {
                return Err("invalid pcm".into());
            }
            let samples: Vec<f32> = bytes.chunks_exact(2)
                .map(|p| i16::from_le_bytes([p[0], p[1]]) as f32 / 32768.0).collect();
            let (text, chunks) = pipeline::transcribe(&mut engine, &samples, &config.dictionary, &config.formatting)?;
            Ok(json!({"text": text, "chunks": chunks, "engine_ms": started.elapsed().as_millis()}))
        })();
        // No input text, audio, private dictionary or paths in errors/logs.
        send(&mut output, result.unwrap_or_else(|_| json!({"error": "transcription_failed"})))?;
    }
    Ok(())
}

fn main() {
    if run().is_err() {
        let _ = send(&mut std::io::stdout(), json!({"error": "worker_unavailable"}));
        std::process::exit(1);
    }
}
