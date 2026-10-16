# Data, News, Market Sentiment & Connector Integration

## Purpose
Bring **real public signals** into ProcuraX without pretending that the fictional showcase company owns the reported assets or supplier relationships. Internal transaction tables remain synthetic unless a real business has explicitly provided authorized data.

## Data provenance labels
Use one required enum in storage and UI:
- `PUBLIC_REAL`: an observed public article, filing, commodity series, trade data point or official public record.
- `SYNTHETIC`: generated fictional supplier/PO/inventory/contract/customer data.
- `DERIVED`: a value calculated from other records (e.g., days of cover, evidence confidence, model prediction).
- `ILLUSTRATIVE`: a hard-coded visual/sample value only. This class must not be presented as current or evaluated output.

Every dashboard, card, graph, case and article row should surface the appropriate label. Add a global scenario banner: `Illustrative ApexDrive case · synthetic internal operations · real public sources where available`.

## Sources for the initial PoC

| Provider | Purpose | Credential | Important limitation |
|---|---|---|---|
| GDELT DOC API | Global news metadata and source URLs for shutdowns, shortages, strikes, weather, ports, restrictions | No key for the basic DOC API | GDELT result is a candidate article, not verified supplier exposure; sentiment/event classification may need to be computed |
| Marketaux | Market/financial news + identified entity sentiment | `MARKETAUX_API_TOKEN` | Provider plan limits and redistribution permissions must be rechecked |
| Alpha Vantage News Sentiment | Financial-market news and sentiment/ticker/topic metadata | `ALPHA_VANTAGE_API_KEY` | Rate limits/entitlement depend on provider plan; use budget carefully |
| NewsData.io | Supplementary general/news feed | `NEWSDATA_API_KEY` | Free-plan delay/quota may make it unsuitable for real-time claims |
| SEC EDGAR | Official U.S. corporate filings/submissions | No API key for public data APIs; `SEC_USER_AGENT` should identify app + contact | Company coverage and freshness are limited by filings; not an operational alert feed |
| World Bank commodity prices | Historical input-cost proxy series | Public downloadable files | Mostly periodic/historical series, not intraday data |
| Optional FRED / NOAA / India TRADESTAT / UN Comtrade | Context for macro pressure, weather, trade concentration | May require free key, registration or portal access | Add only when the feature is scoped and tested |

Official docs: GDELT https://www.gdeltproject.org/data.html ; Marketaux https://www.marketaux.com/documentation ; Alpha Vantage https://www.alphavantage.co/documentation/ ; NewsData.io https://newsdata.io/documentation ; SEC EDGAR https://www.sec.gov/edgar/sec-api-documentation ; World Bank commodities https://www.worldbank.org/en/research/commodity-markets . Verify current provider docs, free-tier limits and terms at implementation time. Do not hard-code marketing-plan quotas.

## Keys / configuration
- Keep credentials in local `.env` or a platform secret store only.
- Never expose API tokens through React/Vite, client-side fetches, `VITE_*` variables, response payloads or log lines.
- Keep the isolated reference connectors under `integrations/real_data_connectors/` for smoke tests; integrate them into `backend/app/services/signals/providers/` behind adapters once contracts are reviewed.
- Have one central backend config model for provider settings, feature flags, timeouts, quotas and enable/disable switches. Avoid two disconnected `.env` sources after integration.
- Add a Settings > Data Providers UI that reveals only key configured/not configured, last fetch, status and quota state, never the secret value.

## Normalized provider interface
Define a provider protocol/interface such as:
- `provider_name`
- `is_configured()`
- `fetch(query, start_at, end_at, limit) -> ProviderFetchResult`
- `normalize(raw_item) -> NormalizedSignal`
- `health_check() -> ProviderHealth`

Return a typed result including `status`: `success`, `partial_success`, `no_results`, `not_configured`, `quota_exceeded`, `rate_limited`, `provider_unavailable`, `invalid_response`, or `error`. Include provider, fetched_at_utc, result_count, normalized_count, error_code, retry_after when present and request/case correlation ID. Do not raise away the provider state so the UI cannot display it.

