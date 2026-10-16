from __future__ import annotations

import os
from common import request_json, save_csv, save_json

URL = "https://www.alphavantage.co/query"


def main() -> None:
    key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    if not key:
        print("[Alpha Vantage] skipped: set ALPHA_VANTAGE_API_KEY in .env")
        return
    topics = os.getenv("ALPHA_VANTAGE_TOPICS", "manufacturing").strip()
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": topics,
        "limit": min(int(os.getenv("ALPHA_VANTAGE_LIMIT", "100")), 100),
        "sort": "LATEST",
        "apikey": key,
    }
    data = request_json(URL, params=params)
    if isinstance(data, dict) and ("Error Message" in data or "Note" in data or "Information" in data):
        raise RuntimeError(f"Alpha Vantage returned a message (quota/key issue likely): {data}")
    json_path = save_json("alpha_vantage_news_sentiment", data)
    feed = data.get("feed", []) if isinstance(data, dict) else []
    rows = []
    for article in feed:
        rows.append({
            "provider": "Alpha Vantage",
            "provider_article_id": article.get("url"),
            "title": article.get("title"),
            "description_or_snippet": article.get("summary"),
            "canonical_url": article.get("url"),
            "publisher": article.get("source"),
            "published_at_utc": article.get("time_published"),
            "language": article.get("language"),
            "overall_sentiment_score": article.get("overall_sentiment_score"),
            "overall_sentiment_label": article.get("overall_sentiment_label"),
            "ticker_sentiment": article.get("ticker_sentiment"),
            "topics": article.get("topics"),
            "search_query": topics,
        })
    csv_path = save_csv("alpha_vantage_news_sentiment", rows)
    print(f"Alpha Vantage: {len(rows)} article records. JSON: {json_path}; CSV: {csv_path}")


if __name__ == "__main__":
    main()
