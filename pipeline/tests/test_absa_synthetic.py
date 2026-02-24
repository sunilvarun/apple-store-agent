"""
Synthetic ABSA validation test.

Run this BEFORE collecting real data to confirm:
- Aspect detection fires correctly on obvious mentions
- VADER sentiment direction is correct (positive/negative)
- The pipeline doesn't crash

Success criteria:
    - Aspect detection accuracy >= 80%
    - Sentiment direction accuracy >= 75%

Usage:
    python pipeline/tests/test_absa_synthetic.py
"""

import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Add pipeline root to path
sys.path.insert(0, str(Path(__file__).parents[2]))
from pipeline.process.run_absa import ASPECTS, ASPECT_THRESHOLD, detect_aspects, rescale_vader

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 20 hand-written test cases with known expected aspect + sentiment direction
SYNTHETIC_TESTS = [
    # Camera — positive
    {"text": "The camera on this phone is absolutely incredible, best photos I have ever taken",
     "expected_aspect": "camera", "expected_sentiment": "positive"},

    # Camera — negative
    {"text": "Disappointed with the camera, photos are blurry in low light and the zoom is terrible",
     "expected_aspect": "camera", "expected_sentiment": "negative"},

    # Battery — positive
    {"text": "Battery lasts all day easily, I can go from morning to night without charging",
     "expected_aspect": "battery", "expected_sentiment": "positive"},

    # Battery — negative
    {"text": "Battery drains so fast, I need to charge it twice a day, totally unacceptable",
     "expected_aspect": "battery", "expected_sentiment": "negative"},

    # Performance — positive
    {"text": "This phone is blazing fast, apps open instantly and multitasking is completely smooth",
     "expected_aspect": "performance", "expected_sentiment": "positive"},

    # Performance — negative
    {"text": "The phone lags constantly, scrolling is not smooth and apps take forever to open",
     "expected_aspect": "performance", "expected_sentiment": "negative"},

    # Heating — negative
    {"text": "The phone gets incredibly hot during gaming, it burns your hand after 20 minutes",
     "expected_aspect": "heating", "expected_sentiment": "negative"},

    # Heating — positive/neutral
    {"text": "Surprisingly cool even during heavy use, no overheating issues at all",
     "expected_aspect": "heating", "expected_sentiment": "positive"},

    # Display — positive
    {"text": "The screen is gorgeous, super bright outdoors and the OLED colors are stunning",
     "expected_aspect": "display", "expected_sentiment": "positive"},

    # Display — negative
    {"text": "The display is dim outdoors, hard to see in sunlight and colors look washed out",
     "expected_aspect": "display", "expected_sentiment": "negative"},

    # Durability — positive
    {"text": "Dropped it twice already on concrete with no case and not a single scratch, very durable",
     "expected_aspect": "durability", "expected_sentiment": "positive"},

    # Durability — negative
    {"text": "The glass cracked from a minor drop, build quality feels cheap for the price",
     "expected_aspect": "durability", "expected_sentiment": "negative"},

    # Weight — positive
    {"text": "Very lightweight and comfortable to hold one-handed for long periods",
     "expected_aspect": "weight", "expected_sentiment": "positive"},

    # Weight — negative
    {"text": "Way too heavy and bulky, my wrist hurts after holding it for just a few minutes",
     "expected_aspect": "weight", "expected_sentiment": "negative"},

    # Value — positive
    {"text": "Totally worth the price, best value smartphone I have ever purchased",
     "expected_aspect": "value", "expected_sentiment": "positive"},

    # Value — negative
    {"text": "Way too expensive for what you get, completely overpriced compared to the competition",
     "expected_aspect": "value", "expected_sentiment": "negative"},

    # Camera — positive (video specific)
    {"text": "The cinematic video mode is mind-blowing, my YouTube videos look professional now",
     "expected_aspect": "camera", "expected_sentiment": "positive"},

    # Battery — positive (charging)
    {"text": "Fast charging is great, goes from 0 to 80 percent in under 30 minutes",
     "expected_aspect": "battery", "expected_sentiment": "positive"},

    # Performance — positive (gaming)
    {"text": "Games run at 120fps perfectly smooth, zero lag even in the most demanding titles",
     "expected_aspect": "performance", "expected_sentiment": "positive"},

    # Value — negative (upgrade)
    {"text": "Not worth upgrading from last year, barely any differences to justify the cost",
     "expected_aspect": "value", "expected_sentiment": "negative"},
]


