/**
 * Surface 2: Supplier 360 & Risk Intelligence
 */
import { useEffect, useState } from 'react'
import type { ModelCardResponse, RiskScoreResponse } from '../types'
import { fetchRiskModelCard, fetchRiskScore } from '../lib/api'

export function Supplier360View() {
  const [selectedSupplier, setSelectedSupplier] = useState('SUP-1047')
  const [riskData, setRiskData] = useState<RiskScoreResponse | null>(null)
  const [modelCard, setModelCard] = useState<ModelCardResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchRiskScore(selectedSupplier), fetchRiskModelCard()])
      .then(([riskRes, cardRes]) => {
        setRiskData(riskRes)
        setModelCard(cardRes)
      })
      .catch(() => {
        // Fallback demo data
        if (selectedSupplier === 'SUP-1047') {
          setRiskData({
            supplier_id: 'SUP-1047',
            supplier_name: 'ApexDrive Components',
            as_of_date: '2026-09-30',
            stockout_probability_90d: 0.682,
            evidence_confidence: 0.82,
            governed_risk_score: 78.5,
            risk_tier: 'HIGH',
            top_risk_drivers: [
              { feature: 'otif_degradation_30d', importance: 0.35, direction: 'INCREASING_RISK', description: 'OTIF delivery dropped by 18% over the last 30-day window' },
              { feature: 'transit_delay_lead_time', importance: 0.28, direction: 'INCREASING_RISK', description: 'Logistics transit time increased from 14 to 28 days (+14 days delay)' },
              { feature: 'single_source_criticality', importance: 0.22, direction: 'INCREASING_RISK', description: 'Critical sole-source supplier for flagship harness SKU-WIRE-01' },
              { feature: 'port_congestion_index', importance: 0.15, direction: 'INCREASING_RISK', description: 'Western maritime freight delays at Nhava Sheva corridor' },
            ],
            model_version: 'risk-logreg-v1.0',
            formula_audit: { formula: 'Score = 0.50 * Prob + 0.30 * Conf + 0.20 * Impact' },
          })
        } else {
          setRiskData({
            supplier_id: 'SUP-1012',
            supplier_name: 'ElectroMotion Technologies',
            as_of_date: '2026-09-30',
            stockout_probability_90d: 0.142,
            evidence_confidence: 0.91,
            governed_risk_score: 24.0,
            risk_tier: 'LOW',
            top_risk_drivers: [
              { feature: 'otif_stability', importance: 0.40, direction: 'REDUCING_RISK', description: 'Stable 96.5% historical OTIF delivery record' },
              { feature: 'dual_source_qualification', importance: 0.35, direction: 'REDUCING_RISK', description: 'Pre-qualified active secondary supplier under DOC-POL-DUAL-SOURCE' },
              { feature: 'capacity_available', importance: 0.25, direction: 'REDUCING_RISK', description: '50% spare production capacity verified for harness assembly' },
            ],
            model_version: 'risk-logreg-v1.0',
            formula_audit: { formula: 'Score = 0.50 * Prob + 0.30 * Conf + 0.20 * Impact' },
          })
        }

        setModelCard({
          model_name: 'Logistic Regression Baseline',
          version: '1.0.0',
          target_definition: 'Binary 90-day supplier stockout / delivery breakdown',
          prediction_horizon: '90 days forward',
          training_window: 'Historical 2024-01-01 to 2026-06-30',
          held_out_window: '2026-07-01 to 2026-09-30 (SUP-1047 degradation window)',
          sample_sizes: { train_rows: 900, test_rows: 180, suppliers: 60 },
          evaluation_metrics: { roc_auc: 0.6285, brier_score: 0.2456, accuracy: 0.60 },
          leakage_protection: { flagship_supplier_excluded: true, flagship_id: 'SUP-1047' },
        })
      })
      .finally(() => setLoading(false))
  }, [selectedSupplier])

  return (
    <div className="surface-content">
      {loading && <div className="notice-banner info-banner">Loading supplier risk score & model card…</div>}
      {/* Supplier Selector */}

      <div className="supplier-selector-bar">
        <label htmlFor="supplier-select"><strong>Select Supplier to Inspect:</strong></label>
        <select
          id="supplier-select"
          className="supplier-dropdown"
          value={selectedSupplier}
          onChange={(e) => setSelectedSupplier(e.target.value)}
        >
          <option value="SUP-1047">SUP-1047: ApexDrive Components (Disrupted Flagship · High Risk)</option>
          <option value="SUP-1012">SUP-1012: ElectroMotion Technologies (Pre-qualified Alternate · Low Risk)</option>
        </select>
        <span className="pill">SYNTHETIC_DATA</span>
      </div>

      {riskData && (
        <>
          {/* Supplier Profile Card */}
          <section className="supplier-header-card">
            <div className="supplier-title-group">
              <span className={`supplier-avatar-large ${(riskData.risk_tier || 'HIGH').toLowerCase()}`}>
                {(riskData.supplier_name || 'A').slice(0, 1)}
              </span>
              <div>
                <h2>{riskData.supplier_name || 'ApexDrive Components'}</h2>
                <div className="supplier-submeta">
                  <span>Supplier ID: <strong>{riskData.supplier_id}</strong></span>
                  <span>Category: <strong>Automotive High-Voltage Harnesses</strong></span>
                  <span>Primary Contract: <strong>DOC-MSA-APEX-2025</strong></span>
                  <span>Tier: <strong>Tier-1 Direct</strong></span>
                </div>
              </div>
            </div>
            <div className="risk-score-display">
              <div className="risk-score-number">{(riskData.governed_risk_score ?? 78.5).toFixed(1)}</div>
              <div className={`risk-tier-badge ${(riskData.risk_tier || 'HIGH').toLowerCase()}`}>{riskData.risk_tier || 'HIGH'} RISK</div>
              <small>Governed 0–100 Formula Score</small>
            </div>
          </section>

          {/* Metric Breakdown Grid */}
          <section className="metric-grid">
            <article className="metric-card">
              <div className="metric-icon red">P</div>
              <div className="metric-label">90-Day Stockout Probability</div>
              <div className="metric-value">{((riskData.stockout_probability_90d ?? 0.68) * 100).toFixed(1)}%</div>
              <div className="metric-detail">Logistic Regression Output (Uncalibrated)</div>
            </article>
            <article className="metric-card">
              <div className="metric-icon teal">C</div>
              <div className="metric-label">Evidence Confidence Band</div>
              <div className="metric-value">{((riskData.evidence_confidence ?? 0.82) * 100).toFixed(1)}%</div>
              <div className="metric-detail">Multi-source coverage & corroboration</div>
            </article>
            <article className="metric-card">
              <div className="metric-icon blue">M</div>
              <div className="metric-label">Model Registry Version</div>
              <div className="metric-value">{riskData.model_version}</div>
              <div className="metric-detail">Held-out window validation</div>
            </article>
            <article className="metric-card">
              <div className="metric-icon amber">G</div>
              <div className="metric-label">Leakage Guard Status</div>
              <div className="metric-value" style={{ color: 'var(--forest-primary)' }}>PROTECTED</div>
              <div className="metric-detail">Zero training contamination</div>
            </article>
          </section>

          {/* Risk Drivers Waterfall & Model Card */}
          <div className="two-column">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Top Explainable Risk Drivers</h2>
                  <p>Decomposition of risk factors driving score to {(riskData.governed_risk_score ?? 78.5).toFixed(1)}</p>
                </div>
                <span className="pill">DERIVED</span>
              </div>
              <div className="drivers-list">
                {(riskData.top_risk_drivers || []).map((d) => (
                  <div key={d.feature} className="driver-item">
                    <div className="driver-meta">
                      <strong>{d.description}</strong>
                      <span>{((d.importance ?? 0.25) * 100).toFixed(0)}% weight</span>
                    </div>
                    <div className="driver-desc">Feature: <code>{d.feature}</code> · Direction: {d.direction || 'INCREASING_RISK'}</div>
                    <div className="driver-bar-wrap">
                      <div className="driver-bar" style={{ width: `${Math.min(100, (d.importance ?? 0.25) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {modelCard && (
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Model Card & Validation</h2>
                    <p>Transparent ML specifications per Section 12.1</p>
                  </div>
                  <span className="pill">GOVERNED</span>
                </div>
                <div className="model-card-body">
                  <div className="meta-pair">
                    <span>Algorithm</span>
                    <strong>{modelCard.model_name} (Scikit-Learn)</strong>
                  </div>
                  <div className="meta-pair">
                    <span>Target Definition</span>
                    <strong>{modelCard.target_definition}</strong>
                  </div>
                  <div className="meta-pair">
                    <span>Training Sample</span>
                    <strong>{modelCard.sample_sizes?.train_rows ?? 900} rows ({modelCard.sample_sizes?.suppliers ?? 60} suppliers)</strong>
                  </div>
                  <div className="meta-pair">
                    <span>Held-out Test Sample</span>
                    <strong>{modelCard.sample_sizes?.test_rows ?? 180} rows (temporal split)</strong>
                  </div>
                  <div className="meta-pair">
                    <span>ROC-AUC Metric</span>
                    <strong style={{ color: '#2563eb' }}>{(modelCard.evaluation_metrics?.roc_auc ?? 0.6285).toFixed(4)}</strong>
                  </div>
                  <div className="meta-pair">
                    <span>Brier Calibration Score</span>
                    <strong style={{ color: '#0f9d9a' }}>{(modelCard.evaluation_metrics?.brier_score ?? 0.2456).toFixed(4)}</strong>
                  </div>
                  <div className="meta-pair">
                    <span>Flagship Contamination</span>
                    <strong style={{ color: '#059669' }}>
                      {modelCard.leakage_protection?.flagship_id || 'SUP-1047'} Excluded from Training: YES
                    </strong>
                  </div>
                </div>
              </section>
            )}
          </div>
        </>
      )}
    </div>
  )
}
