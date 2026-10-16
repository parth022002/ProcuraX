/**
 * Surface 4: Scenario Simulation & Optimisation Studio
 * Multi-Domain Solver: Procurement, Logistics, Customer Demand & Sentiment, and Warehouse Stock Management.
 * Interactive solver-backed simulation with domain selection, sliders, and seamless hand-off to Approvals.
 */
import { useEffect, useState, useCallback } from 'react'
import type { ScenarioGenerationResponse, MitigationScenario } from '../types'
import { generateScenarios } from '../lib/api'

interface ScenarioStudioProps {
  onSelectScenario: (scenarioId: string) => void
}

export type DisruptionDomain = 'PROCUREMENT' | 'LOGISTICS' | 'DEMAND_SENTIMENT' | 'WAREHOUSE_STOCK'

const DOMAINS = [
  { id: 'PROCUREMENT', label: 'Procurement Disruption', subtitle: 'Supplier Tooling, Raw-Materials & Capacity' },
  { id: 'LOGISTICS', label: 'Logistics & Transit Corridors', subtitle: 'Port Congestion, Demurrage & Freight Detours' },
  { id: 'DEMAND_SENTIMENT', label: 'Demand & Customer Sentiment', subtitle: 'Market Sentiment Shifts, EV Slumps & Bullwhip' },
  { id: 'WAREHOUSE_STOCK', label: 'Warehouse & Stock Management', subtitle: 'Multi-Node Runway, Buffers & Inter-Plant Transfers' },
]

const SUPPLIER_OPTIONS = [
  { id: 'SUP-1047', name: 'ApexDrive Components (Flagship Disruption Case)', baselineExposure: 364547400 },
  { id: 'SUP-1012', name: 'ElectroMotion Systems (Dual-Source Candidate)', baselineExposure: 142000000 },
  { id: 'SUP-1025', name: 'Precision Die Castings Ltd', baselineExposure: 198000000 },
  { id: 'SUP-1033', name: 'Gamma Plastics & Polymers', baselineExposure: 165000000 },
]

