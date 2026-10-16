# ProcuraX — Real News & Market Data Connectors (Free-tier starter)

This is a live-data connector starter, not a synthetic dataset. When run, it requests current/recent records from the providers you enable and writes the received responses into `data/raw/`. Authenticated connectors require API keys that you register yourself.

## Recommended free configuration

1. **GDELT DOC API** — broad global news, no API key. Useful for supplier disruption, port congestion, factory closures, labour strikes, export restrictions and logistics incidents. It returns article metadata and URLs; calculate your own sentiment/event classification unless using a provider/model that returns it.
2. **Marketaux** — market/financial news with entity matching and per-entity sentiment scores. Free plan currently advertises 100 requests/day and up to 3 articles per news request. Sign up: https://www.marketaux.com/ . Read current limits/terms before relying on them.
3. **Alpha Vantage NEWS_SENTIMENT** — market news with ticker/topic relevance and sentiment metadata. Free API usage is currently limited (documented at 25 API requests/day for the standard free usage limit); use sparingly. Key: https://www.alphavantage.co/support/#api-key
4. **NewsData.io** — alternative general and market news. Free plan currently lists 200 API credits/day and 12-hour delay for its free plan. Key: https://newsdata.io/
5. **SEC EDGAR** — primary-company filings and submission metadata, no API key; provide a descriptive User-Agent with a contact address and respect SEC fair-access guidance. https://www.sec.gov/edgar/sec-api-documentation

The free plan and data terms can change. Verify each provider's latest usage limits, caching, attribution, retention and display/redistribution permissions before public deployment. An API being free to call does not automatically grant the right to republish full articles.

## Setup (Windows PowerShell)

```powershell
cd ProcuraX_Real_Data_Connectors
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Put your own keys in `.env`. Do not commit `.env`, expose it in screenshots, or put keys in frontend code. The provided `.gitignore` excludes it.

## Run connectors

```powershell
python src/fetch_gdelt.py
python src/fetch_marketaux.py
python src/fetch_alpha_vantage.py
python src/fetch_newsdata.py
python src/fetch_sec_edgar.py
```

Each connector can be run independently; a missing optional key is reported and that connector is skipped. The output folder stores JSON responses and normalized CSV files where practical. Raw responses should be retained with retrieval timestamps and source URLs so evidence can be audited.

## Search terms tailored for ProcuraX

The defaults search terms around supplier risk and logistics disruption. Change them in each script to fit the scenario. Useful query terms:

- `supplier shutdown`, `factory closure`, `supplier bankruptcy`, `capacity reduction`
- `semiconductor shortage`, `component shortage`, `raw material shortage`
- `port congestion`, `port closure`, `shipping delay`, `container rates`
- `labor strike`, `export restriction`, `sanctions`, `earthquake`, `flood`, `cyclone`
- `automotive supply chain`, `battery material`, `copper`, `aluminium`, `lithium`, `nickel`

## What each provider gives you

- **Marketaux:** entity sentiment is provider-generated; preserve both the article-level metadata and entity-level score. Sentiment is not equivalent to risk: a positive article can still report a risk, and a negative article may be irrelevant to your supplier.
- **Alpha Vantage:** market news & sentiment data, ticker/topic relevance and sentiment scores. Broad topic coverage is not the same as an operational supplier event feed.
- **GDELT:** wide global-news search and article metadata. Treat its returned headlines as evidence leads; classify event type, severity, affected facility/location, recency and corroboration separately.
- **NewsData.io:** additional coverage and categories; free tier is delayed, so it is not suitable for real-time alerts.
- **SEC EDGAR:** authoritative corporate filings; good for disclosed supply constraints and risk factors, but filings are periodic and often not operationally real-time.

## ProcuraX normalized data contract

For every ingested article, retain these fields when available:

- `provider`, `provider_article_id`, `title`, `description_or_snippet`, `canonical_url`, `publisher`, `published_at_utc`, `retrieved_at_utc`, `language`
- `entity_name`, `entity_type`, `entity_symbol`, `entity_match_score`, `provider_sentiment_score`
- `search_query`, `raw_payload_path`, `ingestion_status`

For your own downstream model, add separate derived fields:

- `event_type`, `event_severity`, `affected_supplier_or_facility`, `affected_country_or_port`
- `source_reliability`, `corroboration_count`, `contradiction_flag`, `evidence_age_hours`
- `procurement_exposure_match`, `risk_hypothesis`, `evidence_confidence`, `review_status`

Keep raw provider sentiment separate from your governed ProcuraX risk score. A headline's tone alone should never drive a procurement action.

## Provider sign-up links and free-plan notes

- GDELT docs/data: https://www.gdeltproject.org/data.html — no API key for DOC API.
- Marketaux docs and sign-up: https://www.marketaux.com/documentation and https://www.marketaux.com/ . Free: 100 requests/day, 3 articles/request according to the current published pricing.
- Alpha Vantage docs/key: https://www.alphavantage.co/documentation/ and https://www.alphavantage.co/support/#api-key . Standard free usage is limited to 25 API requests/day; check endpoint-specific entitlement.
- NewsData.io docs/key: https://newsdata.io/documentation and https://newsdata.io/ . Free currently lists 200 credits/day, up to 10 articles/request, and a 12-hour news delay.
- SEC data APIs: https://www.sec.gov/edgar/sec-api-documentation — no API key; valid descriptive User-Agent and fair access are required.
- FRED (optional macro indicators): https://fred.stlouisfed.org/docs/api/api_key.html — free registration required.
- NOAA climate data (optional weather disruption signals): https://www.ncei.noaa.gov/cdo-web/token — email registration required; documented at 10,000 requests/day, 5 requests/second per token.
- World Bank commodity prices (optional commodity indicators): https://www.worldbank.org/en/research/commodity-markets — downloadable historical XLS data, no API key is needed for the published files.

## Research and demo safeguards

1. Store the original title, URL, source and timestamp with every evidence record.
2. Deduplicate by canonical URL/title similarity before aggregating sentiment.
3. Store article publication time and ingestion time separately; never confuse stale news with a fresh event.
4. Require an entity/location match and corroboration before calling a news item a supplier disruption.
5. Respect terms, robots.txt, paywalls and copyright. Store metadata/snippets and link users to the publisher rather than bulk-republishing full article text.
6. Keep the flagship disruption scenario out of model training if you use it as a held-out demonstration.
7. This starter captures real public information from enabled sources but does not guarantee that every provider returns records for every query.


## Integration note inside the main ProcuraX repository
These scripts are isolated reference fetchers. The main application should not shell out to them from an HTTP request. Port provider logic to typed backend adapters, centralize secrets in the root/backend environment settings, persist normalized observations, and add fixture-based tests before connecting them to the workspace. Live fetches must be opt-in.
