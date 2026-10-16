from __future__ import annotations

import os
import requests
from common import request_json, save_csv, save_json

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def main() -> None:
    agent = os.getenv("SEC_USER_AGENT", "ProcuraXResearch contact@example.com").strip()
    if "contact@example.com" in agent:
        print("[SEC] Warning: replace SEC_USER_AGENT in .env with an app name and real contact email.")
    headers = {"User-Agent": agent, "Accept-Encoding": "gzip, deflate", "Host": "www.sec.gov"}
    tickers = [x.strip().upper() for x in os.getenv("SEC_TICKERS", "AAPL,TSLA,TM").split(",") if x.strip()]
    company_map = request_json(TICKERS_URL, headers=headers)
    save_json("sec_company_tickers", company_map)
    lookup = {}
    values = company_map.values() if isinstance(company_map, dict) else []
    for item in values:
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker", "")).upper()
        if ticker:
            lookup[ticker] = {"cik": str(item.get("cik_str", "")).zfill(10), "title": item.get("title")}
    rows = []
    for ticker in tickers:
        company = lookup.get(ticker)
        if not company:
            print(f"[SEC] ticker {ticker} not found in SEC company ticker list; skipping (not all non-US companies are covered).")
            continue
        # SEC fair-access guidance asks for a descriptive User-Agent and reasonable request rates.
        url = SUBMISSIONS_URL.format(cik=company["cik"])
        data = request_json(url, headers={"User-Agent": agent, "Accept-Encoding": "gzip, deflate"})
        save_json(f"sec_submissions_{ticker.lower()}", data)
        recent = (data.get("filings", {}).get("recent", {}) if isinstance(data, dict) else {})
        forms = recent.get("form", [])
        accession = recent.get("accessionNumber", [])
        filed = recent.get("filingDate", [])
        primary = recent.get("primaryDocument", [])
        report_dates = recent.get("reportDate", [])
        for i, form in enumerate(forms[:100]):
            acc = accession[i] if i < len(accession) else ""
            acc_clean = acc.replace("-", "")
            document = primary[i] if i < len(primary) else ""
            cik_nozero = str(int(company["cik"]))
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_nozero}/{acc_clean}/{document}" if acc and document else None
            rows.append({
                "provider": "SEC EDGAR", "ticker": ticker, "company_name": data.get("name", company.get("title")),
                "form": form, "filing_date": filed[i] if i < len(filed) else None,
                "report_date": report_dates[i] if i < len(report_dates) else None,
                "accession_number": acc, "primary_document": document, "canonical_url": filing_url,
                "description_or_snippet": "SEC filing metadata; review the primary filing for disclosed supply-chain risks.",
            })
        requests_pause = 0.15
        import time
        time.sleep(requests_pause)
    csv_path = save_csv("sec_edgar_recent_filings", rows)
    print(f"SEC EDGAR: {len(rows)} recent filing metadata rows. CSV: {csv_path}")


if __name__ == "__main__":
    main()
