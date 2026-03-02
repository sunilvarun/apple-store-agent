"""
Fetch YouTube transcripts for all videos already in our comments dataset.

No API key needed — youtube-transcript-api pulls captions directly from YouTube.
Reuses the 54 video IDs we already collected so we don't repeat the search.

Output: pipeline/data/raw/youtube_transcripts_iphone17.jsonl
Fields:  source, video_id, video_title, comment_text (sentences), start_time

Usage:
    cd ~/Documents/apple-store-agent
    source venv/bin/activate
    python pipeline/collect/transcript_collector.py
"""

import json
import re
import time
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

_ytt = YouTubeTranscriptApi()

RAW_DIR = Path(__file__).parents[1] / "data" / "raw"
COMMENTS_FILE = RAW_DIR / "youtube_comments_iphone17.jsonl"
OUTPUT_FILE   = RAW_DIR / "youtube_transcripts_iphone17.jsonl"

# Group raw transcript segments into chunks of ~this many words before outputting
CHUNK_WORDS = 35
MIN_CHUNK_WORDS = 8   # discard chunks shorter than this

# Patterns to strip from auto-generated captions
NOISE_PATTERNS = [
    re.compile(r"\[.*?\]"),          # [Music], [Applause], [Laughter], etc.
    re.compile(r"\(.*?\)"),          # (upbeat music), (laughs)
    re.compile(r"^um+\s*$", re.I),   # filler words as standalone chunks
    re.compile(r"^uh+\s*$", re.I),
]


def clean_segment(text: str) -> str:
    for pat in NOISE_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


def chunk_transcript(segments: list[dict]) -> list[dict]:
    """
    Group raw timestamped segments (each ~3-5 words) into
    meaningful chunks of ~CHUNK_WORDS words each.
    Returns list of {text, start_time}.
    """
    chunks = []
    current_words = []
    current_start = None

    for seg in segments:
        text = clean_segment(seg.text if hasattr(seg, "text") else seg.get("text", ""))
        if not text:
            continue

        words = text.split()
        if not words:
            continue

        if current_start is None:
            current_start = seg.start if hasattr(seg, "start") else seg.get("start", 0)

        current_words.extend(words)

        # Flush when we hit the target chunk size, or on sentence-ending punctuation
        if len(current_words) >= CHUNK_WORDS or (current_words and current_words[-1][-1:] in ".!?"):
            chunk_text = " ".join(current_words)
            if len(current_words) >= MIN_CHUNK_WORDS:
                chunks.append({"text": chunk_text, "start_time": round(current_start, 1)})
            current_words = []
            current_start = None

    # Flush remainder
    if len(current_words) >= MIN_CHUNK_WORDS:
        chunks.append({"text": " ".join(current_words), "start_time": round(current_start or 0, 1)})

    return chunks


def load_video_ids() -> list[tuple[str, str]]:
    """Return unique (video_id, video_title) pairs from the comments file."""
    seen = set()
    videos = []
    with open(COMMENTS_FILE, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            vid = rec["video_id"]
            if vid not in seen:
                seen.add(vid)
                videos.append((vid, rec["video_title"]))
    return videos


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    videos = load_video_ids()
    print(f"Fetching transcripts for {len(videos)} videos...\n")

    total_chunks = 0
    skipped = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i, (video_id, video_title) in enumerate(videos, 1):
            prefix = f"[{i:02d}/{len(videos)}]"
            try:
                # Prefer English; fall back to auto-generated
                transcript = _ytt.fetch(video_id, languages=["en", "en-US", "en-GB"])
                chunks = chunk_transcript(transcript)

                for chunk in chunks:
                    record = {
                        "source":       "youtube_transcript",
                        "video_id":     video_id,
                        "video_title":  video_title,
                        "comment_text": chunk["text"],   # same key as comments for normalize step
                        "start_time":   chunk["start_time"],
                        "like_count":   0,               # transcripts have no likes
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")

                total_chunks += len(chunks)
                print(f"{prefix} {video_title[:55]:<55} → {len(chunks)} chunks")

            except (NoTranscriptFound, TranscriptsDisabled):
                print(f"{prefix} {video_title[:55]:<55} → [NO TRANSCRIPT]")
                skipped += 1

            except Exception as e:
                print(f"{prefix} {video_title[:55]:<55} → [ERROR: {e}]")
                skipped += 1

            time.sleep(0.3)   # be polite

    print(f"\n--- Done ---")
    print(f"Transcript chunks written: {total_chunks:,}")
    print(f"Videos skipped (no captions): {skipped}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
