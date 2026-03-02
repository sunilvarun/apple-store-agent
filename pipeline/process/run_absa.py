"""
Aspect-Based Sentiment Analysis (ABSA) pipeline for iPhone 17 reviews.

Input:  pipeline/data/processed/reviews_normalized.jsonl
Output: pipeline/data/derived/review_aspect_scores.json

Method:
    1. Aspect detection: sentence-level cosine similarity against seed phrase embeddings
    2. Sentiment scoring: VADER compound score per sentence
    3. Aggregation: mean sentiment per (model, aspect) with confidence weighting

Usage:
    python pipeline/process/run_absa.py
"""

import html
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

PROCESSED_PATH  = Path(__file__).parents[1] / "data" / "processed" / "reviews_normalized.jsonl"
OUTPUT_PATH     = Path(__file__).parents[1] / "data" / "derived" / "review_aspect_scores.json"
QUOTES_PATH     = Path(__file__).parents[1] / "data" / "derived" / "review_quotes.json"

QUOTE_MIN_WORDS   = 12    # too short → not informative
QUOTE_MAX_WORDS   = 70    # too long → hard to read
QUOTE_MIN_SENTIMENT = 0.25  # |vader compound| must be this strong to qualify as a quote

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
ASPECT_THRESHOLD = 0.35   # cosine similarity minimum to assign an aspect
CONFIDENCE_VOLUME = 500   # reviews needed for confidence = 1.0
EXCLUDED_SLUG = "iphone-17-unknown"

# Aspect taxonomy with seed phrases
ASPECTS: dict[str, list[str]] = {
    "camera": [
        "photo quality", "camera", "zoom", "night mode", "portrait mode",
        "video quality", "ProRAW", "cinematic mode", "main camera",
        "ultrawide", "telephoto", "low light", "lens",
    ],
    "battery": [
        "battery life", "battery drain", "charging", "all day battery",
        "runs out of power", "battery percentage", "fast charging",
        "MagSafe", "battery health", "power",
    ],
    "performance": [
        "speed", "performance", "fast", "lag", "smooth", "A18",
        "chip", "processor", "gaming performance", "multitasking",
        "responsive", "snappy", "slow",
    ],
    "heating": [
        "gets hot", "overheating", "warm", "heat", "thermal throttling",
        "temperature", "heats up", "burning hot",
    ],
    "display": [
        "screen", "display", "ProMotion", "brightness", "OLED",
        "refresh rate", "color accuracy", "always on display",
        "resolution", "pixel", "Dynamic Island",
    ],
    "durability": [
        "drop test", "scratch", "durable", "build quality", "titanium",
        "aluminum", "glass", "cracked", "water resistant", "IP68",
        "rugged", "sturdy",
    ],
    "weight": [
        "weight", "heavy", "light", "thin", "slim", "comfortable to hold",
        "bulky", "pocketable", "size", "one-handed",
    ],
    "value": [
        "price", "expensive", "worth it", "value for money", "overpriced",
        "affordable", "cost", "upgrade", "not worth", "good deal",
    ],
}


def compute_aspect_centroids(model: SentenceTransformer) -> dict[str, np.ndarray]:
    """Embed all seed phrases and compute mean centroid per aspect."""
    print("Computing aspect centroids...")
    centroids = {}
    for aspect, seeds in ASPECTS.items():
        embeddings = model.encode(seeds, convert_to_numpy=True, show_progress_bar=False)
        centroids[aspect] = embeddings.mean(axis=0)
        # L2-normalize for cosine similarity via dot product
        centroids[aspect] /= np.linalg.norm(centroids[aspect])
    return centroids


def detect_aspects(
    sentence_embedding: np.ndarray,
    centroids: dict[str, np.ndarray],
    threshold: float = ASPECT_THRESHOLD,
) -> list[str]:
    """Return aspects whose centroid is within threshold similarity of the sentence."""
    detected = []
    for aspect, centroid in centroids.items():
        similarity = float(np.dot(sentence_embedding, centroid))
        if similarity >= threshold:
            detected.append(aspect)
    return detected


