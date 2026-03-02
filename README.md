# Apple Store Agentic Commerce

An AI-powered iPhone recommendation engine combining real review sentiment analysis with an agentic Claude-powered shopping assistant.

**Live stack:** React frontend · FastAPI backend · Claude claude-sonnet-4-6 agent · 10,621 real reviews (YouTube comments, Reddit posts, and video transcripts)

---

## Project Structure

```
apple-store-agent/
├── pipeline/          ← one-time review data collection + ABSA
│   ├── collect/       ← YouTube comments, Reddit posts, YouTube transcripts
│   ├── process/       ← normalize, deduplicate, run ABSA
│   ├── data/derived/  ← review_aspect_scores.json + review_quotes.json (committed)
│   └── tests/         ← synthetic ABSA validation
├── backend/           ← FastAPI + Claude agent (complete)
│   ├── agent/         ← claude_agent.py, tool_definitions.py, tool_handlers.py
│   ├── catalog/       ← catalog_store.py, iphone_catalog.json
│   ├── api/           ← routes for /chat, /catalog, /admin
│   └── models/        ← Pydantic models
└── frontend/          ← React + Vite Apple Store UI (complete)
    └── src/
        ├── components/ ← NavBar, ProductGrid, ChatPanel, ComparisonTable, CartDrawer
        └── hooks/      ← useChat (SSE), useCatalog, useComparison
```

---

## Review Data Pipeline

This runs **once** to generate `pipeline/data/derived/review_aspect_scores.json` and `review_quotes.json`, which the recommendation engine uses to score phones and surface real reviewer quotes.

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
2. Create a new project → **APIs & Services → Library** → enable "YouTube Data API v3"
3. **Credentials → Create Credentials → API Key**
4. Add to `.env`: `YOUTUBE_API_KEY=AIza...`
5. **Quota:** 10,000 units/day (free). This pipeline uses ~300 units total.

#### Reddit API (PRAW)
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → **"create another app"** → script type
2. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=abc123
   REDDIT_CLIENT_SECRET=xyz789
   REDDIT_USER_AGENT=iphone17-research/1.0 by /u/your_username
   ```

### 3. Validate the ABSA pipeline (no API keys needed)

```bash
python pipeline/tests/test_absa_synthetic.py
```

Expected output:
```
Aspect detection accuracy:  17/20 = 85%
Sentiment direction accuracy: 16/20 = 80%
RESULT: PASS — Pipeline is ready for real data collection.
```

### 4. Collect review data

```bash
# YouTube comments (~10 min, ~300 API quota units)
python pipeline/collect/youtube_collector.py

# Reddit threads + comments (~5 min)
python pipeline/collect/reddit_collector.py

# YouTube video transcripts (no API key needed — free)
python pipeline/collect/transcript_collector.py
```

Outputs:
- `pipeline/data/raw/youtube_comments_iphone17.jsonl`
- `pipeline/data/raw/reddit_iphone17.jsonl`
- `pipeline/data/raw/youtube_transcripts_iphone17.jsonl`

### 5. Process and score

```bash
# Normalize + deduplicate all three sources
python pipeline/process/normalize_reviews.py

# Run ABSA (~15-30 min depending on volume)
python pipeline/process/run_absa.py
```

Final outputs:
- `pipeline/data/derived/review_aspect_scores.json` — per-model, per-aspect sentiment scores
- `pipeline/data/derived/review_quotes.json` — verbatim reviewer quotes + positive_pct per aspect

Example output:
```json
{
  "iphone-17-pro": {
    "camera": {
      "positive_pct": 79,
      "total_mentions": 985,
      "quotes": [
        {"text": "The low light performance is stunning, way better than my old phone.", "sentiment": "positive"},
        {"text": "Portrait mode nails the bokeh without making it look fake.", "sentiment": "positive"},
        {"text": "ProRes files are huge and fill up storage fast.", "sentiment": "negative"}
      ]
    }
  }
}
```

---

## Backend

FastAPI server with a Claude claude-sonnet-4-6 agentic loop and 5 tools for product search, ranking, and comparison.

```bash
cd ~/Documents/apple-store-agent/backend
source ../venv/bin/activate
cp .env.example .env   # add ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --port 8000
```

Key endpoints:
- `GET /api/health` — `{"status":"ok","catalog_loaded":true,"model_count":4}`
- `GET /api/catalog` — full iPhone catalog with specs
- `POST /api/chat` — SSE streaming chat with Claude agent

---

## Frontend

React + Vite Apple Store UI with streaming chat panel, comparison table, and product modal.

```bash
cd ~/Documents/apple-store-agent/frontend
npm install
npm run dev   # → http://localhost:5173
```

Vite proxies `/api/*` → `localhost:8000` automatically.

---

## Success Criteria

| Check | Target | Actual |
|-------|--------|--------|
| Synthetic test aspect accuracy | ≥ 80% | 85% |
| Synthetic test sentiment accuracy | ≥ 75% | 80% |
| Models with confidence > 0.5 on ≥ 4 aspects | ≥ 3 models | 4 models |
| Normalized reviews per major model | ≥ 1,000 | ≥ 2,600 |
| Total normalized review corpus | — | 10,621 |

---

## How It Works

See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for a plain-English deep dive into the AI architecture — the agentic loop, the ABSA pipeline, the blended ranking formula, and how reviewer quotes surface in recommendations.
