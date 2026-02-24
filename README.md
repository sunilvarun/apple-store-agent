# Apple Store Agentic Commerce

An AI-powered iPhone recommendation engine that combines real review sentiment analysis with an agentic Claude-powered shopping assistant.

---

## Project Structure

```
apple-store-agent/
├── pipeline/          ← Step 1: one-time review data collection + ABSA
├── backend/           ← Step 2: FastAPI + Claude agent (coming soon)
└── frontend/          ← Step 3: React Apple Store UI (coming soon)
```

---

## Step 1: Review Data Pipeline

This runs **once** to generate `pipeline/data/derived/review_aspect_scores.json`, which the recommendation engine uses to score phones on camera, battery, performance, etc.

### 1. Setup

```bash
cd ~/Documents/apple-store-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Get API credentials

#### YouTube Data API v3
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Library** → search "YouTube Data API v3" → Enable
4. Go to **APIs & Services → Credentials** → **Create Credentials → API Key**
5. Copy the key into `.env`:
   ```
   YOUTUBE_API_KEY=AIza...
   ```
6. **Quota:** 10,000 units/day (free). This pipeline uses ~300 units total.

#### Reddit API (PRAW)
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll down → click **"create another app"**
3. Select **"script"**, give it any name (e.g. `iphone17-research`)
4. Set redirect URI to `http://localhost:8080`
5. Copy the values into `.env`:
   ```
   REDDIT_CLIENT_ID=abc123        ← shown under app name
   REDDIT_CLIENT_SECRET=xyz789    ← shown as "secret"
   REDDIT_USER_AGENT=iphone17-research/1.0 by /u/your_username
   ```

### 3. Validate the ABSA pipeline (no API keys needed)

Run the synthetic test first to confirm the aspect detection and sentiment scoring work correctly before collecting real data:

```bash
python pipeline/tests/test_absa_synthetic.py
```

Expected output:
```
Aspect detection accuracy:  17/20 = 85%
Sentiment direction accuracy: 16/20 = 80%
RESULT: PASS — Pipeline is ready for real data collection.
```

If it fails, check the failure details and adjust `ASPECT_THRESHOLD` in `run_absa.py`.

### 4. Collect review data

```bash
# YouTube comments (~10 min, ~300 API quota units)
python pipeline/collect/youtube_collector.py

# Reddit threads + comments (~5 min)
python pipeline/collect/reddit_collector.py
```

Outputs:
- `pipeline/data/raw/youtube_comments_iphone17.jsonl`
- `pipeline/data/raw/reddit_iphone17.jsonl`

### 5. Process and score

```bash
# Normalize + deduplicate
python pipeline/process/normalize_reviews.py

# Run ABSA (~15-30 min depending on volume)
python pipeline/process/run_absa.py
```

Final output: `pipeline/data/derived/review_aspect_scores.json`

Example:
```json
{
  "iphone-17-pro-max": {
    "camera":      {"score": 0.84, "volume": 1420, "confidence": 1.0},
    "battery":     {"score": 0.71, "volume":  980, "confidence": 1.0},
    "performance": {"score": 0.79, "volume": 1100, "confidence": 1.0},
    "heating":     {"score": 0.55, "volume":  240, "confidence": 0.48}
  }
}
```

---

## Success Criteria

| Check | Target |
|-------|--------|
| Synthetic test aspect accuracy | ≥ 80% |
| Synthetic test sentiment accuracy | ≥ 75% |
| Models with confidence > 0.5 on ≥ 4 aspects | ≥ 3 models |
| Normalized reviews per major model | ≥ 1,000 |

---

## What's Next

Once `review_aspect_scores.json` is generated and looks good:

- **backend/**: FastAPI server + Claude claude-sonnet-4-6 agent with tool_use for recommendations
- **frontend/**: React + Vite Apple Store UI with chat panel and comparison table
