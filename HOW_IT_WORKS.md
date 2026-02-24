# How It Works — Apple Store Agentic Commerce App

> A plain-English deep dive into the AI engine behind this project, written for product thinkers.
> No code knowledge required.

---

## Table of Contents

1. [The Big Idea](#1-the-big-idea)
2. [What Makes This "Agentic"](#2-what-makes-this-agentic)
3. [The Three Layers of Intelligence](#3-the-three-layers-of-intelligence)
4. [Layer 1 — The Review Data Pipeline](#4-layer-1--the-review-data-pipeline)
5. [Layer 2 — The Recommendation Engine](#5-layer-2--the-recommendation-engine)
6. [Layer 3 — The Claude Agent](#6-layer-3--the-claude-agent)
7. [How a Recommendation Actually Happens (Step by Step)](#7-how-a-recommendation-actually-happens-step-by-step)
8. [The App List Feature](#8-the-app-list-feature)
9. [Why This Approach vs. Just Asking ChatGPT](#9-why-this-approach-vs-just-asking-chatgpt)
10. [Limitations and Honest Caveats](#10-limitations-and-honest-caveats)

---

## 1. The Big Idea

Most product recommendation systems do one of two things:

- **Filter by specs** — "You want 5x zoom? Here are phones with 5x zoom." Cold, mechanical.
- **Ask an LLM** — "Hey ChatGPT, what's the best iPhone?" The model answers from memory, which may be months or years out of date, and cites no evidence.

This app combines both approaches with a third ingredient: **real customer sentiment**, extracted from thousands of YouTube comments and Reddit posts written by actual users after they bought these phones.

The result: a recommendation that sounds like advice from a knowledgeable friend who has read every review on the internet — and can show their work.

---

## 2. What Makes This "Agentic"

The word "agent" is used loosely in AI. Here's what it means precisely in this project.

A traditional AI chatbot works like a **single tennis volley**: you ask a question, the model hits back an answer. Done.

An **agentic** system works more like a **research analyst**: you give them a brief, and they go away, use tools, gather data, synthesize it, and come back with a structured answer — often doing several things in parallel before returning to you.

In this app, when you ask "Which iPhone is best for photography?", Claude doesn't answer from memory. Instead, it:

1. **Decides what tools to use** (like a researcher choosing which databases to query)
2. **Calls those tools** (which run real code that looks up real data)
3. **Reads the results** (specs from Apple's catalog, review scores from 8,737 real comments)
4. **Reasons over the results** and synthesizes an answer
5. **Responds** with a recommendation grounded in that data

This loop — think → act → observe → think again — is what makes it "agentic." Claude is not a lookup table. It is a reasoning engine that directs its own research process.

---

## 3. The Three Layers of Intelligence

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Claude Agent (the "brain")                    │
│  Understands intent, directs tools, synthesizes answer  │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Recommendation Engine (the "calculator")      │
│  Scores phones on specs + reviews, ranks candidates     │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Review Data Pipeline (the "research")         │
│  Collected 8,737 real reviews → extracted sentiment     │
└─────────────────────────────────────────────────────────┘
```

Each layer feeds the next. The pipeline feeds the engine. The engine feeds the agent. The agent talks to you.

---

## 4. Layer 1 — The Review Data Pipeline

### Why we needed this

Apple publishes spec sheets. We can look up that the iPhone 17 Pro Max has a 48MP camera. But spec sheets don't tell you:

- "Does the camera actually hold up in low light in real conditions?"
- "Does it run hot when gaming?"
- "Is the battery good enough for a full travel day?"

For that, you need to hear from people who actually bought and used the phone. That's what this layer does.

### Step 1: Data Collection

We collected comments from two sources using their public APIs:

| Source | What we collected | Volume |
|--------|------------------|--------|
| YouTube | Comments on iPhone 17 review videos | 11,447 comments from 54 videos |
| Reddit | Posts from r/apple, r/iphone, r/iPhonePhotography | 1,138 comments |
| **Total** | | **12,585 raw comments** |

We searched for queries like _"iPhone 17 Pro camera test"_, _"iPhone 17 Air review"_, _"iPhone 17 battery life"_ to find relevant videos and threads.

### Step 2: Cleaning and Labeling

Not all comments are useful. We filtered out:
- Comments under 10 words (too short to contain real signal)
- Spam (all-caps, repetitive characters, emoji-only)
- Near-duplicates (comments that were essentially copy-pasted)

We also had to figure out **which iPhone model each comment was about**. This sounds easy but is surprisingly hard — most people just write "the camera is amazing" without saying which iPhone. We solved this by:

1. Scanning the comment text for model keywords ("Pro Max", "Air", etc.)
2. If no match, falling back to the **video title** ("iPhone 17 Pro Review" tells us the model even if the comment doesn't)

After cleaning: **8,737 usable reviews** across 4 models, all above 1,000 reviews per model.

| Model | Reviews |
|-------|---------|
| iPhone 17 Pro | 2,756 |
| iPhone 17 Pro Max | 2,218 |
| iPhone 17 Air | 1,902 |
| iPhone 17 | 1,861 |

### Step 3: Aspect-Based Sentiment Analysis (ABSA)

This is the core intellectual contribution of the pipeline. Instead of asking "is this comment positive or negative overall?", we ask: **"For each specific aspect of the phone, what does this comment say — and is it positive or negative?"**

The 8 aspects we track:

| Aspect | Example seed phrases |
|--------|---------------------|
| **camera** | photo quality, zoom, night mode, portrait, ProRAW |
| **battery** | battery life, battery drain, charge, all day, died |
| **performance** | fast, smooth, chip, lag, speed, A19 |
| **heating** | hot, overheating, warm, thermal |
| **display** | screen, brightness, OLED, refresh rate |
| **durability** | dropped, scratched, cracked, titanium |
| **weight** | heavy, light, comfortable, bulky |
| **value** | worth it, price, expensive, overpriced |

**How aspect detection works:**

We use an AI technique called **sentence embeddings** (via a model called `all-MiniLM-L6-v2`). Every piece of text — whether it's a comment or an aspect keyword — gets converted into a list of numbers (a "vector") that represents its meaning. Texts with similar meaning have vectors that point in similar directions.

We take each aspect's keywords, compute their average vector (the "centroid"), then check: does this comment's vector point close enough to this aspect's centroid? If yes (similarity > 35%), the comment is tagged as being about that aspect.

**How sentiment scoring works:**

We use a tool called **VADER** (Valence Aware Dictionary and sEntiment Reasoner), designed specifically for social media language. It handles things like capitalization ("SO good" vs "so good"), punctuation ("great!!!" vs "great"), and negation ("not bad" is positive, not negative).

Each comment gets a sentiment score from -1.0 (very negative) to +1.0 (very positive).

**The output:**

For each model + aspect combination, we compute:
- **Mean sentiment score** (rescaled to 0–1, where 0.5 is neutral)
- **Volume** (how many comments mentioned this aspect)
- **Confidence** (how much to trust the score — higher volume = higher confidence, capped at 1.0 after 500+ mentions)

This gives us a table like:

| Model | Camera Score | Battery Score | Value Score | ... |
|-------|-------------|---------------|-------------|-----|
| iPhone 17 Pro | 0.604 | 0.589 | 0.571 | ... |
| iPhone 17 Pro Max | 0.598 | 0.601 | 0.563 | ... |
| iPhone 17 Air | 0.581 | 0.556 | 0.534 | ... |
| iPhone 17 | 0.572 | 0.578 | 0.587 | ... |

This table — `review_aspect_scores.json` — is the permanent artifact that powers every recommendation. It was computed once from 8,737 real reviews and lives in the codebase.

---

## 5. Layer 2 — The Recommendation Engine

Once we have the review scores, we need a way to **rank phones against each other** for a specific user's needs.

### The Preference Vector

When Claude understands what you want, it extracts a structured "preference profile" — we call this the **PreferenceVector**. It looks something like:

```
{
  "priorities": ["camera", "battery"],   ← what matters most to you
  "budget_max": 1100,                    ← hard ceiling
  "storage_min": "256GB",               ← minimum storage needed
  "size_preference": "large",           ← screen size preference
  "must_have": [],                      ← deal-breakers
  "app_categories": ["photo_editing"]   ← inferred from your app list
}
```

This vector tells the ranking engine exactly what to optimize for.

### The Blended Score Formula

For each candidate phone, we compute a **blended score** that combines two signals:

```
Final Score = (Spec Score × 0.6) + (Review Score × Confidence × 0.4)
```

**Why 60/40?**

Specs are objective and verifiable — a phone either has 5x optical zoom or it doesn't. Reviews are subjective and vary by sample. The 60/40 split says: trust the facts first, but let real user sentiment meaningfully influence the outcome. The `× Confidence` term means a score based on 50 reviews weighs less than one based on 800 reviews.

**How Spec Scores are calculated:**

Each spec is converted to a 0–1 score relative to the current catalog. Examples:

| Spec | "Best" gets | Logic |
|------|-------------|-------|
| Camera system | 1.0 if 3-camera, 0.7 if 2-camera, 0.4 if 1-camera | More lenses = more capability |
| Battery | Normalized by max hours in catalog | More hours = higher score |
| Performance | A19 Pro = 1.0, A19 = 0.85 | Chip tier hierarchy |
| Weight | Lighter = higher score (inverted) | Portability |
| Value | Lower starting price = higher score (inverted) | Affordability |

**How Review Scores feed in:**

The review score for a given aspect (e.g., "camera") for a given phone comes directly from the ABSA pipeline. If you prioritize "camera", the camera review score flows into your personalized ranking with full weight. If you prioritize "battery", the battery score dominates.

**The final ranking:**

```
Total Score = Σ (weight_i × blended_score_i)
```

Where `weight_i` is determined by your priorities. If you said camera is your #1 priority, camera gets the highest weight. The phone with the highest total score wins.

---

## 6. Layer 3 — The Claude Agent

The agent is the conversational interface that sits on top of the engine. It is not just a chatbot — it is a **director** that decides which tools to call, in what order, with what parameters, based on what you asked.

### The 5 Tools

Claude has access to exactly 5 tools, each a precise function:

| Tool | What it does | When Claude uses it |
|------|-------------|---------------------|
| `extract_preferences` | Converts natural language into a structured PreferenceVector | Always first — understands what you actually want |
| `search_catalog` | Filters the iPhone catalog by series, price, tier | Narrows candidates before deep analysis |
| `get_product_details` | Returns full specs + review scores for one model | Deep-dive on a specific phone |
| `rank_iphones` | Runs the blended scorer on a list of candidates | The core recommendation step |
| `compare_products` | Side-by-side comparison of 2–3 models | When you ask "what's the difference between X and Y?" |

### The System Prompt

Claude receives a set of hard instructions before every conversation:

- **Always use tools.** Never answer from memory or training data. Specs change. Reviews are real data. Use them.
- **Never invent specifications.** If a spec isn't in the catalog, say so.
- **Use `rank_iphones` for recommendations.** Don't reason intuitively about which phone wins — run the numbers.
- **Cite evidence.** When you make a claim ("the Pro Max has the best battery"), you should have the review data to back it up.

This is called "grounding" — anchoring the model's outputs to verifiable, structured data rather than letting it speculate.

### The Agentic Loop

Every time you send a message, this loop runs:

```
1. Send your message + conversation history to Claude
       ↓
2. Claude reasons about what to do next
       ↓
3. Claude decides to call one or more tools
   (often in parallel — e.g., extract_preferences + search_catalog simultaneously)
       ↓
4. We execute those tools locally (real code, real data)
       ↓
5. We send the tool results back to Claude
       ↓
6. Claude reasons again: "Do I have enough to answer? Or do I need more?"
       ↓
7a. If Claude needs more → go back to step 3 (another tool call)
7b. If Claude has enough → generate the final answer and stream it to you
```

This loop can run up to **10 iterations** (a safety cap to prevent infinite loops). In practice, most recommendations resolve in 2–3 iterations.

### Streaming

The response arrives in real time — you see Claude's thinking appear word by word, and you see tool calls animate as they happen ("Searching catalog...", "Ranking iPhones..."). This is powered by **Server-Sent Events (SSE)**, the same technology used by ChatGPT's streaming responses. The backend pushes small chunks of data to the browser as they're ready, rather than waiting for the full answer to complete before showing anything.

---

## 7. How a Recommendation Actually Happens (Step by Step)

Let's trace exactly what happens when you type: **"Best iPhone for photography under $1,100"**

**Turn 1 — Claude receives your message and decides to act in parallel:**
- Calls `extract_preferences` → extracts `{priorities: ["camera"], budget_max: 1100}`
- Calls `search_catalog` → filters to phones under $1,100 → returns iPhone 17, 17 Air, 17 Pro

**Turn 2 — Claude receives those results and calls the ranker:**
- Calls `rank_iphones` with the 3 candidates and your PreferenceVector
- The engine computes blended scores for each, weighted toward camera
- Returns ranked list: `[iPhone 17 Pro (0.81), iPhone 17 Air (0.74), iPhone 17 (0.71)]`

**Turn 3 — Claude has everything it needs. It generates the answer:**
> "Based on specs and 2,756 real user reviews, the **iPhone 17 Pro** is the best photography phone under $1,100. Its 3-camera system with 5× optical zoom and ProRAW support earns a camera sentiment score of 0.604 from 795 dedicated camera reviews — the highest volume of any model. If you want to save $100 and don't need telephoto zoom, the iPhone 17 Air is a solid runner-up..."

The entire process takes 3–6 seconds. No information was hallucinated. Every claim traces back to either a spec in the catalog or a score derived from real reviews.

---

## 8. The App List Feature

One of the more novel features: you can paste your list of apps and get a recommendation based on what those apps actually need from the hardware.

This works through the `extract_preferences` tool, which contains a hardcoded knowledge base mapping app categories to hardware requirements:

| App Category | GPU Need | Storage Need | Camera Need |
|-------------|----------|--------------|-------------|
| Photo/video editing (Lightroom, CapCut) | High | High | Yes |
| Gaming (Genshin Impact, PUBG, CoD) | High | High | No |
| Productivity (Word, Notion, Slack) | Low | Low | No |
| Streaming (Netflix, YouTube) | Medium | Medium | No |

So if you paste "Lightroom, PUBG Mobile, Slack", the system infers you need high GPU performance and high storage — which translates to prioritizing the Performance and Storage spec scores in the ranker, and likely recommends a Pro model.

Unknown apps default to "medium" requirements on all dimensions.

---

## 9. Why This Approach vs. Just Asking ChatGPT

| | This App | ChatGPT / Generic LLM |
|---|---|---|
| **Data freshness** | Grounded in real iPhone 17 reviews collected now | Training data cut-off, may describe old models |
| **Source of truth** | Specs from structured catalog, sentiment from 8,737 real reviews | Model's internal weights (impossible to audit) |
| **Auditability** | "iPhone 17 Pro camera score: 0.604 from 795 reviews" | "Trust me" |
| **Hallucination risk** | Low — agent is prohibited from using memory for specs | High — models confabulate specs confidently |
| **Personalization** | PreferenceVector + app-to-hardware mapping | Generic advice |
| **Ranking** | Deterministic blended scorer with explicit weights | Intuitive reasoning (opaque) |

The key insight: **LLMs are excellent reasoners but poor fact-keepers.** This architecture plays to Claude's strength (reasoning, synthesis, natural language) while compensating for its weakness (factual recall) by giving it tools backed by structured, verified data.

---

## 10. Limitations and Honest Caveats

No system is perfect. Here's what to know:

**Review data is YouTube/Reddit-biased.** These platforms skew toward enthusiasts and power users. A casual user who bought an iPhone 17 and is happy with it probably didn't leave a YouTube comment. This means sentiment scores may underweight "good enough" satisfaction.

**ABSA has ~75% sentiment accuracy.** In testing against 20 hand-labeled reviews, the pipeline got sentiment direction right 15/20 times. At 2,000+ reviews per model, the errors average out — but individual scores should be treated as directional signals, not precise measurements.

**iPhone 17 isn't released yet.** The catalog is based on announced/leaked specs and realistic placeholders. The review data is from early adopter impressions, pre-release leaks, and comparison content. Real post-launch reviews would improve the scores significantly.

**The ranker weights are assumptions.** The 60/40 spec/review split and the per-spec scoring formulas were designed thoughtfully but not A/B tested. A real product would tune these weights against a held-out test set of "ground truth" recommendations.

**App-to-hardware mapping is handcrafted.** The knowledge base that maps apps like "Lightroom" to hardware requirements was written by hand. It covers the most common apps well but will default to "medium" for anything niche or new.

---

*Built with Claude claude-sonnet-4-6 (Anthropic), FastAPI, React, sentence-transformers, and VADER sentiment analysis.*
*Review data: 8,737 comments from YouTube and Reddit, collected February 2026.*
