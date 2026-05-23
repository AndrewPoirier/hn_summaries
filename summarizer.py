import json
import os

import requests
from dotenv import load_dotenv

# Load settings from summarizer_settings.json
with open('summarizer_settings.json', 'r') as f:
    settings = json.load(f)

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def summarize(text):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    # Truncate to keep input within a reasonable token budget
    max_input_chars = settings.get("max_input_chars", 12000)
    text = text[:max_input_chars]

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hn-summaries",
            "X-Title": "HN Summaries",
        },
        json={
            "model": settings["model"],
            "messages": [
                {"role": "system", "content": settings["prompt"]},
                {"role": "user", "content": f"Summarize the following web page content:\n\n{text}"},
            ],
            "max_tokens": settings.get("max_tokens", 800),
        },
        timeout=settings.get("request_timeout_seconds", 60),
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
