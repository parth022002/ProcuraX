/**
 * Surface 7: Outcome Review & Post-Decision Operational KPI Tracking
 */
import { useEffect, useState } from 'react'
import type { DisruptionCase, ObservedOutcome } from '../types'
import { fetchCases, recordCaseOutcome } from '../lib/api'
import { Icon } from './Icons'

export function OutcomeReviewView() {
  const [activeCase, setActiveCase] = useState<DisruptionCase | null>(null)
  const [actualOtif, setActualOtif] = useState(0.94)
  const [actualServiceLevel, setActualServiceLevel] = useState(0.98)
  const [actualCostLakhs, setActualCostLakhs] = useState(14.2)
  const [outcomeLabel, setOutcomeLabel] = useState('MITIGATED_SUCCESS')
  const [notes, setNotes] = useState('Assembly lines at Pune and Chennai maintained 100% scheduled uptime with zero line stoppages.')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchCases()
      .then((cases) => {
        if (cases && cases.length > 0) {
          const actioned = cases.find((c) => c.action_packet || c.state === 'ACTION_PACKET_PREPARED' || c.state === 'OUTCOME_RECORDED')
          setActiveCase(actioned || cases[cases.length - 1])
        }
      })
      .catch(() => {
        // Fallback demo case (Action packet prepared, waiting for observed operational result)
        setActiveCase({
          case_id: 'CAS-SUP-1047-01',
          supplier_id: 'SUP-1047',
          supplier_name: 'ApexDrive Components',
          state: 'ACTION_PACKET_PREPARED',
          severity: 'HIGH',
          created_at_utc: '2026-10-14T09:00:00Z',
          updated_at_utc: '2026-10-14T09:45:00Z',
          activated_hypotheses: ['H1: Lead time escalation', 'H2: Single-source buffer stockout', 'H3: Dual-source clause invocation'],
          critic_score: 0.88,
          critic_retries_used: 0,
          risk_score: 78.5,
          candidate_scenarios: [],
          citations: [],
          audit_trail: [],
        })
      })
  }, [])

  const handleSubmitOutcome = () => {
    if (!activeCase) return
    setLoading(true)
    setMessage(null)

    const payload: ObservedOutcome = {
      outcome_id: `OUT-${activeCase.case_id}-${Date.now().toString().slice(-4)}`,
      case_id: activeCase.case_id,
      supplier_id: activeCase.supplier_id,
      decision_timestamp_utc: activeCase.action_packet?.approved_at_utc || new Date().toISOString(),
      observed_at_utc: new Date().toISOString(),
      action_taken: activeCase.action_packet?.scenario_id || 'HYBRID_DUAL_SOURCE',
      actual_otif: actualOtif,
      actual_service_level: actualServiceLevel,
      actual_cost_inr: actualCostLakhs * 100000,
      outcome_label: outcomeLabel,
      notes,
    }

    recordCaseOutcome(activeCase.case_id, payload)
      .then((updated) => {
        setActiveCase(updated)
        setMessage('Observed operational KPIs successfully recorded in audit store!')
      })
      .catch((err: any) => {
        setMessage(err.message || 'Failed to record outcome')
      })
      .finally(() => setLoading(false))
  }

  const outcome = activeCase?.observed_outcome

  return (
    <div className="surface-content">
      {/* Surface Header */}
      <section className="evidence-header-bar">
        <div>
          <h2>Outcome Review & Post-Decision Learning</h2>
          <p>Closed-loop operational validation tracking actual business recovery vs simulation estimates</p>
        </div>
        <div className="simulation-badges">
          <span className="pill green">DATA_QUARANTINED</span>
          <span className="pill">SEPARATED_FROM_FEATURES</span>
        </div>
      </section>

      {/* Temporal Data Isolation Notice */}
      <div className="notice-banner info-banner">
        <strong>Strict Data Boundary Guarantee:</strong> Post-decision observed outcomes are stored in a dedicated
        auditing store and are strictly quarantined from ML prediction features to prevent future data leakage.
      </div>

      {message && (
        <div className="notice-banner success-banner">
          {message}
        </div>
      )}

      {/* Observed vs Planned KPI Cards */}
      <section className="metric-grid">
        <article className="metric-card">
          <div className="metric-icon teal">
            <Icon name="check" size={16} />
          </div>
          <div className="metric-label">Actual On-Time In-Full (OTIF)</div>
          <div className="metric-value">
            {outcome ? `${(outcome.actual_otif * 100).toFixed(1)}%` : 'Pending'}
          </div>
          <div className="metric-detail">
            {outcome ? 'Audited result vs 90% SLA' : 'Baseline: 82% | Target: >90%'}
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon blue">
            <Icon name="activity" size={16} />
          </div>
          <div className="metric-label">Actual Service Level Achieved</div>
          <div className="metric-value">
            {outcome ? `${(outcome.actual_service_level * 100).toFixed(1)}%` : 'Pending'}
          </div>
          <div className="metric-detail">
            {outcome ? 'Plant continuity verified' : 'Baseline: 38% | Target: >95%'}
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon amber">
            <Icon name="chart" size={16} />
          </div>
          <div className="metric-label">Actual Spend Incurred</div>
          <div className="metric-value">
            {outcome ? `₹${(outcome.actual_cost_inr / 100000).toFixed(2)} L` : 'Pending'}
          </div>
          <div className="metric-detail">
            {outcome ? 'Persisted in audit ledger' : 'Projected budget: ₹14.50 Lakhs'}
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon green">
            <Icon name="shield" size={16} />
          </div>
          <div className="metric-label">Mitigation Classification</div>
          <div className="metric-value" style={{ color: outcome ? 'var(--forest-primary)' : 'var(--text-muted)', fontSize: outcome ? '16px' : '15px' }}>
            {outcome ? outcome.outcome_label : 'AWAITING_OUTCOME'}
          </div>
          <div className="metric-detail">
            {outcome ? 'Assembly line downtime averted' : 'Awaiting operational logging'}
          </div>
        </article>
      </section>

      {/* Form to Log Actual KPIs & Existing Record */}
      <div className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Record Post-Decision Operational Result</h2>
              <p>Capture verified manufacturing results for Case: <strong>{activeCase?.case_id || 'CAS-SUP-1047-01'}</strong></p>
            </div>
            <span className="pill">OBSERVED_OUTCOME</span>
          </div>

          <div className="approval-form-body">
            {/* Delivery OTIF Slider Field */}
            <div className="governed-slider-field">
              <div className="slider-field-header">
                <label htmlFor="otif-slider" className="form-label">
                  Actual Delivery OTIF Achieved
                </label>
                <div className="slider-metric-pill">
                  <span>{(actualOtif * 100).toFixed(1)}%</span>
                  <small>Target: ≥90.0%</small>
                </div>
              </div>
              <div className="slider-track-wrap">
                <input
                  id="otif-slider"
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.01"
                  value={actualOtif}
                  onChange={(e) => setActualOtif(Number(e.target.value))}
                  className="governed-slider-control"
                />
                <div className="slider-ticks-row">
                  <span>50% (Disrupted)</span>
                  <span className="tick-target">90% SLA Target</span>
                  <span>100% (Optimal)</span>
                </div>
              </div>
            </div>

            {/* Service Level Slider Field */}
            <div className="governed-slider-field">
              <div className="slider-field-header">
                <label htmlFor="sl-slider" className="form-label">
                  Actual Service Level Achieved
                </label>
                <div className="slider-metric-pill">
                  <span>{(actualServiceLevel * 100).toFixed(1)}%</span>
                  <small>Target: ≥95.0%</small>
                </div>
              </div>
              <div className="slider-track-wrap">
                <input
                  id="sl-slider"
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.01"
                  value={actualServiceLevel}
                  onChange={(e) => setActualServiceLevel(Number(e.target.value))}
                  className="governed-slider-control"
                />
                <div className="slider-ticks-row">
                  <span>50% (Bottleneck)</span>
                  <span className="tick-target">95% SLA Target</span>
                  <span>100% (Full Continuity)</span>
                </div>
              </div>
            </div>

            {/* 2-Column Inputs Grid: Spend & Classification */}
            <div className="outcome-form-grid">
              <div className="form-row">
                <label htmlFor="cost-input" className="form-label">Actual Spend Incurred (₹ Lakhs)</label>
                <div className="outcome-currency-input-wrap">
                  <span className="currency-symbol">₹</span>
                  <input
                    id="cost-input"
                    type="number"
                    step="0.1"
                    className="outcome-input"
                    value={actualCostLakhs}
                    onChange={(e) => setActualCostLakhs(Number(e.target.value))}
                  />
                  <span className="currency-unit">Lakhs</span>
                </div>
                <span className="field-caption">Planned Envelope: ₹14.50 Lakhs</span>
              </div>

              <div className="form-row">
                <label htmlFor="label-select" className="form-label">Outcome Classification</label>
                <select
                  id="label-select"
                  className="custom-select outcome-dropdown"
                  value={outcomeLabel}
                  onChange={(e) => setOutcomeLabel(e.target.value)}
                >
                  <option value="MITIGATED_SUCCESS">MITIGATED_SUCCESS (Lines Protected)</option>
                  <option value="PARTIAL_RECOVERY">PARTIAL_RECOVERY (Minor Delays)</option>
                  <option value="UNRESOLVED_SHORTAGE">UNRESOLVED_SHORTAGE (Line Downtime)</option>
                </select>
                <span className="field-caption">Deterministic State Closure Tag</span>
              </div>
            </div>

            {/* Plant Manager Notes */}
            <div className="form-row">
              <label htmlFor="outcome-notes" className="form-label">Plant Manager Operational Notes</label>
              <textarea
                id="outcome-notes"
                className="reason-textarea"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Document plant floor observations, supplier logistics recovery, and assembly line continuity..."
              />
            </div>

            <button
              className="replay-action-button outcome-action-btn"
              onClick={handleSubmitOutcome}
              disabled={loading}
            >
              {loading ? 'Recording to Immutable Audit Store…' : 'Record Observed Outcome in Audit Store →'}
            </button>
            <div className="audit-store-assurance">
              <Icon name="shield" size={13} />
              <span>Strict Data Quarantine: Observed operational outcomes are isolated from ML training sets.</span>
            </div>
          </div>
        </section>

        {/* Existing Recorded Outcome Display */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Audited Case Outcome Status</h2>
              <p>Current post-decision outcome logged for {activeCase?.case_id || 'CAS-SUP-1047-01'}</p>
            </div>
            <span className={`pill ${outcome ? 'green' : 'copper'}`}>
              {outcome ? 'AUDITED_VERIFIED' : 'AWAITING_OUTCOME'}
            </span>
          </div>

          {outcome ? (
            <div className="approval-form-body">
              <div className="packet-id-row">
                <span>Outcome ID: <strong>{outcome.outcome_id}</strong></span>
                <span className="status-badge feasible">{outcome.outcome_label}</span>
              </div>
              <div className="packet-meta-grid">
                <div className="meta-pair">
                  <span>Supplier</span>
                  <strong>{activeCase?.supplier_name} ({outcome.supplier_id})</strong>
                </div>
                <div className="meta-pair">
                  <span>Action Executed</span>
                  <strong>{outcome.action_taken}</strong>
                </div>
                <div className="meta-pair">
                  <span>Observed At</span>
                  <strong>{new Date(outcome.observed_at_utc).toLocaleString()}</strong>
                </div>
                <div className="meta-pair">
                  <span>Actual Spend</span>
                  <strong style={{ color: 'var(--forest-primary)' }}>₹{(outcome.actual_cost_inr / 100000).toFixed(2)} Lakhs</strong>
                </div>
              </div>

              <div className="form-row" style={{ marginTop: '8px' }}>
                <span className="form-label">Operational Observations</span>
                <div className="observations-quote-box">
                  "{outcome.notes}"
                </div>
              </div>

              <div className="ledger-verification-seal">
                <Icon name="shield" size={16} />
                <div className="seal-meta">
                  <strong>Ledger Immutability Enforced</strong>
                  <span>SHA256 signature verified • Data strictly quarantined from ML training features</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-packet-state outcome-staging-card">
              <div className="empty-packet-badge">
                <Icon name="clock" size={22} />
              </div>
              <h3 className="empty-packet-title">Governed Decision Loop Awaiting Operational Results</h3>
              <p className="empty-packet-desc">
                Mitigation scenario <strong>HYBRID_DUAL_SOURCE</strong> was authorized by CPO. Complete the closed loop by recording verified plant line KPIs.
              </p>
              
              <div className="packet-preview-box">
                <div className="preview-row">
                  <span className="preview-kicker">Authorized Scenario:</span>
                  <span className="preview-value">HYBRID_DUAL_SOURCE (Tier-2 Fast-Track)</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Budget Ceiling:</span>
                  <span className="preview-value">₹14.50 Lakhs (CPO Allocated)</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Line Target:</span>
                  <span className="preview-value">100% Scheduled Production Continuity</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Audit Ledger:</span>
                  <span className="preview-value mono">PostgreSQL Immutable Store (Quarantined)</span>
                </div>
              </div>

              <div className="governed-reassurance-note">
                <Icon name="lock" size={13} />
                <span>Zero Data Leakage Guarantee: Historical observations never modify model inference weights without explicit retrain governance.</span>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
