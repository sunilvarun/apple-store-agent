"""
Reddit collector for iPhone 17 reviews using Reddit's public JSON API.

No credentials required. Uses Reddit's read-only JSON endpoints with a proper
User-Agent header, which is within Reddit's terms for research/personal use.

Output: pipeline/data/raw/reddit_iphone17.jsonl

Usage:
    python pipeline/collect/reddit_collector.py
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from tqdm import tqdm

OUTPUT_PATH = Path(__file__).parents[1] / "data" / "raw" / "reddit_iphone17.jsonl"

SUBREDDITS = ["apple", "iphone", "iPhonePhotography"]
SEARCH_QUERY = "iPhone 17"
MAX_THREADS_PER_SUBREDDIT = 40
CUTOFF_DAYS = 365

# Reddit requires a descriptive User-Agent for API access
HEADERS = {
    "User-Agent": "iphone17-review-research/1.0 (academic research; contact: research@example.com)"
}

SLEEP_BETWEEN_REQUESTS = 1.0   # stay well under 60 req/min rate limit
BASE_URL = "https://www.reddit.com"


def search_threads(subreddit: str, query: str, max_results: int = 40) -> list[dict]:
    """Search a subreddit for threads matching query. Handles pagination."""
    threads = []
    after = None
    cutoff_ts = (datetime.utcnow() - timedelta(days=CUTOFF_DAYS)).timestamp()

    while len(threads) < max_results:
        params = {
            "q": query,
            "sort": "relevance",
            "t": "year",
            "limit": min(100, max_results - len(threads)),
            "type": "link",
        }
        if after:
            params["after"] = after

        url = f"{BASE_URL}/r/{subreddit}/search.json"
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            resp.raise_for_status()
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        except requests.RequestException as e:
            print(f"  [WARN] Search failed for r/{subreddit}: {e}")
            break

        data = resp.json().get("data", {})
        posts = data.get("children", [])
        if not posts:
            break

        for post in posts:
            p = post.get("data", {})
            if p.get("created_utc", 0) < cutoff_ts:
                continue
            threads.append({
                "id": p.get("id"),
                "title": p.get("title", ""),
                "subreddit": subreddit,
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "created_utc": p.get("created_utc", 0),
            })

        after = data.get("after")
        if not after:
            break

    return threads


def fetch_thread_comments(subreddit: str, thread_id: str, thread_title: str) -> list[dict]:
    """Fetch top-level comments for a thread. Returns flat list of comment dicts."""
    url = f"{BASE_URL}/r/{subreddit}/comments/{thread_id}.json"
    params = {"limit": 500, "depth": 1, "sort": "top"}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    except requests.RequestException as e:
        print(f"  [WARN] Comment fetch failed for thread {thread_id}: {e}")
        return []

    try:
        listing = resp.json()
    except json.JSONDecodeError:
        return []

    # Reddit returns [thread_listing, comments_listing]
    if not isinstance(listing, list) or len(listing) < 2:
        return []

    comments = []
    comment_items = listing[1].get("data", {}).get("children", [])

    for item in comment_items:
        if item.get("kind") != "t1":
            continue
        c = item.get("data", {})
        body = c.get("body", "").strip()
        if body in ("[deleted]", "[removed]", ""):
            continue
        comments.append({
            "source": "reddit",
            "subreddit": subreddit,
            "thread_id": thread_id,
            "thread_title": thread_title,
            "comment_id": c.get("id", ""),
            "comment_text": body,
            "score": c.get("score", 0),
            "created_utc": datetime.utcfromtimestamp(
                c.get("created_utc", 0)
            ).isoformat() + "Z",
        })

    return comments


def run():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    seen_thread_ids: set[str] = set()
    seen_comment_ids: set[str] = set()
    total_threads = 0
    total_written = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        for subreddit in SUBREDDITS:
            print(f"\nSearching r/{subreddit} for '{SEARCH_QUERY}'...")
            threads = search_threads(subreddit, SEARCH_QUERY, MAX_THREADS_PER_SUBREDDIT)
            print(f"  Found {len(threads)} threads")

            for thread in tqdm(threads, desc=f"  r/{subreddit}", leave=False):
                tid = thread["id"]
                if not tid or tid in seen_thread_ids:
                    continue
                seen_thread_ids.add(tid)
                total_threads += 1

                comments = fetch_thread_comments(subreddit, tid, thread["title"])
                for comment in comments:
                    cid = comment["comment_id"]
                    if cid in seen_comment_ids:
                        continue
                    seen_comment_ids.add(cid)
                    out_file.write(json.dumps(comment, ensure_ascii=False) + "\n")
                    total_written += 1

    print(f"\nDone.")
    print(f"Threads scraped: {total_threads}")
    print(f"Comments written: {total_written}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Collected: {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    run()
