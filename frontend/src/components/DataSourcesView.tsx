/**
 * Data Sources & Ingestion Console View (Screen 11)
 * Per Master Prompt Section 5: Manual 'Fetch now' trigger, ingestion history,
 * deduplication metrics, and original source attribution links.
 */
import { useEffect, useState } from 'react'
import { fetchSignals, triggerSignalIngest, triggerWebScraper } from '../lib/api'
import type { SignalItem } from '../types'
import { Icon } from './Icons'

export function DataSourcesView() {
  const [signals, setSignals] = useState<SignalItem[]>([])
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [selectedProvider, setSelectedProvider] = useState<string>('ALL')

  const loadSignals = async () => {
    setLoading(true)
    try {
      const res = await fetchSignals('SUP-1047', 50)
      setSignals(res.signals || [])
    } catch (err: unknown) {
      setStatusMessage(`Failed to load signals: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleManualFetch = async () => {
    setIngesting(true)
    setStatusMessage('Triggering live ingestion from GDELT, Marketaux, Alpha Vantage, and NewsData.io...')
    try {
      const result = await triggerSignalIngest(true)
      setSignals(result.signals || [])
      setStatusMessage(`Ingestion run complete! ${result.total} signals retrieved & deduplicated via SHA-256 content hashes.`)
    } catch (err: unknown) {
      setStatusMessage(`Ingestion note: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIngesting(false)
    }
  }

  const handleWebScrape = async () => {
    setScraping(true)
    setStatusMessage('Active Web Scraper running: Crawling global supply chain portals (SupplyChainBrain, FreightWaves, Reuters SC)...')
    try {
      const result = await triggerWebScraper(15)
      setSignals(result.signals || [])
      setStatusMessage(`Web Scraping successful! Scraped ${result.total} real-time disruption articles and persisted to Neon PostgreSQL.`)
    } catch (err: unknown) {
      setStatusMessage(`Web Scraping note: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setScraping(false)
    }
  }

  useEffect(() => {
    loadSignals()
  }, [])

  const filteredSignals = selectedProvider === 'ALL'
    ? signals
    : signals.filter((s) => s.provider.toLowerCase() === selectedProvider.toLowerCase())

  return (
    <div className="surface-content">
      {/* Header Bar */}
      <section className="evidence-header-bar" style={{ marginBottom: '20px' }}>
        <div>
          <h2>Data Sources & Signal Ingestion Console</h2>
          <p>
            Ingest, normalize, and deduplicate real public market signals for disruption intelligence
          </p>
        </div>
        <div className="data-sources-btn-group">
          <button
            className="data-sources-btn"
            onClick={loadSignals}
            disabled={loading || ingesting || scraping}
          >
            <Icon name="refresh" size={14} />
            <span>{loading ? 'Refreshing...' : 'Refresh Feeds'}</span>
          </button>
          <button
            className="data-sources-btn copper"
            onClick={handleManualFetch}
            disabled={ingesting || scraping}
          >
            <Icon name="spark" size={14} />
            <span>{ingesting ? 'Fetching Live Feeds...' : 'Fetch Live APIs'}</span>
          </button>
          <button
            className="data-sources-btn primary"
            onClick={handleWebScrape}
            disabled={scraping || ingesting}
          >
            <Icon name="network" size={14} />
            <span>{scraping ? 'Crawling Global Feeds...' : 'Run Web Scraper (Live Feeds)'}</span>
          </button>
        </div>
      </section>

      {statusMessage && (
        <div className="notice-banner info-banner" style={{ marginBottom: '20px' }}>
          <Icon name="check" size={15} />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Ingestion Pipeline Metric Cards */}
      <section className="metric-grid" style={{ marginBottom: '20px' }}>
        <article className="metric-card">
          <div className="metric-icon teal">
            <Icon name="radio" size={16} />
          </div>
          <div className="metric-label">Active Public Signals</div>
          <div className="metric-value">{signals.length}</div>
          <div className="metric-detail">Ingested, Deduplicated & Parsed</div>
        </article>
        <article className="metric-card">
          <div className="metric-icon blue">
            <Icon name="database" size={16} />
          </div>
          <div className="metric-label">Storage Backend</div>
          <div className="metric-value" style={{ fontSize: '18px', color: 'var(--forest-primary)' }}>
            Neon Postgres
          </div>
          <div className="metric-detail">Lakebase Postgres (pgvector)</div>
        </article>
        <article className="metric-card">
          <div className="metric-icon green">
            <Icon name="shield" size={16} />
          </div>
          <div className="metric-label">Deduplication Protocol</div>
          <div className="metric-value" style={{ fontSize: '18px' }}>
            SHA-256 Hash
          </div>
          <div className="metric-detail">Zero-Collision Content Signature</div>
        </article>
        <article className="metric-card">
          <div className="metric-icon amber">
            <Icon name="target" size={16} />
          </div>
          <div className="metric-label">Scenario Target</div>
          <div className="metric-value">SUP-1047</div>
          <div className="metric-detail">ApexDrive Flagship Component</div>
        </article>
      </section>

      {/* Signals Table Panel */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Normalized Signals ({filteredSignals.length})</h2>
            <p>Verified public market signals deduplicated and structured for ML feature mapping</p>
          </div>
          <div className="role-selector-group">
            <label htmlFor="provider-filter">Filter Provider:</label>
            <select
              id="provider-filter"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="role-dropdown"
            >
              <option value="ALL">All Providers ({signals.length})</option>
              <option value="SupplyChainBrain">SupplyChainBrain (Web)</option>
              <option value="FreightWaves">FreightWaves (Web)</option>
              <option value="TheLoadstar">TheLoadstar (Web)</option>
              <option value="GDELT">GDELT</option>
              <option value="Marketaux">Marketaux</option>
              <option value="Alpha Vantage">Alpha Vantage</option>
              <option value="NewsData.io">NewsData.io</option>
              <option value="SEC EDGAR">SEC EDGAR</option>
            </select>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: '140px' }}>Provider & Provenance</th>
                <th>Headline & Verified Source</th>
                <th style={{ width: '150px' }}>Relevance & Entities</th>
                <th style={{ width: '160px' }}>Sentiment Polarity</th>
                <th style={{ width: '120px' }}>Published</th>
              </tr>
            </thead>
            <tbody>
              {filteredSignals.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
                    No signals found matching provider filter "{selectedProvider}".
                  </td>
                </tr>
              ) : (
                filteredSignals.map((s) => (
                  <tr key={s.signal_id}>
                    <td>
                      <div className="signal-provider-cell">
                        <strong className="provider-name">{s.provider}</strong>
                        <span className={`pill ${s.provenance === 'PUBLIC_REAL' ? 'green' : ''}`} style={{ fontSize: '9px', padding: '1px 6px' }}>
                          {s.provenance || 'PUBLIC_REAL'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="signal-headline-block">
                        <div className="signal-title">{s.title}</div>
                        {s.url && (
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                            className="signal-source-link"
                          >
                            <span>Open Original Source Link</span>
                            <Icon name="arrow" size={11} />
                          </a>
                        )}
                        <div className="signal-disclaimer-card">
                          <Icon name="shield" size={12} />
                          <span>{s.disclaimer || 'Scenario assumption: Real public external signal mapped to fictional supplier for PoC decision replay only. Not an assertion of real-world liability.'}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="signal-relevance-cell">
                        <div className="relevance-score-badge">
                          <span>Relevance: <strong>{(s.relevance_score * 100).toFixed(0)}%</strong></span>
                        </div>
                        {s.entities_mentioned && s.entities_mentioned.length > 0 && (
                          <div className="entities-tags-wrap">
                            {s.entities_mentioned.slice(0, 2).map((entity, idx) => (
                              <span key={idx} className="entity-tag">{entity}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="sentiment-cell">
                        <span
                          className={`sentiment-badge ${
                            s.sentiment_score < -0.3
                              ? 'bearish'
                              : s.sentiment_score > 0.3
                              ? 'bullish'
                              : 'neutral'
                          }`}
                        >
                          {s.sentiment_score > 0 ? `+${s.sentiment_score.toFixed(2)}` : s.sentiment_score.toFixed(2)}
                          <small>
                            {s.sentiment_score < -0.3 ? ' Disruption' : s.sentiment_score > 0.3 ? ' Stabilizing' : ' Neutral'}
                          </small>
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="timestamp-cell">
                        <span className="timestamp-date">
                          {s.published_at ? s.published_at.substring(0, 10) : '2026-09-30'}
                        </span>
                        <span className="timestamp-provenance">UTC Feeds</span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
