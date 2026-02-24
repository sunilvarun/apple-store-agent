"""
Normalize and deduplicate raw reviews from YouTube + Reddit.

Steps:
    1. Load raw JSONL files from both sources
    2. Drop short / spammy comments
    3. Deduplicate by exact text match (cosine-sim dedup is too slow for 50k+ reviews)
    4. Assign model_slug by keyword matching
    5. Write pipeline/data/processed/reviews_normalized.jsonl

Usage:
    python pipeline/process/normalize_reviews.py
"""

import json
import re
from pathlib import Path

from tqdm import tqdm

RAW_DIR = Path(__file__).parents[1] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[1] / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "reviews_normalized.jsonl"

MIN_WORD_COUNT = 10
MAX_CAPS_RATIO = 0.6  # drop if > 60% uppercase chars (spam indicator)

# Model slug assignment rules — ordered most specific → least specific
MODEL_RULES = [
    # iPhone 17 Pro Max
    (re.compile(r"\b17\s*pro\s*max\b", re.IGNORECASE), "iphone-17-pro-max"),
    (re.compile(r"\bpro\s*max\b", re.IGNORECASE),       "iphone-17-pro-max"),
    # iPhone 17 Pro
    (re.compile(r"\b17\s*pro\b(?!\s*max)", re.IGNORECASE), "iphone-17-pro"),
    # iPhone 17 Air
    (re.compile(r"\b17\s*air\b", re.IGNORECASE),        "iphone-17-air"),
    (re.compile(r"\biphone\s*air\b", re.IGNORECASE),    "iphone-17-air"),
    # iPhone 17 base
    (re.compile(r"\biphone\s*17\b(?!\s*(pro|air))", re.IGNORECASE), "iphone-17"),
    (re.compile(r"\b(?<!\d)17\b(?!\s*(pro|air|inch|fps|mp|mm|gb|tb|\%))", re.IGNORECASE), "iphone-17"),
]
UNKNOWN_SLUG = "iphone-17-unknown"


def assign_model_slug(text: str) -> str:
    for pattern, slug in MODEL_RULES:
        if pattern.search(text):
            return slug
    return UNKNOWN_SLUG


def is_spam(text: str) -> bool:
    """Return True if the text looks like spam or is too short."""
    words = text.split()
    if len(words) < MIN_WORD_COUNT:
        return True

    # Mostly uppercase
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > MAX_CAPS_RATIO:
        return True

    # Repeated characters (e.g. "aaaaaaaaaa" or "!!!!!!!")
    if re.search(r"(.)\1{6,}", text):
        return True

    return False


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [SKIP] File not found: {path}")
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def run():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading raw data...")
    youtube_records = load_jsonl(RAW_DIR / "youtube_comments_iphone17.jsonl")
    reddit_records = load_jsonl(RAW_DIR / "reddit_iphone17.jsonl")

    all_records = youtube_records + reddit_records
    print(f"  YouTube: {len(youtube_records):,} comments")
    print(f"  Reddit:  {len(reddit_records):,} comments")
    print(f"  Total:   {len(all_records):,} comments")

    # Stats
    dropped_short = 0
    dropped_spam = 0
    dropped_duplicate = 0
    dropped_unknown_model = 0
    written = 0
    per_model: dict[str, int] = {}

    seen_texts: set[str] = set()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        for record in tqdm(all_records, desc="Normalizing"):
            text = record.get("comment_text", "").strip()

            # Drop short
            if len(text.split()) < MIN_WORD_COUNT:
                dropped_short += 1
                continue

            # Drop spam
            if is_spam(text):
                dropped_spam += 1
                continue

            # Exact-text deduplicate
            text_key = text.lower()
            if text_key in seen_texts:
                dropped_duplicate += 1
                continue
            seen_texts.add(text_key)

            # Assign model: first try comment text, fall back to video/thread title
            model_slug = assign_model_slug(text)
            if model_slug == UNKNOWN_SLUG:
                title = record.get("video_title") or record.get("thread_title") or ""
                model_slug = assign_model_slug(title)

            normalized = {
                "model_slug": model_slug,
                "text": text,
                "source": record.get("source", "unknown"),
                "engagement_score": record.get("like_count") or record.get("score") or 0,
            }

            out_file.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            per_model[model_slug] = per_model.get(model_slug, 0) + 1
            written += 1

    print(f"\n--- Normalization complete ---")
    print(f"Written: {written:,}")
    print(f"Dropped (too short):   {dropped_short:,}")
    print(f"Dropped (spam):        {dropped_spam:,}")
    print(f"Dropped (duplicate):   {dropped_duplicate:,}")
    print(f"\nPer-model breakdown:")
    for slug, count in sorted(per_model.items(), key=lambda x: -x[1]):
        flag = " ← excluded from scoring" if slug == UNKNOWN_SLUG else ""
        print(f"  {slug}: {count:,}{flag}")
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
