from __future__ import annotations

import os
from common import request_json, save_csv, save_json

URL = "https://api.marketaux.com/v1/news/all"


def main() -> None:
    token = os.getenv("MARKETAUX_API_TOKEN", "").strip()
    if not token:
        print("[Marketaux] skipped: set MARKETAUX_API_TOKEN in .env")
        return
    query = os.getenv("MARKETAUX_SEARCH", 'supplier | "supply chain" | semiconductor | logistics | "factory shutdown" | port disruption')
    limit = min(int(os.getenv("MARKETAUX_LIMIT", "3")), 3)  # Free plan currently allows 3 articles/request.
    params = {
        "api_token": token,
        "search": query,
        "language": "en",
        "limit": limit,
        "group_similar": "true",
        "must_have_entities": "true",
    }
    data = request_json(URL, params=params)
    json_path = save_json("marketaux", data)
    articles = data.get("data", []) if isinstance(data, dict) else []
    rows = []
    for article in articles:
        entities = article.get("entities") or []
        if not entities:
            rows.append({
                "provider": "Marketaux", "provider_article_id": article.get("uuid"),
                "title": article.get("title"), "description_or_snippet": article.get("description") or article.get("snippet"),
                "canonical_url": article.get("url"), "publisher": article.get("source"),
                "published_at_utc": article.get("published_at"), "language": article.get("language"),
                "entity_name": None, "entity_symbol": None, "entity_type": None,
                "entity_match_score": None, "provider_sentiment_score": None, "search_query": query,
            })
        for entity in entities:
            rows.append({
                "provider": "Marketaux", "provider_article_id": article.get("uuid"),
                "title": article.get("title"), "description_or_snippet": article.get("description") or article.get("snippet"),
                "canonical_url": article.get("url"), "publisher": article.get("source"),
                "published_at_utc": article.get("published_at"), "language": article.get("language"),
                "entity_name": entity.get("name"), "entity_symbol": entity.get("symbol"), "entity_type": entity.get("type"),
                "entity_country": entity.get("country"), "entity_industry": entity.get("industry"),
                "entity_match_score": entity.get("match_score"), "provider_sentiment_score": entity.get("sentiment_score"),
                "sentiment_highlights": entity.get("highlights"), "search_query": query,
            })
    csv_path = save_csv("marketaux_articles_entities", rows)
    print(f"Marketaux: {len(articles)} articles, {len(rows)} entity/article rows. JSON: {json_path}; CSV: {csv_path}")


if __name__ == "__main__":
    main()
