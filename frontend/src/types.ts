/**
 * TypeScript types for ProcuraX full-stack decision intelligence platform.
 * Mirrors FastAPI Pydantic schemas with provenance and audit metadata.
 */

export type ProvenanceType = 'PUBLIC_REAL' | 'SYNTHETIC' | 'DERIVED' | 'ILLUSTRATIVE'

export type HealthResponse = {
  status: string
  app: string
  environment: string
  implementation_status: string
}

export type SignalProvider = {
  provider_id: string
  name: string
  status: 'HEALTHY' | 'DEGRADED' | 'UNCONFIGURED' | 'OFFLINE'
  signal_count: number
  last_fetched_utc: string | null
  provenance: ProvenanceType
}

export type SignalItem = {
  signal_id: string
  provider: string
  title: string
  url: string
  published_at: string
  retrieved_at: string
  sentiment_score: number
  relevance_score: number
  entities_mentioned: string[]
  is_assumption: boolean
  disclaimer: string
  provenance: ProvenanceType
  freshness_status?: 'fresh' | 'recent' | 'stale' | 'archived'
  age_hours?: number | null
  persisted?: boolean
  content_hash?: string
}

export type RiskScoreResponse = {
  supplier_id: string
  supplier_name: string
  as_of_date: string
  stockout_probability_90d: number
  evidence_confidence: number
  governed_risk_score: number
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  top_risk_drivers: Array<{
    feature: string
    importance: number
    direction: string
    description: string
  }>
  model_version: string
  formula_audit: Record<string, string>
}

export type ModelCardResponse = {
  model_name: string
  version: string
  target_definition: string
  prediction_horizon: string
  training_window: string
  held_out_window: string
  sample_sizes: {
    train_rows: number
    test_rows: number
    suppliers: number
  }
  evaluation_metrics: {
    roc_auc: number
    brier_score: number
    accuracy: number
  }
  leakage_protection: {
    flagship_supplier_excluded: boolean
    flagship_id: string
  }
}

export type DependencyGraphNode = {
  id: string
  label: string
  node_type: 'SUPPLIER' | 'CATEGORY' | 'SKU' | 'PLANT'
  criticality?: number
  metrics?: Record<string, any>
}

export type DependencyGraphEdge = {
  source: string
  target: string
  relation: string
  weight_or_units?: number
}

export type NetworkDependencyGraph = {
  nodes: DependencyGraphNode
  edges: DependencyGraphEdge
}

export type PlantImpactSummary = {
  plant: string
  affected_sku_count: number
  critical_sku_count: number
  min_runway_days: number
  average_runway_days: number
  total_units_at_risk: number
  total_revenue_exposure_inr: number
  downtime_risk_level: string
}

export type SkuImpactSummary = {
  sku_id: string
  family: string
  criticality: number
  plant: string
  on_hand_units: number
  safety_stock_units: number
  average_daily_consumption: number
  runway_days: number
  buffer_penetration_days: number
  projected_stockout_date?: string
  units_at_risk: number
  revenue_exposure_inr: number
}

export type ImpactReportResponse = {
  supplier_id: string
  supplier_name: string
  as_of_date: string
  disruption_lead_time_days: number
  stockout_probability_used: number
  total_revenue_exposure_inr: number
  min_inventory_runway_days: number
  most_vulnerable_plant: string
  most_vulnerable_sku: string
  affected_sku_count: number
  affected_plants: string[]
  sku_impacts: SkuImpactSummary[]
  plant_impacts: PlantImpactSummary[]
  dependency_graph: {
    nodes: DependencyGraphNode[]
    edges: DependencyGraphEdge[]
  }
  formula_version: string
  assumptions: string[]
}

