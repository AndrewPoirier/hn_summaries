import json
import time

import requests

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

with open("settings.json", "r") as f:
    settings = json.load(f)

REQUEST_TIMEOUT_SECONDS = settings.get("request_timeout_seconds", 45)
REQUEST_USER_AGENT = settings.get("request_user_agent", "hn_summaries/1.0")
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


def _get_json(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": REQUEST_USER_AGENT},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BACKOFF_BASE ** attempt
                print(f"Request error for {url}: {e}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                print(f"Error fetching {url}: {e}")
                return None


def get_top_story_ids(limit=500):
    ids = _get_json(f"{HN_API_BASE}/topstories.json")
    if not ids:
        return []
    return ids[:limit]


def get_item(item_id):
    return _get_json(f"{HN_API_BASE}/item/{item_id}.json")
