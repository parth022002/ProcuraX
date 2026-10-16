/**
 * Surface 6: Human Approval Workbench & Governed Decision Loop
 */
import { useEffect, useState } from 'react'
import type { DisruptionCase, HumanApprovalAction } from '../types'
import { approveCase, fetchCases, runGovernedCase } from '../lib/api'
import { Icon } from './Icons'

export function ApprovalWorkbenchView({ initialScenarioId = 'SCN-D' }: { initialScenarioId?: string }) {
  const [activeCase, setActiveCase] = useState<DisruptionCase | null>(null)
  const [actorRole, setActorRole] = useState<'SUPPLY_CHAIN_PLANNER' | 'PROCUREMENT_MANAGER' | 'CATEGORY_DIRECTOR' | 'CPO'>('CPO')
  const [actorId, setActorId] = useState('USR-CPO-01')
  const [approvalReason, setApprovalReason] = useState('Approved optimal dual-sourcing ramp to safeguard Pune and Chennai assembly lines.')
  const [forceCriticFailure, setForceCriticFailure] = useState(false)
  const [selectedScenarioId, setSelectedScenarioId] = useState(initialScenarioId)
  const [loading, setLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (initialScenarioId) {
      setSelectedScenarioId(initialScenarioId)
    }
  }, [initialScenarioId])

  // Fetch or initiate demo case
  const executePipeline = (forceFail = false) => {
    setLoading(true)
    setActionError(null)
    setActionSuccess(null)
    runGovernedCase('SUP-1047', 14.0, forceFail)
      .then((c) => {
        setActiveCase(c)
        if (c.state === 'ESCALATED_TO_HUMAN') {
          setActionError('Critic evaluation failed after 1 retry: escalated to human review per Section 17.2.')
        } else {
          setActionSuccess(`Case ${c.case_id} advanced to Approval Workbench; ready for review.`)
        }
      })
      .catch((err: any) => {
        setActionError(err.message || 'Pipeline execution failed')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setLoading(true)
    fetchCases()
      .then((cases) => {
        if (cases && cases.length > 0) {
          setActiveCase(cases[cases.length - 1])
        }
      })
      .catch((err: any) => {
        // Read-only mode on mount: do NOT trigger consequential decision runs automatically
        console.warn('Could not load historical cases:', err.message)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleAction = (action: HumanApprovalAction) => {
    if (!activeCase) return
    setLoading(true)
    setActionError(null)
    setActionSuccess(null)

    const payload = {
      action,
      actor_id: actorId,
      actor_role: actorRole,
      reason: approvalReason,
      idempotency_key: `IDEM-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      selected_scenario_id: selectedScenarioId,
      modified_allocations: action === 'MODIFY' ? { electro_motion_share: 0.30, apex_share: 0.70 } : undefined,
    }

    approveCase(activeCase.case_id, payload)
      .then((updated) => {
        setActiveCase(updated)
        setActionSuccess(`Action ${action} successfully processed. State: ${updated.state}.`)
      })
      .catch((err: any) => {
        setActionError(err.message || 'Action failed')
      })
      .finally(() => setLoading(false))
  }

  const scenarioSpends: Record<string, number> = {
    'SCN-A': 0,
    'SCN-B': 12400000, // ₹1.24 Cr
    'SCN-C': 6800000,  // ₹68 Lakhs
    'SCN-D': 18432000, // ₹1.843 Cr (Live Solver Output)
  }
  const spendAmount = scenarioSpends[selectedScenarioId] ?? 18432000.0
  const isAuthorizedRole = spendAmount > 1000000 ? (actorRole === 'CPO' || actorRole === 'CATEGORY_DIRECTOR') : true

  return (
    <div className="surface-content">
      {/* Workbench Header & Pipeline Replay Bar */}
      <section className="workbench-top-bar">
        <div>
          <h2>Human Approval Workbench & Decision Replay</h2>
          <p>Deterministic Policy Engine RBAC, Proposal-Only Action Packet, and Append-Only Audit Trail</p>
        </div>
        <div className="workbench-pipeline-controls">
          <label className="critic-toggle">
            <input
              type="checkbox"
              checked={forceCriticFailure}
              onChange={(e) => {
                setForceCriticFailure(e.target.checked)
                executePipeline(e.target.checked)
              }}
            />
            <span>Simulate Critic Failure (Escalate)</span>
          </label>
          <button
            className="replay-action-button"
            onClick={() => executePipeline(forceCriticFailure)}
            disabled={loading}
          >
            {loading ? 'Executing State Loop…' : 'Replay Decision Loop ↺'}
          </button>
        </div>
      </section>

      {actionError && (
        <div className="notice-banner error-banner">
          <strong>Policy / Governance Alert:</strong> {actionError}
        </div>
      )}

      {actionSuccess && (
        <div className="notice-banner success-banner">
          <strong>Audit Confirmation:</strong> {actionSuccess}
        </div>
      )}

      {!activeCase && (
        <div className="notice-banner info-banner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <strong>Read-Only Workbench Mode:</strong> No decision case is currently loaded. Click <em>"Run Decision Pipeline"</em> to execute the 11-step governed analysis and generate a case for review.
          </div>
          <button
            className="replay-action-button"
            onClick={() => executePipeline(false)}
            disabled={loading}
            style={{ marginLeft: '16px', whiteSpace: 'nowrap' }}
          >
            {loading ? 'Executing Loop…' : 'Run Decision Pipeline (SUP-1047) ▶'}
          </button>
        </div>
      )}

      {/* 8-Stage Decision Loop Stepper */}
      <section className="panel" style={{ marginBottom: '24px' }}>
        <div className="panel-heading">
          <div>
            <h2>Governed Decision Loop Lifecyle</h2>
            <p>11-step typed state progression with Critic sufficiency gates and audit tracking</p>
          </div>
          <span className="pill">STATE: {activeCase?.state || 'DETECTED'}</span>
        </div>
        <div className="stepper-horizontal">
          {[
            ['DETECTED', '01. Detect'],
            ['HYPOTHESES_ACTIVATED', '02. Hypotheses'],
            ['INVESTIGATING', '03. Investigate'],
            ['CRITIC_EVALUATING', '04. Critic Check'],
            ['IMPACT_QUANTIFIED', '05. Quantify'],
            ['SCENARIOS_SIMULATED', '06. Simulate'],
            ['RECOMMENDATION_GROUNDED', '07. Ground'],
            ['POLICY_EVALUATED', '08. Policy'],
            ['PENDING_HUMAN_APPROVAL', '09. Approval'],
            ['ACTION_PACKET_PREPARED', '10. Action Packet'],
            ['OUTCOME_RECORDED', '11. Outcome'],
          ].map(([stepKey, label]) => {
            const isCompleted = activeCase && activeCase.audit_trail.some((a) =>
              a.to_state === stepKey ||
              (stepKey === 'CRITIC_EVALUATING' && (a.to_state === 'CRITIC_PASSED' || a.to_state === 'CRITIC_FAILED')) ||
              (stepKey === 'ACTION_PACKET_PREPARED' && activeCase.action_packet)
            )
            const isCurrent = activeCase?.state === stepKey
            return (
              <div key={stepKey} className={`stepper-node ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}>
                <div className="stepper-dot">{isCompleted ? '✓' : ''}</div>
                <span className="stepper-label">{label}</span>
              </div>
            )
          })}
        </div>
      </section>

      {/* Interactive Approval Form & Policy Checker */}
      <div className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Approver Identity & Governance Policy Check</h2>
              <p>Simulate distinct enterprise roles and observe deterministic authorization</p>
            </div>
            <span className="pill">RBAC_ENFORCED</span>
          </div>
          <div className="approval-form-body">
            <div className="form-row">
              <label htmlFor="approver-role" className="form-label">Acting User Role:</label>
              <select
                id="approver-role"
                className="custom-select"
                style={{ width: '100%', height: '38px' }}
                value={actorRole}
                onChange={(e) => {
                  const r = e.target.value as any
                  setActorRole(r)
                  if (r === 'SUPPLY_CHAIN_PLANNER') setActorId('USR-PLANNER-01')
                  else if (r === 'PROCUREMENT_MANAGER') setActorId('USR-PM-01')
                  else setActorId('USR-CPO-01')
                }}
              >
                <option value="SUPPLY_CHAIN_PLANNER">Supply Chain Planner (Threshold &le; ₹10 Lakhs)</option>
                <option value="PROCUREMENT_MANAGER">Procurement Manager (Threshold &le; ₹10 Lakhs)</option>
                <option value="CPO">Chief Procurement Officer / Director (Threshold &gt; ₹10 Lakhs)</option>
              </select>
            </div>

            <div className={`policy-check-banner ${isAuthorizedRole ? 'authorized' : 'blocked'}`}>
              <div className="policy-check-title">
                {isAuthorizedRole ? '✓ POLICY AUTHORIZED FOR SPEND' : '✗ POLICY AUTHORIZATION BLOCKED'}
              </div>
              <p>
                Mitigation spend is <strong>₹{(spendAmount / 100000).toFixed(2)} Lakhs</strong> (Threshold: ₹10,00,000).
                {isAuthorizedRole
                  ? ' Executive sign-off authority confirmed. CPO / Director role permitted to authorize.'
                  : ` Role '${actorRole}' lacks authority for material spend exceeding ₹10 Lakhs. CPO approval mandatory.`}
              </p>
            </div>

            <div className="form-row">
              <label htmlFor="decision-reason" className="form-label">Decision Justification (Mandatory Audit Rationale):</label>
              <textarea
                id="decision-reason"
                className="reason-textarea"
                rows={3}
                value={approvalReason}
                onChange={(e) => setApprovalReason(e.target.value)}
                placeholder="Enter formal justification for audit record..."
              />
            </div>

            {/* Structured Human Decision Actions Grid */}
            <div className="approval-actions-bar">
              <button
                className="action-btn btn-approve primary-wide"
                onClick={() => handleAction('APPROVE')}
                disabled={loading}
              >
                {activeCase?.state === 'ACTION_PACKET_PREPARED'
                  ? '✓ Action Packet Prepared & Staged (Signed)'
                  : '✓ Approve Mitigation Plan (Proceed)'}
              </button>
              <div className="action-sub-grid">
                <button
                  className="action-btn btn-modify"
                  onClick={() => handleAction('MODIFY')}
                  disabled={loading || activeCase?.state === 'ACTION_PACKET_PREPARED'}
                >
                  ✎ Modify (30/70)
                </button>
                <button
                  className="action-btn btn-evidence"
                  onClick={() => handleAction('REQUEST_MORE_EVIDENCE')}
                  disabled={loading}
                >
                  ▤ Request Evidence
                </button>
                <button
                  className="action-btn btn-reject"
                  onClick={() => handleAction('REJECT')}
                  disabled={loading}
                >
                  ✕ Reject Action
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Proposal-Only Action Packet Card */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Proposal-Only Action Packet</h2>
              <p>Cryptographically hashed ERP staging packet (Strict read-only safety boundary)</p>
            </div>
            <span className="pill green">PROPOSAL_ONLY</span>
          </div>

          {activeCase?.action_packet ? (
            <div className="action-packet-body">
              <div className="packet-id-row">
                <span>Packet ID: <strong className="packet-id-badge">{activeCase.action_packet.packet_id}</strong></span>
                <span className="pill green" style={{ fontSize: '9.5px' }}>is_proposal_only: true</span>
              </div>
              <div className="packet-meta-grid">
                <div className="meta-pair">
                  <span>Target Gateway</span>
                  <strong>{activeCase.action_packet.target_erp_system}</strong>
                </div>
                <div className="meta-pair">
                  <span>Total Approved Spend</span>
                  <strong style={{ color: 'var(--forest-primary)' }}>₹{(activeCase.action_packet.total_approved_spend_inr / 100000).toFixed(2)} Lakhs</strong>
                </div>
                <div className="meta-pair">
                  <span>Authorized Role</span>
                  <strong>{activeCase.action_packet.authorized_by_role} ({activeCase.action_packet.authorized_by_actor})</strong>
                </div>
                <div className="meta-pair">
                  <span>Approved At</span>
                  <strong>{new Date(activeCase.action_packet.approved_at_utc).toLocaleString()}</strong>
                </div>
              </div>

              <div className="planned-actions-header">
                <span className="form-label">Planned Staging Actions ({activeCase.action_packet.planned_actions.length})</span>
                <span className="field-caption">Strict Read-Only Boundary</span>
              </div>

              <div className="planned-actions-list">
                {activeCase.action_packet.planned_actions.map((act, idx) => (
                  <div key={idx} className="planned-action-item">
                    <div className="action-type-badge">
                      <Icon name="check" size={13} />
                      <span>{act.action_type}</span>
                    </div>
                    <p className="action-item-desc">{act.description}</p>
                  </div>
                ))}
              </div>

              <div className="sha-hash-box">
                <div className="hash-header">
                  <Icon name="shield" size={12} />
                  <span>SHA-256 Cryptographic Verification Seal:</span>
                </div>
                <code className="hash-code">{activeCase.action_packet.packet_sha256}</code>
              </div>
            </div>
          ) : (
            <div className="empty-packet-state">
              <div className="empty-packet-badge">
                <Icon name="lock" size={22} />
              </div>
              <h3 className="empty-packet-title">Action Packet Pending Human Sign-Off</h3>
              <p className="empty-packet-desc">
                Executing executive sign-off on the left generates a cryptographically sealed, immutable action proposal for enterprise ERP staging.
              </p>
              <div className="packet-preview-box">
                <div className="preview-row">
                  <span className="preview-kicker">Target Gateway</span>
                  <span className="preview-value">SAP S/4HANA (Strict Read-Only)</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Proposed Plan</span>
                  <span className="preview-value">{selectedScenarioId}: Hybrid Mitigation</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Materiality Spend</span>
                  <span className="preview-value">₹{(spendAmount / 100000).toFixed(2)} Lakhs (CPO Required)</span>
                </div>
                <div className="preview-row">
                  <span className="preview-kicker">Governance Hash</span>
                  <span className="preview-value mono">HMAC-SHA256 (Sealed on Approval)</span>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Audit Trail Log */}
      {activeCase && (
        <section className="panel" style={{ marginTop: '24px' }}>
          <div className="panel-heading">
            <div>
              <h2>Append-Only Governance Audit Trail</h2>
              <p>Immutable record of all state transitions, actor IDs, and policy decisions for {activeCase.case_id}</p>
            </div>
            <span className="pill">{activeCase.audit_trail.length} AUDIT EVENTS</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '120px' }}>Timestamp (UTC)</th>
                  <th style={{ width: '180px' }}>From State</th>
                  <th style={{ width: '220px' }}>To State</th>
                  <th style={{ width: '190px' }}>Actor ID</th>
                  <th>Audit Detail</th>
                </tr>
              </thead>
              <tbody>
                {activeCase.audit_trail.map((evt, idx) => (
                  <tr key={idx}>
                    <td className="muted" style={{ fontFamily: 'DM Mono', fontSize: '10.5px' }}>
                      {new Date(evt.timestamp_utc).toLocaleTimeString()}
                    </td>
                    <td>
                      <span className="state-badge from">{evt.from_state}</span>
                    </td>
                    <td>
                      <span className={`state-badge ${evt.to_state === 'PENDING_HUMAN_APPROVAL' ? 'pending' : ''}`}>
                        {evt.to_state}
                      </span>
                    </td>
                    <td>
                      <span className="actor-tag">{evt.actor}</span>
                    </td>
                    <td style={{ lineHeight: '1.45', color: 'var(--text-main)', fontSize: '11.5px' }}>
                      {evt.detail}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
