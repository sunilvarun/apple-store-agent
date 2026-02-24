"""
YouTube Data API v3 collector for iPhone 17 reviews.

Fetches top comments from iPhone 17 review videos.
Output: pipeline/data/raw/youtube_comments_iphone17.jsonl

Quota usage: ~1 unit per 100-comment page. Total run ~300 units (well within 10k/day limit).

Setup:
    1. Get API key from https://console.cloud.google.com
    2. Enable YouTube Data API v3
    3. Add YOUTUBE_API_KEY to .env
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

load_dotenv(Path(__file__).parents[2] / ".env")

API_KEY = os.getenv("YOUTUBE_API_KEY")
OUTPUT_PATH = Path(__file__).parents[1] / "data" / "raw" / "youtube_comments_iphone17.jsonl"

SEARCH_QUERIES = [
    "iPhone 17 Pro Max review",
    "iPhone 17 Pro review",
    "iPhone 17 review",
    "iPhone 17 Air review",
    "iPhone 17 Pro camera test",
    "iPhone 17 battery life test",
]

MAX_VIDEOS_PER_QUERY = 10
MAX_COMMENTS_PER_VIDEO = 500
SLEEP_BETWEEN_REQUESTS = 0.5  # seconds


def build_client():
    if not API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY not found in .env\n"
            "Get one at: https://console.cloud.google.com → APIs & Services → Credentials"
        )
    return build("youtube", "v3", developerKey=API_KEY)


def search_videos(client, query: str, max_results: int = 10) -> list[dict]:
    """Search for videos matching query. Returns list of {video_id, title}."""
    try:
        response = client.search().list(
            q=query,
            part="id,snippet",
            type="video",
            maxResults=max_results,
            order="relevance",
            relevanceLanguage="en",
        ).execute()
        time.sleep(SLEEP_BETWEEN_REQUESTS)

        videos = []
        for item in response.get("items", []):
            if item["id"].get("kind") == "youtube#video":
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                })
        return videos
    except HttpError as e:
        print(f"  [WARN] Search failed for '{query}': {e}")
        return []


def fetch_comments(client, video_id: str, video_title: str, max_comments: int = 500) -> list[dict]:
    """Fetch top comments for a video. Returns list of comment dicts."""
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:
            response = client.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                order="relevance",
                pageToken=next_page_token,
            ).execute()
            time.sleep(SLEEP_BETWEEN_REQUESTS)

            for item in response.get("items", []):
                top = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "source": "youtube",
                    "video_id": video_id,
                    "video_title": video_title,
                    "comment_text": top["textDisplay"],
                    "like_count": top.get("likeCount", 0),
                    "published_date": top["publishedAt"],
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        if "commentsDisabled" in str(e):
            print(f"  [SKIP] Comments disabled for video {video_id}")
        else:
            print(f"  [WARN] Comment fetch failed for {video_id}: {e}")

    return comments


def run():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Building YouTube client...")
    client = build_client()

    seen_video_ids: set[str] = set()
    seen_comment_texts: set[str] = set()
    total_written = 0
    quota_estimate = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        for query in SEARCH_QUERIES:
            print(f"\nSearching: '{query}'")
            videos = search_videos(client, query, MAX_VIDEOS_PER_QUERY)
            quota_estimate += 100  # search costs ~100 units
            print(f"  Found {len(videos)} videos")

            for video in tqdm(videos, desc="  Fetching comments", leave=False):
                vid_id = video["video_id"]
                if vid_id in seen_video_ids:
                    continue
                seen_video_ids.add(vid_id)

                comments = fetch_comments(client, vid_id, video["title"], MAX_COMMENTS_PER_VIDEO)
                quota_estimate += len(comments) // 100 + 1

                for comment in comments:
                    # Deduplicate across videos
                    text = comment["comment_text"].strip()
                    if text in seen_comment_texts:
                        continue
                    seen_comment_texts.add(text)

                    out_file.write(json.dumps(comment, ensure_ascii=False) + "\n")
                    total_written += 1

            if quota_estimate > 8000:
                print(f"\n[WARN] Estimated quota usage ~{quota_estimate} units. Stopping early to stay under daily limit.")
                break

    print(f"\nDone. {total_written} comments written to {OUTPUT_PATH}")
    print(f"Unique videos scraped: {len(seen_video_ids)}")
    print(f"Estimated quota used: ~{quota_estimate} / 10,000 units")
    print(f"Collected: {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    run()
