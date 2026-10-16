from __future__ import annotations

import os
from common import request_json, save_csv, save_json

URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = '"supply chain" OR supplier OR logistics OR semiconductor OR "port disruption" OR "factory shutdown" OR "export restriction"'


def main() -> None:
    params = {
        "query": QUERY,
        "mode": "ArtList",
        "format": "json",
        "sort": "DateDesc",
        "timespan": os.getenv("GDELT_TIMESPAN", "7d"),
        "maxrecords": int(os.getenv("GDELT_MAX_RECORDS", "100")),
    }
    data = request_json(URL, params=params, headers={"User-Agent": "ProcuraX research data client/1.0"})
    json_path = save_json("gdelt", data)
    articles = data.get("articles", []) if isinstance(data, dict) else []
    rows = []
    for article in articles:
        rows.append({
            "provider": "GDELT",
            "provider_article_id": article.get("url"),
            "title": article.get("title"),
            "description_or_snippet": None,
            "canonical_url": article.get("url"),
            "publisher": article.get("domain"),
            "published_at_utc": article.get("seendate"),
            "language": article.get("language"),
            "source_country": article.get("sourcecountry"),
            "provider_sentiment_score": None,
            "search_query": QUERY,
        })
    csv_path = save_csv("gdelt_articles", rows)
    print(f"GDELT: found {len(rows)} article records. JSON: {json_path}; CSV: {csv_path}")


if __name__ == "__main__":
    main()
