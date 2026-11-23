// Adapté de Murmure 1.11.3 audio/clean_recording.rs (AGPL-3.0-or-later).
static FILLER_WORDS: &[&str] = &[
    "euh", "hmm", "hm", "mmm", "uh", "um", "uhm", "umm", "uhh", "uhhh", "ah", "mm", "mh", "eh",
    "ehh", "ha", "mm-hmm",
];

fn is_filler(word: &str) -> bool {
    let normalized = word.trim_matches(|c: char| !c.is_alphanumeric());
    if normalized.is_empty() {
        return false;
    }
    let lower = normalized.to_lowercase();
    FILLER_WORDS.contains(&lower.as_str())
}

pub(super) fn strip_fillers_and_repeats(text: &str) -> String {
    let words: Vec<&str> = text.split_whitespace().filter(|w| !is_filler(w)).collect();
    if words.is_empty() {
        return String::new();
    }

    let mut result: Vec<&str> = Vec::with_capacity(words.len());
    let mut i = 0;

    while i < words.len() {
        let current_lower = words[i].to_lowercase();
        let mut count = 1;

        while i + count < words.len() && words[i + count].to_lowercase() == current_lower {
            count += 1;
        }

        if count >= 3 {
            result.push(words[i]);
            result.push(words[i + 1]);
        } else {
            for j in 0..count {
                result.push(words[i + j]);
            }
        }

        i += count;
    }

    result.join(" ")
}

