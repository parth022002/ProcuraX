"""Deterministic fixture payloads for signal intelligence providers.

Ensures CI, offline tests, and mock replays run reliably without external network dependencies.
"""
from __future__ import annotations

FIXTURE_GDELT = {
    "articles": [
        {
            "url": "https://www.reuters.com/markets/commodities/copper-supply-disruption-global-refinery-maintenance-2026",
            "title": "Copper Supply Facing Extended Constraints Amid Major Refinery Maintenance",
            "domain": "reuters.com",
            "seendate": "2026-07-02T08:30:00Z",
            "language": "English",
            "sourcecountry": "United Kingdom",
        },
        {
            "url": "https://www.bloomberg.com/news/articles/2026-06-15/port-congestion-slows-raw-material-deliveries-west-coast-india",
            "title": "Port Congestion Slows Raw Material Inflows to Western India Automotive Hubs",
            "domain": "bloomberg.com",
            "seendate": "2026-06-15T12:00:00Z",
            "language": "English",
            "sourcecountry": "India",
        },
    ]
}

FIXTURE_MARKETAUX = {
    "data": [
        {
            "uuid": "mkt-uuid-1047-copper",
            "title": "Automotive Component Suppliers Warn of BLDC Motor Magnetic Coil Delays",
            "description": "Shortage of high-grade copper wire and electrical steel impacts motor assembly lead times across South Asia.",
            "snippet": "Shortage of high-grade copper wire and electrical steel impacts motor assembly lead times across South Asia.",
            "url": "https://www.financialexpress.com/auto/auto-parts-makers-flag-copper-shortages-delays/3456789/",
            "source": "financialexpress.com",
            "published_at": "2026-07-10T14:15:00Z",
            "language": "en",
            "entities": [
                {
                    "name": "ApexDrive Components Ltd",
                    "symbol": "APEXDRV",
                    "type": "equity",
                    "country": "in",
                    "industry": "Automotive Parts",
                    "match_score": 0.92,
                    "sentiment_score": -0.74,
                    "highlights": ["severe delivery delays reported for third-quarter delivery schedules"],
                }
            ],
        }
    ]
}

FIXTURE_ALPHA_VANTAGE = {
    "feed": [
        {
            "title": "Global Logistics Bottlenecks Impact Tier-1 Sub-assembly Shipments",
            "url": "https://www.wsj.com/articles/supply-chain-shipping-container-imbalances-2026",
            "time_published": "2026-07-18T10:45:00Z",
            "summary": "Container shortages and freight route re-directions increase average transit times by 12 to 18 days.",
            "source": "Wall Street Journal",
            "language": "en",
            "overall_sentiment_score": -0.58,
            "overall_sentiment_label": "Bearish",
            "ticker_sentiment": [],
            "topics": [{"topic": "Manufacturing", "relevance_score": "0.95"}],
        }
    ]
}

FIXTURE_NEWSDATA = {
    "results": [
        {
            "article_id": "newsdata-art-8812",
            "title": "Industrial Raw Material Prices Surge Following Mining Work Stoppage",
            "description": "Essential magnet wire and copper rod prices climb 8.4% week-on-week.",
            "link": "https://economictimes.indiatimes.com/industry/indlgoods/raw-materials-price-surge-2026",
            "source_id": "economictimes",
            "pubDate": "2026-07-22 09:00:00",
            "language": "english",
        }
    ]
}

FIXTURE_SEC_EDGAR = {
    "name": "Global Auto Components Holdings Inc",
    "filings": {
        "recent": {
            "form": ["10-Q", "8-K"],
            "accessionNumber": ["0001047000-26-000123", "0001047000-26-000124"],
            "filingDate": ["2026-07-28", "2026-07-05"],
            "reportDate": ["2026-06-30", "2026-07-05"],
            "primaryDocument": ["gac-20260630.htm", "gac-8k-20260705.htm"],
        }
    }
}