export type MitigationScenario = {
  scenario_id: string
  name: string
  description: string
  scenario_type: 'DO_NOTHING' | 'ALTERNATE_SUPPLIER' | 'EXPEDITE_BUFFER' | 'HYBRID'
  is_feasible: boolean
  infeasibility_reasons: string[]
  total_mitigation_cost_inr: number
  baseline_revenue_exposure_inr: number
  residual_revenue_exposure_inr: number
  net_avoided_loss_inr: number
  roi_percentage: number
  runway_gain_days: number
  projected_service_level: number
  recovery_time_days: number
  requires_executive_approval: boolean
  approval_role_required: string
  constraint_compliance_log: string[]
}

export type ScenarioGenerationResponse = {
  supplier_id: string
  supplier_name: string
  as_of_date: string
  baseline_revenue_exposure_inr: number
  disruption_lead_time_days: number
  scenarios: MitigationScenario[]
  recommended_scenario_id: string
  tradeoff_summary: string
  solver_version: string
}

export type Citation = {
  chunk_id: string
  document_id: string
  document_title: string
  version: string
  section: string
  quote_text: string
}

export type CopilotQueryResponse = {
  query: string
  answer: string
  citations: Citation[]
  abstained: boolean
  abstention_reason: string | null
  retrieval_iterations: number
  critic_sufficiency_score: number
  user_role_applied: string
}

export type DocumentMetadata = {
  document_id: string
  title: string
  document_type: string
  version: string
  effective_date: string
  access_level: 'ALL' | 'PROCUREMENT_MANAGER' | 'CPO'
  chunk_count: number
  description: string
}

export type AuditEvent = {
  timestamp_utc: string
  from_state: string
  to_state: string
  actor: string
  detail: string
}

export type ProposalActionPacket = {
  packet_id: string
  case_id: string
  scenario_id: string
  is_proposal_only: boolean
  target_erp_system: string
  planned_actions: Array<{
    action_type: string
    description: string
    target_supplier?: string
    target_component?: string
    allocated_percentage?: number
    quantity_units?: number
    contract_clause?: string
  }>
  total_approved_spend_inr: number
  authorized_by_role: string
  authorized_by_actor: string
  approved_at_utc: string
  packet_sha256: string
}

export type ObservedOutcome = {
  outcome_id: string
  case_id: string
  supplier_id: string
  decision_timestamp_utc: string
  observed_at_utc: string
  action_taken: string
  actual_otif: number
  actual_service_level: number
  actual_cost_inr: number
  outcome_label: string
  notes?: string
}

export type HumanApprovalAction = 'APPROVE' | 'MODIFY' | 'REQUEST_MORE_EVIDENCE' | 'REJECT'

export type HumanApprovalPayload = {
  action: HumanApprovalAction
  actor_id: string
  actor_role: string
  reason: string
  idempotency_key: string
  selected_scenario_id?: string
  modified_allocations?: Record<string, any>
}

export type DisruptionCase = {
  case_id: string
  supplier_id: string
  supplier_name: string
  state: string
  severity: string
  created_at_utc: string
  updated_at_utc: string
  activated_hypotheses: string[]
  critic_score: number
  critic_retries_used: number
  critic_gap_identified?: string | null
  risk_score: number
  impact_summary?: Record<string, any>
  candidate_scenarios: MitigationScenario[]
  recommended_scenario_id?: string
  grounded_brief?: string
  citations: Citation[]
  policy_evaluation?: {
    scenario_id: string
    additional_spend_inr: number
    spend_threshold_inr: number
    required_role: string
    reason: string
  }
  approval_decision?: HumanApprovalPayload
  action_packet?: ProposalActionPacket
  observed_outcome?: ObservedOutcome
  audit_trail: AuditEvent[]
}

// Starter UI demo types for backwards compatibility
export type Alert = {
  supplierId: string
  supplier: string
  category: string
  score: number
  issue: string
  impact: string
  updated: string
  status: 'Critical' | 'High' | 'Review'
}

export type Scenario = {
  name: string
  detail: string
  costDelta: string
  riskReduction: string
  status: 'Feasible' | 'Review'
}