## Canonical signal schema
At minimum:
- IDs: `signal_id`, `provider`, `provider_article_id`, `canonical_url`, `content_hash`.
- Content: `title`, `description_or_snippet`, `publisher`, `language`, optional permitted snippet.
- Times: `published_at_utc`, `retrieved_at_utc`, optional `updated_at_utc`.
- Query/metadata: `search_query`, `raw_payload_path`, `schema_version`, `ingestion_status`.
- Entities: `entity_name`, `entity_type`, `entity_symbol`, `entity_match_score`, `mapped_supplier_id`, `mapped_material_id`, `mapped_region_or_facility`, `mapping_method`, `mapping_confidence`.
- Sentiment: `provider_sentiment_score`, `provider_sentiment_label` if provided, `our_sentiment_score`, `our_sentiment_label`, `sentiment_model`, `sentiment_model_version`.
- Event/risk: `event_type`, `event_severity`, `source_credibility`, `recency_score`, `relevance_score`, `cross_source_agreement`, `contradiction_flag`, `evidence_confidence`, `procurement_exposure_match`, `review_status`.

Preserve provider score unchanged; store derived internal score separately. The source article's negative tone is not equivalent to a disruption event or risk score.

## Query and taxonomy defaults
Useful terms (configure rather than hard-code to a single entity):
- `supplier shutdown`, `factory closure`, `supplier bankruptcy`, `capacity reduction`
- `raw material shortage`, `component shortage`, `semiconductor shortage`, `automotive supply chain`
- `port congestion`, `port closure`, `shipping delay`, `container rates`
- `labour strike`, `labor strike`, `export restriction`, `sanctions`, `earthquake`, `flood`, `cyclone`
- raw materials relevant to the synthetic components (e.g., copper, aluminium, nickel, lithium, resin, chips)

Event types: `supplier_shutdown`, `capacity_reduction`, `raw_material_shortage`, `component_shortage`, `quality_issue`, `financial_distress`, `labor_strike`, `port_congestion`, `shipping_delay`, `export_restriction`, `sanctions`, `natural_disaster`, `weather_disruption`, `cyber_incident`, `regulatory_change`, `commodity_price_shock`, `other`, `unknown`.

## Data-quality and reliability rules
- Validate required fields and timestamp parsing. Keep UTC timestamps.
- Canonicalize URLs and deduplicate; keep provider observations when multiple sources mention the same canonical article.
- Do not fetch arbitrary user-provided URLs. Only call approved provider URLs/feed sources (SSRF prevention).
- Use request timeout, bounded retries, backoff/jitter and respect HTTP 429/`Retry-After`. Add caps for manual fetch count and date window.
- Distinguish no result from provider failure and quota exhaustion.
- Save raw public payloads only to ignored local storage when appropriate; commit fixtures, not raw bulk results or secrets.
- Keep source links, timestamps, provider and fetch status visible in Evidence Panel.
- Do not reproduce full article body absent an explicit right to store/display it. Prefer title, provider-returned snippet, metadata and publisher link.
- For SEC requests, use a descriptive User-Agent and follow SEC fair-access guidance.
- Live calls are opt-in smoke tests. CI uses fixture/mock responses and does not spend user's API quota.

## Synthetic-to-real matching policy
The fictional company ApexDrive and `SUP-1047` do not exist in external news. Use `scenario_mapping`/`scenario_rules` only to let a scenario say, for example: “For demo purposes, this generic public signal about a raw material in a configured sourcing region is treated as a candidate signal against SUP-1047.” Display the mapping method and label it as an assumption. Do not use external articles to claim the fictional supplier was actually named or affected.

## Sentiment design
1. Preserve provider sentiment when present.
2. Derive internal polarity/sentiment only as an independent feature with model/version recorded.
3. Independently classify event type, severity, target entity/location, operational relevance and time relevance.
4. Evidence confidence should consider source credibility, recency decay, entity/material/region relevance, source independence and corroboration; penalize duplicate syndicated articles and contradictions.
5. Surface uncertainty and conflicting evidence. A single weak source must not trigger a high-confidence material action.
6. Feed only the derived, evidence-reviewed features into the governed risk-score layer; log the feature snapshot.

## Required provider UI states
Per provider show: status chip + text, last successful fetch, last attempt, freshness, returned items, filtered duplicates, errors/quota state, enable/disable, and manual fetch action for permitted roles. Never show a green “connected” status just because a key exists; make a real, safe health/status check where provider allows it.
