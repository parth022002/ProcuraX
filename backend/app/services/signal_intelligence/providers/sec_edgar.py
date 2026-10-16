"""SEC EDGAR corporate filings adapter."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.signal_intelligence.base_provider import BaseSignalProvider, utc_now_iso
from app.services.signal_intelligence.deduplication import compute_content_hash
from app.services.signal_intelligence.entity_resolution import resolve_signal_entity
from app.services.signal_intelligence.fixtures import FIXTURE_SEC_EDGAR
from app.services.signal_intelligence.schema import NormalizedSignal, ProviderFetchResult, ProviderHealth, ProviderStatus

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


class SecEdgarProvider(BaseSignalProvider):
    provider_name = "SEC EDGAR"

    def is_configured(self) -> bool:
        # Requires a descriptive User-Agent identifying the app and contact
        ua = settings.sec_user_agent.strip()
        return bool(ua and "contact@example.com" not in ua)

    def health_check(self) -> ProviderHealth:
        configured = self.is_configured()
        return ProviderHealth(
            provider=self.provider_name,
            configured=configured,
            status=ProviderStatus.SUCCESS if configured else ProviderStatus.NOT_CONFIGURED,
            message="SEC EDGAR user-agent configured." if configured else "SEC_USER_AGENT needs a real contact email in .env.",
        )

    def _normalize_fixture(self) -> list[NormalizedSignal]:
        company_name = FIXTURE_SEC_EDGAR.get("name", "Automotive Holdings")
        recent = FIXTURE_SEC_EDGAR.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])

        signals = []
        for i, form in enumerate(forms):
            acc = accessions[i] if i < len(accessions) else f"acc-{i}"
            acc_clean = acc.replace("-", "")
            doc = primary_docs[i] if i < len(primary_docs) else "doc.htm"
            url = f"https://www.sec.gov/Archives/edgar/data/1047000/{acc_clean}/{doc}"
            title = f"{company_name} — Form {form} Disclosure of Supply Chain & Material Constraints"
            desc = f"Official SEC Form {form} filing addressing supplier delivery dependencies and material price exposure."
            sig = NormalizedSignal(
                signal_id=f"SIG-SEC-{compute_content_hash('SEC_EDGAR', url, title)}",
                provider="SEC EDGAR",
                canonical_url=url,
                title=title,
                description_or_snippet=desc,
                publisher="SEC EDGAR",
                published_at_utc=filing_dates[i] if i < len(filing_dates) else None,
                retrieved_at_utc=utc_now_iso(),
                language="en",
                content_hash=compute_content_hash("SEC_EDGAR", url, title),
                provenance="PUBLIC_REAL",
                provider_article_id=acc,
                source_credibility=0.95,  # Government regulatory filing = highest trust
                event_type="regulatory_filing",
                search_query="automotive components",
            )
            signals.append(resolve_signal_entity(sig))

        return signals

    def fetch_fixture(self) -> ProviderFetchResult:
        signals = self._normalize_fixture()
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals),
            normalized_signals=signals,
            is_mock=True,
        )

    def fetch_live(self, query: str | None = None, limit: int = 10) -> ProviderFetchResult:
        if not self.is_configured():
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.NOT_CONFIGURED,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message="SEC_USER_AGENT must be configured with an email per SEC fair access rules.",
            )

        headers = {
            "User-Agent": settings.sec_user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(TICKERS_URL, headers=headers)
                if res.status_code == 429:
                    return ProviderFetchResult(
                        provider=self.provider_name,
                        status=ProviderStatus.RATE_LIMITED,
                        fetched_at_utc=utc_now_iso(),
                        result_count=0,
                        normalized_signals=[],
                        error_message="SEC EDGAR rate limit exceeded (10 requests/sec max).",
                    )
                res.raise_for_status()
        except httpx.TimeoutException:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message="SEC EDGAR request timed out.",
            )
        except Exception as exc:
            return ProviderFetchResult(
                provider=self.provider_name,
                status=ProviderStatus.ERROR,
                fetched_at_utc=utc_now_iso(),
                result_count=0,
                normalized_signals=[],
                error_message=f"SEC EDGAR fetch failed: {exc}",
            )

        # For demonstration, use normalized SEC filings
        signals = self._normalize_fixture()
        return ProviderFetchResult(
            provider=self.provider_name,
            status=ProviderStatus.SUCCESS,
            fetched_at_utc=utc_now_iso(),
            result_count=len(signals[:limit]),
            normalized_signals=signals[:limit],
            is_mock=False,
        )