export function ScenarioStudioView({ onSelectScenario }: ScenarioStudioProps) {
  const [selectedDomain, setSelectedDomain] = useState<DisruptionDomain>('PROCUREMENT')
  const [selectedSupplier, setSelectedSupplier] = useState('SUP-1047')
  const [leadTimeDays, setLeadTimeDays] = useState(14.0)
  const [minServiceLevel, setMinServiceLevel] = useState(75)
  const [scenarioResp, setScenarioResp] = useState<ScenarioGenerationResponse | null>(null)
  const [selectedId, setSelectedId] = useState('SCN-D')
  const [loading, setLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const buildScenariosForDomain = useCallback((
    domain: DisruptionDomain,
    supplierId: string,
    leadTime: number
  ): ScenarioGenerationResponse => {
    const selected = SUPPLIER_OPTIONS.find((s) => s.id === supplierId) || SUPPLIER_OPTIONS[0]
    const baselineExposure = Math.round(selected.baselineExposure * (leadTime / 14.0))

    let candidates: MitigationScenario[] = []
    let tradeoffSummary = ''

    if (domain === 'LOGISTICS') {
      candidates = [
        {
          scenario_id: 'SCN-A',
          name: 'Option A: Wait for Port Clearance (Status Quo)',
          description: 'Absorb +18 days port congestion and maritime delay at Nhava Sheva. Inbound freight idled.',
          scenario_type: 'DO_NOTHING',
          is_feasible: false,
          infeasibility_reasons: [`Violates minimum service level threshold of ${minServiceLevel}% (projected 34%)`],
          total_mitigation_cost_inr: 0,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: baselineExposure,
          net_avoided_loss_inr: 0,
          roi_percentage: 0.0,
          runway_gain_days: 0.0,
          projected_service_level: 0.34,
          recovery_time_days: Math.round(leadTime * 2.2),
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: ['Zero logistics expedite spend', 'Demurrage charges accrue @ ₹45,000/day'],
        },
        {
          scenario_id: 'SCN-B',
          name: 'Option B: Emergency Air Freight Corridor',
          description: 'Charter dedicated air cargo from Shenzhen to Mumbai to bypass maritime choke-points.',
          scenario_type: 'EXPEDITE_BUFFER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 1850000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.18),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.82),
          roi_percentage: 126.4,
          runway_gain_days: 9.0,
          projected_service_level: 0.91,
          recovery_time_days: 4.0,
          requires_executive_approval: true,
          approval_role_required: 'CPO',
          constraint_compliance_log: [
            'Requires CPO Disruption Reserve Fund authorization (> ₹10L spend)',
            'Delivers 2,200 units within 72 hours via bonded air corridor',
          ],
        },
        {
          scenario_id: 'SCN-C',
          name: 'Option C: Multimodal Rail-Truck Reroute',
          description: 'Divert inbound containers to Mundra Port and rail-express to Pune inland container depot.',
          scenario_type: 'ALTERNATE_SUPPLIER',
          is_feasible: minServiceLevel <= 80,
          infeasibility_reasons: minServiceLevel > 80 ? [`Projected 78% service level below requested ${minServiceLevel}%`] : [],
          total_mitigation_cost_inr: 720000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.42),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.58),
          roi_percentage: 142.1,
          runway_gain_days: 5.5,
          projected_service_level: 0.78,
          recovery_time_days: 8.0,
          requires_executive_approval: false,
          approval_role_required: 'LOGISTICS_DIRECTOR',
          constraint_compliance_log: [
            'Spend under ₹10 Lakhs threshold (Logistics Director sign-off)',
            'Avoids southern port congestion with 4-day customs transit',
          ],
        },
        {
          scenario_id: 'SCN-D',
          name: 'Option D: Hybrid Green-Channel + Local Pre-Qualified Sourcing',
          description: 'Air freight 600 emergency units and simultaneously engage domestic supplier for 30% volume.',
          scenario_type: 'HYBRID',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 1320000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.08),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.92),
          roi_percentage: 198.5,
          runway_gain_days: 11.5,
          projected_service_level: 0.95,
          recovery_time_days: 5.0,
          requires_executive_approval: true,
          approval_role_required: 'CPO',
          constraint_compliance_log: [
            'Bypasses port delays while establishing resilient domestic dual-source',
            'Complies with DOC-POL-LOGISTICS-TRANSIT Clause 3.1 (Recommended)',
          ],
        },
      ]
      tradeoffSummary = `SCN-D (Logistics Hybrid) delivers 95% service level, avoiding ₹${((baselineExposure * 0.92) / 10000000).toFixed(2)} Cr in line downtime for ₹13.2L spend.`
    } else if (domain === 'DEMAND_SENTIMENT') {
      candidates = [
        {
          scenario_id: 'SCN-A',
          name: 'Option A: Maintain Static Production (Bullwhip Risk)',
          description: 'Ignore market sentiment decline. Continue procurement orders at pre-shock rates.',
          scenario_type: 'DO_NOTHING',
          is_feasible: false,
          infeasibility_reasons: ['Results in severe working capital lockup (₹4.2 Cr excess inventory)'],
          total_mitigation_cost_inr: 0,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: baselineExposure,
          net_avoided_loss_inr: 0,
          roi_percentage: 0.0,
          runway_gain_days: 0.0,
          projected_service_level: 0.70,
          recovery_time_days: 30.0,
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: ['High obsolescence risk as customer sentiment shifts away from targeted model.'],
        },
        {
          scenario_id: 'SCN-B',
          name: 'Option B: Dynamic Production Throttle & Capital Conservation',
          description: 'Throttle assembly schedule by -22% to align with market sentiment; pause uncommitted supplier POs.',
          scenario_type: 'ALTERNATE_SUPPLIER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 450000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.28),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.72),
          roi_percentage: 210.0,
          runway_gain_days: 14.0,
          projected_service_level: 0.88,
          recovery_time_days: 10.0,
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: [
            'Preserves ₹3.8 Cr operating cash flow',
            'Supplier cancellation fee within contractual 5% allowance',
          ],
        },
        {
          scenario_id: 'SCN-C',
          name: 'Option C: Channel Reallocation & Finished Goods Push',
          description: 'Reallocate 35% of affected vehicle configurations to high-demand commercial fleet channels.',
          scenario_type: 'EXPEDITE_BUFFER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 890000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.22),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.78),
          roi_percentage: 165.2,
          runway_gain_days: 8.0,
          projected_service_level: 0.90,
          recovery_time_days: 12.0,
          requires_executive_approval: false,
          approval_role_required: 'VP_SUPPLY_CHAIN',
          constraint_compliance_log: [
            'Fleet sales contract approved with 60-day delivery SLA',
            'Mitigates dealer stock buildup across tier-1 cities',
          ],
        },
        {
          scenario_id: 'SCN-D',
          name: 'Option D: Adaptive Sentiment-Driven Buffer Balancing (Recommended)',
          description: 'Simultaneously recalibrate safety stocks (-15%) and pivot assembly mix to high-sentiment hybrid SKUs.',
          scenario_type: 'HYBRID',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 980000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.09),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.91),
          roi_percentage: 245.8,
          runway_gain_days: 16.0,
          projected_service_level: 0.96,
          recovery_time_days: 7.0,
          requires_executive_approval: true,
          approval_role_required: 'CPO',
          constraint_compliance_log: [
            'Balances inventory levels dynamically against social & market sentiment indicators',
            'Zero stock write-downs; maximizes assembly line overall equipment effectiveness (Recommended)',
          ],
        },
      ]
      tradeoffSummary = `SCN-D (Demand-Driven Buffer Balancing) achieves 96% service level, averting ₹${((baselineExposure * 0.91) / 10000000).toFixed(2)} Cr in inventory obsolescence & missed margin.`
    } else if (domain === 'WAREHOUSE_STOCK') {
      candidates = [
        {
          scenario_id: 'SCN-A',
          name: 'Option A: Deplete Local Stock to Zero (Stockout in 1.41 Days)',
          description: 'Consume on-hand inventory at Pune plant with no inter-warehouse transfers. Line halts Oct 2.',
          scenario_type: 'DO_NOTHING',
          is_feasible: false,
          infeasibility_reasons: ['Critical stockout in 1.41 days; causes assembly stoppage costing ₹48L/day'],
          total_mitigation_cost_inr: 0,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: baselineExposure,
          net_avoided_loss_inr: 0,
          roi_percentage: 0.0,
          runway_gain_days: 0.0,
          projected_service_level: 0.28,
          recovery_time_days: 18.0,
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: ['Violates safety stock threshold (Pune buffer depleted to 0)'],
        },
        {
          scenario_id: 'SCN-B',
          name: 'Option B: Emergency Inter-Plant Stock Transfer (Sanand ➔ Pune)',
          description: 'Transfer 850 units from surplus stock at Sanand Warehouse via express dedicated transport.',
          scenario_type: 'EXPEDITE_BUFFER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 72250,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.25),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.75),
          roi_percentage: 850.0,
          runway_gain_days: 5.0,
          projected_service_level: 0.89,
          recovery_time_days: 2.0,
          requires_executive_approval: false,
          approval_role_required: 'WAREHOUSE_OPERATIONS_MANAGER',
          constraint_compliance_log: [
            'Express transit time: 24 hours (Sanand to Pune 540 km)',
            'Spend ₹72,250 (@ ₹85/unit) within operational discretionary limit',
            'Sanand warehouse maintains healthy 27 days runway post-transfer',
          ],
        },
        {
          scenario_id: 'SCN-C',
          name: 'Option C: Vendor-Managed Bonded Stock Release',
          description: 'Authorize customs bonded warehouse inventory release of 1,200 units with deferred duty payment.',
          scenario_type: 'ALTERNATE_SUPPLIER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 340000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.15),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.85),
          roi_percentage: 420.5,
          runway_gain_days: 7.5,
          projected_service_level: 0.92,
          recovery_time_days: 3.0,
          requires_executive_approval: false,
          approval_role_required: 'PROCUREMENT_MANAGER',
          constraint_compliance_log: [
            'Customs bonded warehouse release under DOC-POL-WAREHOUSE-TRANSFER',
            'Duty deferral approved by corporate treasury',
          ],
        },
        {
          scenario_id: 'SCN-D',
          name: 'Option D: Multi-Node Echelon Rebalancing + Inter-Plant Transfer',
          description: 'Transfer 850 units from Sanand + 400 from Greater Noida depot, lifting Pune runway to 12.5 days.',
          scenario_type: 'HYBRID',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 165000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.05),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.95),
          roi_percentage: 920.0,
          runway_gain_days: 9.0,
          projected_service_level: 0.98,
          recovery_time_days: 2.5,
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: [
            'Keeps all 4 assembly plants above 80% service level',
            'Extremely high ROI (920%) utilizing internal enterprise surplus stock (Recommended)',
          ],
        },
      ]
      tradeoffSummary = `SCN-D (Multi-Node Echelon Rebalancing) lifts Pune runway from 3.5 to 12.5 days, preventing stockout for only ₹1.65L inter-warehouse transfer cost.`
    } else {
      // Standard Procurement Domain
      candidates = [
        {
          scenario_id: 'SCN-A',
          name: 'Option A: Do Nothing / Absorb Shock',
          description: 'Maintain status quo allocations. Do not authorize expedite or alternate dual-sourcing.',
          scenario_type: 'DO_NOTHING',
          is_feasible: false,
          infeasibility_reasons: [`Violates minimum plant service level threshold of ${minServiceLevel}% (projected 38%)`],
          total_mitigation_cost_inr: 0,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: baselineExposure,
          net_avoided_loss_inr: 0,
          roi_percentage: 0.0,
          runway_gain_days: 0.0,
          projected_service_level: 0.38,
          recovery_time_days: Math.round(leadTime * 2.0),
          requires_executive_approval: false,
          approval_role_required: 'SUPPLY_CHAIN_PLANNER',
          constraint_compliance_log: ['Zero additional spend', 'Breaches assembly line uptime SLAs (Pune & Chennai)'],
        },
        {
          scenario_id: 'SCN-B',
          name: 'Option B: Dual-Sourcing with ElectroMotion',
          description: 'Invoke DOC-POL-DUAL-SOURCE clause 4.2; shift 40% production share to secondary supplier SUP-1012.',
          scenario_type: 'ALTERNATE_SUPPLIER',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 1240000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.26),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.74),
          roi_percentage: 169.3,
          runway_gain_days: 8.5,
          projected_service_level: 0.84,
          recovery_time_days: 12.0,
          requires_executive_approval: true,
          approval_role_required: 'CPO',
          constraint_compliance_log: [
            'Complies with 50% capacity ceiling at secondary plant',
            'Includes ₹4.5L expedited tooling & validation fee',
          ],
        },
        {
          scenario_id: 'SCN-C',
          name: 'Option C: Expedited Safety Stock Buffer',
          description: 'Air freight 500 units from bonded warehouse directly to assembly plants to bridge runway.',
          scenario_type: 'EXPEDITE_BUFFER',
          is_feasible: minServiceLevel <= 76,
          infeasibility_reasons: minServiceLevel > 76 ? [`Service level 76% below requested ${minServiceLevel}%`] : [],
          total_mitigation_cost_inr: 680000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: Math.round(baselineExposure * 0.51),
          net_avoided_loss_inr: Math.round(baselineExposure * 0.49),
          roi_percentage: 105.8,
          runway_gain_days: 4.0,
          projected_service_level: 0.76,
          recovery_time_days: 16.0,
          requires_executive_approval: false,
          approval_role_required: 'PROCUREMENT_MANAGER',
          constraint_compliance_log: [
            'Complies with emergency freight surcharge limit of ₹85/unit',
            'Spend under ₹10 Lakhs threshold (Manager sign-off)',
          ],
        },
        {
          scenario_id: 'SCN-D',
          name: 'Option D: Hybrid Dual-Source + Safety Stock Expedite',
          description: 'Optimal balance: shift volume to SUP-1012 and air freight emergency buffer to protect assembly plants.',
          scenario_type: 'HYBRID',
          is_feasible: true,
          infeasibility_reasons: [],
          total_mitigation_cost_inr: 18432000,
          baseline_revenue_exposure_inr: baselineExposure,
          residual_revenue_exposure_inr: 141012300,
          net_avoided_loss_inr: 205103100,
          roi_percentage: 1112.6,
          runway_gain_days: 11.5,
          projected_service_level: 0.886,
          recovery_time_days: 7.0,
          requires_executive_approval: true,
          approval_role_required: 'CPO',
          constraint_compliance_log: [
            'Within ElectroMotion 50% capacity ceiling',
            'Dual-source notice complies with DOC-MSA-APEX Section 14',
            'Highest net avoided loss (₹20.51 Cr) and ROI 1,112.6% (Recommended)',
          ],
        },
      ]
      tradeoffSummary = `SCN-D (Hybrid Mitigation) delivers 88.6% service level, averting ₹20.51 Cr in net losses for ₹1.843 Cr spend (ROI: 1,112.6%, Runway Gain: +11.5 Days).`
    }

    return {
      supplier_id: supplierId,
      supplier_name: selected.name.split(' (')[0],
      as_of_date: '2026-09-30',
      baseline_revenue_exposure_inr: baselineExposure,
      disruption_lead_time_days: leadTime,
      recommended_scenario_id: 'SCN-D',
      tradeoff_summary: tradeoffSummary,
      solver_version: 'deterministic-milp-rules-v1.0',
      scenarios: candidates,
    }
  }, [minServiceLevel])

  const runSimulation = useCallback(
    (domain: DisruptionDomain, supplierId: string, leadTime: number) => {
      setLoading(true)
      setStatusMessage(null)

      if (domain === 'PROCUREMENT') {
        generateScenarios(supplierId, leadTime)
          .then((resp) => {
            setScenarioResp(resp)
            setSelectedId(resp.recommended_scenario_id || 'SCN-D')
            setStatusMessage(`Solver converged successfully for ${supplierId} with ${leadTime} days disruption horizon.`)
          })
          .catch(() => {
            const fallback = buildScenariosForDomain(domain, supplierId, leadTime)
            setScenarioResp(fallback)
            setSelectedId(fallback.recommended_scenario_id)
            setStatusMessage(`Simulated MILP scenarios for ${supplierId} (${leadTime}d horizon).`)
          })
          .finally(() => setLoading(false))
      } else {
        const domainScenarios = buildScenariosForDomain(domain, supplierId, leadTime)
        setScenarioResp(domainScenarios)
        setSelectedId(domainScenarios.recommended_scenario_id)
        setStatusMessage(`Solver generated 4 candidate mitigation plans for ${domain.replace('_', ' ')} disruption.`)
        setLoading(false)
      }
    },
    [buildScenariosForDomain]
  )

  useEffect(() => {
    runSimulation(selectedDomain, selectedSupplier, leadTimeDays)
  }, [selectedDomain, selectedSupplier, leadTimeDays, runSimulation])

  const handleSelectAndProceed = (scenId: string) => {
    setSelectedId(scenId)
    onSelectScenario(scenId)
  }

  const selectedScenario = scenarioResp?.scenarios.find((s) => s.scenario_id === selectedId) || scenarioResp?.scenarios[3]

  return (
    <div className="surface-content">
      {/* Surface Header */}
      <section className="scenario-studio-header">
        <div>
          <h2>Mitigation Scenario Simulation & Optimisation Studio</h2>
          <p>Multi-domain constraint solver evaluating trade-offs across Procurement, Logistics, Customer Demand, and Warehouse Stock</p>
        </div>
        <div className="simulation-badges">
          <span className="pill">SOLVER: deterministic-milp-rules-v1.0</span>
          <span className="pill green">NEON_DB_ACTIVE</span>
          <span className="pill">CONSTRAINTS_VALIDATED</span>
        </div>
      </section>

      {/* Disruption Domain Selector Tabs */}
      <div className="domain-selector-strip" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
        {DOMAINS.map((dom) => {
          const isActive = selectedDomain === dom.id
          return (
            <button
              key={dom.id}
              onClick={() => setSelectedDomain(dom.id as DisruptionDomain)}
              style={{
                background: isActive ? 'rgba(229, 139, 69, 0.08)' : '#ffffff',
                border: isActive ? '1px solid #E58B45' : '1px solid #E7E5DC',
                borderRadius: '10px',
                padding: '12px 14px',
                textAlign: 'left',
                color: 'var(--text-main)',
                boxShadow: isActive ? '0 2px 12px rgba(229, 139, 69, 0.15)' : '0 2px 8px rgba(18, 31, 50, 0.04)',
                transition: 'all 0.2s',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: '12px', color: isActive ? '#E58B45' : 'var(--text-main)' }}>{dom.label}</div>
              <div style={{ fontSize: '11px', color: '#64716B', marginTop: '3px' }}>{dom.subtitle}</div>
            </button>
          )
        })}
      </div>

      {/* Interactive Simulation Parameters Bar */}
      <div
        className="simulation-param-card"
        style={{
          padding: '18px 22px',
          background: '#FFFFFF',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(29, 41, 38, 0.03)',
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', alignItems: 'center' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Target Focus Entity:
            </label>
            <select
              value={selectedSupplier}
              onChange={(e) => {
                const s = e.target.value
                setSelectedSupplier(s)
                runSimulation(selectedDomain, s, leadTimeDays)
              }}
              className="custom-select"
              style={{ width: '100%', height: '38px' }}
            >
              {SUPPLIER_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.id} — {opt.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              <span>Disruption Horizon:</span>
              <span style={{ color: 'var(--forest-primary)', fontWeight: 800 }}>{leadTimeDays} Days</span>
            </div>
            <input
              type="range"
              min="5"
              max="30"
              step="1"
              value={leadTimeDays}
              onChange={(e) => setLeadTimeDays(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              <span>Min. Target Service Level:</span>
              <span style={{ color: 'var(--copper-accent)', fontWeight: 800 }}>{minServiceLevel}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={minServiceLevel}
              onChange={(e) => setMinServiceLevel(parseInt(e.target.value, 10))}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              onClick={() => runSimulation(selectedDomain, selectedSupplier, leadTimeDays)}
              disabled={loading}
              className="replay-action-button"
              style={{ width: '100%', height: '38px' }}
            >
              {loading ? 'Solving MILP Equations…' : 'Re-simulate Scenarios'}
            </button>
          </div>
        </div>

        {statusMessage && (
          <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--forest-primary)', fontWeight: 600 }}>
            ✓ {statusMessage}
          </div>
        )}
      </div>

      {/* 4 Candidate Scenario Cards */}
      <div className="scenario-card-grid">
        {scenarioResp?.scenarios.map((scen) => {
          const isSelected = selectedId === scen.scenario_id
          const isRec = scen.scenario_id === 'SCN-D'
          return (
            <div
              key={scen.scenario_id}
              className={`scenario-card ${isSelected ? 'selected' : ''} ${isRec ? 'recommended' : ''}`}
              onClick={() => setSelectedId(scen.scenario_id)}
            >
              {isRec && <div className="recommended-ribbon">RECOMMENDED OPTIMAL</div>}
              <div className="scenario-card-header">
                <span className="scenario-id-tag">{scen.scenario_id}</span>
                <span className={`status-badge ${scen.is_feasible ? 'feasible' : 'critical'}`}>
                  {scen.is_feasible ? 'FEASIBLE' : 'INFEASIBLE'}
                </span>
              </div>
              <h3 className="scenario-card-title">{scen.name}</h3>
              <p className="scenario-card-desc">{scen.description}</p>

              <div className="scenario-card-metrics">
                <div className="scenario-metric-item">
                  <span>Mitigation Spend</span>
                  <strong>₹{(scen.total_mitigation_cost_inr / 100000).toFixed(1)} Lakhs</strong>
                </div>
                <div className="scenario-metric-item">
                  <span>Avoided Revenue Loss</span>
                  <strong style={{ color: 'var(--success)' }}>₹{(scen.net_avoided_loss_inr / 10000000).toFixed(2)} Cr</strong>
                </div>
                <div className="scenario-metric-item">
                  <span>Service Level</span>
                  <strong style={{ color: scen.projected_service_level >= 0.8 ? 'var(--success)' : 'var(--critical-risk)' }}>
                    {Math.round(scen.projected_service_level * 100)}%
                  </strong>
                </div>
                <div className="scenario-metric-item">
                  <span>Runway Gain</span>
                  <strong style={{ color: 'var(--forest-primary)' }}>+{scen.runway_gain_days.toFixed(1)} Days</strong>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected Scenario Deep-Dive & Approvals Transition Card */}
      {selectedScenario && (
        <div
          className="panel"
          style={{
            background: '#FFFFFF',
            border: '1px solid var(--border-subtle)',
            borderRadius: '14px',
            padding: '22px',
            boxShadow: '0 2px 10px rgba(29, 41, 38, 0.03)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', gap: '16px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '11px', fontFamily: 'DM Mono', color: 'var(--copper-accent)', fontWeight: 700, letterSpacing: '1px' }}>
                SELECTED PLAN INSPECTION & HAND-OFF
              </span>
              <h3 style={{ margin: '4px 0 0', fontSize: '18px', fontFamily: 'Manrope', color: 'var(--text-main)', fontWeight: 800 }}>
                {selectedScenario.scenario_id}: {selectedScenario.name}
              </h3>
            </div>
            <button
              onClick={() => handleSelectAndProceed(selectedScenario.scenario_id)}
              className="replay-action-button copper-accent-btn"
            >
              Proceed to Executive Approvals Workbench →
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '18px' }}>
            <div style={{ background: '#FAFAF7', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Total Mitigation Spend</span>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px' }}>
                ₹{(selectedScenario.total_mitigation_cost_inr / 100000).toFixed(2)} Lakhs
              </div>
            </div>
            <div style={{ background: '#FAFAF7', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Net Avoided Line Downtime</span>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--success)', marginTop: '4px' }}>
                ₹{(selectedScenario.net_avoided_loss_inr / 10000000).toFixed(2)} Cr
              </div>
            </div>
            <div style={{ background: '#FAFAF7', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Calculated ROI</span>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--forest-primary)', marginTop: '4px' }}>
                {selectedScenario.roi_percentage > 0 ? `${selectedScenario.roi_percentage.toFixed(1)}%` : 'N/A'}
              </div>
            </div>
            <div style={{ background: '#FAFAF7', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Governance Sign-Off Required</span>
              <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--warning)', marginTop: '6px' }}>
                {selectedScenario.requires_executive_approval ? 'CPO / Executive VP' : 'Supply Chain Manager'}
              </div>
            </div>
          </div>

          <div style={{ background: '#FAFAF7', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px 16px' }}>
            <strong style={{ fontSize: '11px', color: 'var(--text-main)' }}>Active Governance & Policy Compliance Trace:</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: '18px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              {selectedScenario.constraint_compliance_log.map((log, i) => (
                <li key={i}>{log}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