def split_sentences(text: str) -> list[str]:
    """Naive sentence splitter. Good enough for social media text."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.split()) >= 4]


def rescale_vader(compound: float) -> float:
    """Rescale VADER compound [-1, 1] to [0, 1]."""
    return (compound + 1.0) / 2.0


def run():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not PROCESSED_PATH.exists():
        print(f"[ERROR] Input file not found: {PROCESSED_PATH}")
        print("Run normalize_reviews.py first.")
        return

    print(f"Loading model: {EMBEDDING_MODEL}")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    vader = SentimentIntensityAnalyzer()

    centroids = compute_aspect_centroids(embedder)

    # Load normalized reviews
    print(f"Loading reviews from {PROCESSED_PATH}...")
    reviews = []
    with open(PROCESSED_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))

    # Filter out unknown-model reviews
    reviews = [r for r in reviews if r["model_slug"] != EXCLUDED_SLUG]
    print(f"Reviews to process: {len(reviews):,} (excluded {EXCLUDED_SLUG})")

    # Per (model_slug, aspect) → list of VADER scores
    scores_by_model_aspect: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    # Per (model_slug, aspect) → list of (sentence, vader_compound) for quote extraction
    quotes_by_model_aspect: dict[str, dict[str, list[tuple]]] = defaultdict(lambda: defaultdict(list))

    print("Running ABSA...")
    for review in tqdm(reviews, desc="Processing reviews"):
        model_slug = review["model_slug"]
        text = review["text"]

        sentences = split_sentences(text)
        if not sentences:
            continue

        # Embed all sentences in one batch
        sentence_embeddings = embedder.encode(
            sentences,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        for sentence, sent_emb in zip(sentences, sentence_embeddings):
            aspects = detect_aspects(sent_emb, centroids)
            if not aspects:
                continue

            vader_score = vader.polarity_scores(sentence)["compound"]

            for aspect in aspects:
                scores_by_model_aspect[model_slug][aspect].append(vader_score)
                # Collect quotes: strong sentiment, right length, no excessive emoji/caps
                words = sentence.split()
                alpha = [c for c in sentence if c.isalpha()]
                caps_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha) if alpha else 0
                if (QUOTE_MIN_WORDS <= len(words) <= QUOTE_MAX_WORDS
                        and abs(vader_score) >= QUOTE_MIN_SENTIMENT
                        and caps_ratio < 0.4):
                    quotes_by_model_aspect[model_slug][aspect].append((sentence, vader_score))

    # Aggregate
    print("Aggregating scores and extracting quotes...")
    result: dict[str, dict[str, dict]] = {}
    quotes_result: dict[str, dict[str, dict]] = {}

    for model_slug, aspect_scores in scores_by_model_aspect.items():
        result[model_slug] = {}
        quotes_result[model_slug] = {}
        for aspect, scores in aspect_scores.items():
            volume = len(scores)
            mean_score = float(np.mean(scores))
            rescaled = rescale_vader(mean_score)
            confidence = min(1.0, volume / CONFIDENCE_VOLUME)

            positive_count = sum(1 for s in scores if s > 0.05)
            negative_count = sum(1 for s in scores if s < -0.05)
            sentiment_total = positive_count + negative_count
            positive_pct = round(positive_count / sentiment_total * 100) if sentiment_total else 50

            result[model_slug][aspect] = {
                "score": round(rescaled, 4),
                "raw_vader_mean": round(mean_score, 4),
                "volume": volume,
                "confidence": round(confidence, 4),
                "positive_pct": positive_pct,
            }

            # Select best quotes: top 2 positive + 1 negative
            candidates = quotes_by_model_aspect[model_slug][aspect]
            pos_quotes = sorted([q for q in candidates if q[1] > 0.05], key=lambda x: -x[1])
            neg_quotes = sorted([q for q in candidates if q[1] < -0.05], key=lambda x: x[1])
            selected = [(t, "positive") for t, _ in pos_quotes[:2]] + \
                       [(t, "negative") for t, _ in neg_quotes[:1]]

            quotes_result[model_slug][aspect] = {
                "positive_pct": positive_pct,
                "total_mentions": volume,
                "quotes": [{"text": html.unescape(t), "sentiment": s} for t, s in selected],
            }

    # Save scores
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Save quotes
    with open(QUOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(quotes_result, f, indent=2)
    print(f"Quotes: {QUOTES_PATH}")

    # Print summary
    print(f"\n--- ABSA complete ---")
    print(f"Output: {OUTPUT_PATH}\n")
    for model_slug, aspects in sorted(result.items()):
        print(f"{model_slug}:")
        for aspect, data in sorted(aspects.items()):
            bar = "█" * int(data["score"] * 10) + "░" * (10 - int(data["score"] * 10))
            conf_flag = f" (low confidence)" if data["confidence"] < 0.5 else ""
            print(f"  {aspect:<12} [{bar}] {data['score']:.2f}  vol={data['volume']:,}  conf={data['confidence']:.2f}{conf_flag}")
        print()


if __name__ == "__main__":
    run()