def compute_centroids(model: SentenceTransformer) -> dict[str, np.ndarray]:
    centroids = {}
    for aspect, seeds in ASPECTS.items():
        embeddings = model.encode(seeds, convert_to_numpy=True, show_progress_bar=False)
        centroid = embeddings.mean(axis=0)
        centroid /= np.linalg.norm(centroid)
        centroids[aspect] = centroid
    return centroids


def run_tests():
    print("Loading models...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    vader = SentimentIntensityAnalyzer()

    print("Computing aspect centroids...")
    centroids = compute_centroids(embedder)

    print(f"\nRunning {len(SYNTHETIC_TESTS)} synthetic tests...\n")

    aspect_correct = 0
    sentiment_correct = 0
    failures = []

    for i, test in enumerate(SYNTHETIC_TESTS):
        text = test["text"]
        expected_aspect = test["expected_aspect"]
        expected_sentiment = test["expected_sentiment"]

        # Aspect detection
        embedding = embedder.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
        detected_aspects = detect_aspects(embedding, centroids, threshold=ASPECT_THRESHOLD)
        aspect_hit = expected_aspect in detected_aspects

        # Sentiment
        compound = vader.polarity_scores(text)["compound"]
        rescaled = rescale_vader(compound)
        predicted_sentiment = "positive" if compound >= 0.05 else ("negative" if compound <= -0.05 else "neutral")
        sentiment_hit = predicted_sentiment == expected_sentiment

        if aspect_hit:
            aspect_correct += 1
        if sentiment_hit:
            sentiment_correct += 1

        status = "PASS" if (aspect_hit and sentiment_hit) else "FAIL"
        if status == "FAIL":
            failures.append({
                "test": i + 1,
                "text": text[:80] + "...",
                "expected_aspect": expected_aspect,
                "detected_aspects": detected_aspects,
                "aspect_hit": aspect_hit,
                "expected_sentiment": expected_sentiment,
                "predicted_sentiment": predicted_sentiment,
                "vader_compound": round(compound, 3),
            })

        print(f"  [{status}] Test {i+1:2d}: aspect={aspect_hit} ({expected_aspect} in {detected_aspects}), "
              f"sentiment={sentiment_hit} ({expected_sentiment}/{predicted_sentiment}, vader={compound:.3f})")

    n = len(SYNTHETIC_TESTS)
    aspect_acc = aspect_correct / n
    sentiment_acc = sentiment_correct / n

    print(f"\n{'='*60}")
    print(f"Aspect detection accuracy:  {aspect_correct}/{n} = {aspect_acc:.0%}")
    print(f"Sentiment direction accuracy: {sentiment_correct}/{n} = {sentiment_acc:.0%}")

    if failures:
        print(f"\nFailures ({len(failures)}):")
        for f in failures:
            print(f"  Test {f['test']}: '{f['text']}'")
            if not f["aspect_hit"]:
                print(f"    Aspect: expected '{f['expected_aspect']}', got {f['detected_aspects']}")
            if f["expected_sentiment"] != f["predicted_sentiment"]:
                print(f"    Sentiment: expected '{f['expected_sentiment']}', got '{f['predicted_sentiment']}' (VADER={f['vader_compound']})")

    print(f"\n{'='*60}")
    passed = aspect_acc >= 0.80 and sentiment_acc >= 0.75
    if passed:
        print("RESULT: PASS — Pipeline is ready for real data collection.")
    else:
        print("RESULT: FAIL — Review aspect seeds or threshold before collecting real data.")
        if aspect_acc < 0.80:
            print(f"  Aspect accuracy {aspect_acc:.0%} < 80% target. Consider adding seed phrases or lowering threshold.")
        if sentiment_acc < 0.75:
            print(f"  Sentiment accuracy {sentiment_acc:.0%} < 75% target. Check VADER on these text types.")

    return passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
