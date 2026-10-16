from __future__ import annotations

import os
from common import request_json, save_csv, save_json

URL = "https://newsdata.io/api/1/latest"


def main() -> None:
    key = os.getenv("NEWSDATA_API_KEY", "").strip()
    if not key:
        print("[NewsData.io] skipped: set NEWSDATA_API_KEY in .env")
        return
    query = os.getenv("NEWSDATA_QUERY", 'supply chain OR supplier OR logistics OR port disruption OR semiconductor shortage')
    size = min(int(os.getenv("NEWSDATA_SIZE", "10")), 10)  # Free plan currently allows up to 10 articles/request.
    params = {"apikey": key, "q": query, "language": "en", "size": size}
    data = request_json(URL, params=params)
    if isinstance(data, dict) and data.get("status") == "error":
        raise RuntimeError(f"NewsData.io API error: {data}")
    json_path = save_json("newsdata_io", data)
    articles = data.get("results", []) if isinstance(data, dict) else []
    rows = []
    for article in articles:
        rows.append({
            "provider": "NewsData.io", "provider_article_id": article.get("article_id"),
            "title": article.get("title"), "description_or_snippet": article.get("description") or article.get("content"),
            "canonical_url": article.get("link"), "publisher": article.get("source_name"),
            "published_at_utc": article.get("pubDate"), "language": article.get("language"),
            "country": article.get("country"), "category": article.get("category"),
            "provider_sentiment_score": article.get("sentiment"),
            "search_query": query,
        })
    csv_path = save_csv("newsdata_io_articles", rows)
    print(f"NewsData.io: {len(rows)} article records. JSON: {json_path}; CSV: {csv_path}")


if __name__ == "__main__":
    main()
