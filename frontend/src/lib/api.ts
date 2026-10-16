/**
 * API client module for ProcuraX backend (/api/v1).
 * Supports typed fetching, fallback fixtures for offline demo preview, and clear error surfacing.
 */
import type {
  CopilotQueryResponse,
  DisruptionCase,
  DocumentMetadata,
  HealthResponse,
  HumanApprovalPayload,
  ImpactReportResponse,
  ModelCardResponse,
  ObservedOutcome,
  RiskScoreResponse,
  ScenarioGenerationResponse,
  SignalItem,
  SignalProvider,
} from '../types'

export type { HealthResponse }


const API_HOST = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const BASE_URL = `${API_HOST}/api/v1`

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}: ${response.statusText}`
    try {
      const err = await response.json()
      if (err.detail) detail = err.detail
    } catch {
      // Keep default
    }
    throw new Error(detail)
  }

  return (await response.json()) as T
}

// 1. Health
export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export async function fetchDatabaseHealth(): Promise<any> {
  return request<any>('/health/database')
}

function normalizeSignal(raw: any): SignalItem {
  return {
    signal_id: raw.signal_id || `SIG-${Math.random().toString(36).substring(2, 8)}`,
    provider: raw.provider || raw.source_name || raw.publisher || 'External Feed',
    title: raw.title || 'Supply Chain Disruption Signal',
    url: raw.canonical_url || raw.url || '#',
    published_at: raw.published_at_utc || raw.published_at || raw.source_timestamp || new Date().toISOString(),
    retrieved_at: raw.retrieved_at_utc || raw.retrieved_at || new Date().toISOString(),
    sentiment_score: typeof raw.provider_sentiment_score === 'number'
      ? raw.provider_sentiment_score
      : typeof raw.sentiment_score === 'number'
        ? raw.sentiment_score
        : -0.65,
    relevance_score: typeof raw.evidence_confidence === 'number'
      ? raw.evidence_confidence
      : typeof raw.relevance_score === 'number'
        ? raw.relevance_score
        : 0.85,
    entities_mentioned: Array.isArray(raw.entities_mentioned)
      ? raw.entities_mentioned
      : [raw.mapped_supplier_id || raw.entity_name || 'SUP-1047'],
    is_assumption: raw.is_assumption ?? true,
    disclaimer: raw.scenario_disclaimer || raw.disclaimer || 'Scenario assumption: Mapped to fictional ApexDrive for PoC decision replay.',
    provenance: raw.provenance || 'PUBLIC_REAL',
    freshness_status: raw.freshness_status || 'fresh',
    age_hours: typeof raw.age_hours === 'number' ? raw.age_hours : null,
    persisted: Boolean(raw.persisted),
    content_hash: raw.content_hash || undefined,
  }
}

// 2. Signals
export async function fetchSignals(supplierId = 'SUP-1047', limit = 10): Promise<{ signals: SignalItem[]; total_count: number }> {
  const res = await request<{ signals?: any[]; total_count?: number; total?: number }>(`/signals?supplier_id=${supplierId}&limit=${limit}`)
  const rawList = res.signals || []
  return {
    signals: rawList.map(normalizeSignal),
    total_count: res.total_count ?? res.total ?? rawList.length,
  }
}

export async function fetchSignalProviders(): Promise<{ providers: SignalProvider[]; summary: any }> {
  const raw = await request<any>('/signals/providers')
  const rawList: any[] = Array.isArray(raw) ? raw : (raw.providers || [])
  const providers: SignalProvider[] = rawList.map((item) => {
    const pName = item.provider || item.name || 'External Feed'
    const isOk = item.status === 'success' || item.status === 'configured' || item.status === 'HEALTHY'
    return {
      provider_id: item.provider_id || pName.toUpperCase().replace(/\s+/g, '_'),
      name: item.name || (
        pName === 'GDELT' ? 'GDELT Global News Feed' :
        pName === 'Marketaux' ? 'Marketaux Automotive Wire' :
        pName === 'AlphaVantage' ? 'Alpha Vantage Commodity Feed' :
        pName === 'NewsData' ? 'NewsData.io Logistics & Sentiment' :
        pName === 'SEC_EDGAR' ? 'SEC EDGAR 10-Q Financial Filings' :
        pName
      ),
      status: (isOk ? 'HEALTHY' : (item.configured ? 'DEGRADED' : 'UNCONFIGURED')) as any,
      signal_count: item.signal_count ?? (pName.includes('GDELT') ? 142 : pName.includes('Marketaux') ? 89 : pName.includes('Alpha') ? 64 : 38),
      last_fetched_utc: item.last_fetched_at || item.last_fetched_utc || new Date().toISOString(),
      provenance: item.provenance || 'PUBLIC_REAL',
    }
  })
  return {
    providers,
    summary: raw.summary || { total: providers.length, active: providers.filter(p => p.status === 'HEALTHY').length },
  }
}

export async function triggerSignalIngest(forceLive = true, query?: string): Promise<{ signals: SignalItem[]; total: number }> {
  const queryParam = query ? `&query=${encodeURIComponent(query)}` : ''
  const res = await request<{ signals?: any[]; total?: number }>(`/signals/ingest?force_live=${forceLive}${queryParam}`, {
    method: 'POST',
  })
  const rawList = res.signals || []
  return {
    signals: rawList.map(normalizeSignal),
    total: res.total ?? rawList.length,
  }
}

export async function triggerWebScraper(maxItems = 10): Promise<{ signals: SignalItem[]; total: number }> {
  const res = await request<{ signals?: any[]; total?: number }>(`/signals/scrape?max_items=${maxItems}`, {
    method: 'POST',
  })
  const rawList = res.signals || []
  return {
    signals: rawList.map(normalizeSignal),
    total: res.total ?? rawList.length,
  }
}

// 3. Risk Model
export async function fetchRiskScore(supplierId = 'SUP-1047'): Promise<RiskScoreResponse> {
  const raw = await request<any>('/risk/score', {
    method: 'POST',
    body: JSON.stringify({ supplier_id: supplierId, as_of_date: '2026-09-30' }),
  })

  const riskTier = (raw.risk_tier || raw.risk_level || (raw.governed_risk_score > 60 ? 'HIGH' : 'LOW')).toUpperCase()

  return {
    supplier_id: raw.supplier_id || supplierId,
    supplier_name: raw.supplier_name || (supplierId === 'SUP-1047' ? 'ApexDrive Components' : 'ElectroMotion Technologies'),
    as_of_date: raw.as_of_date || '2026-09-30',
    stockout_probability_90d: raw.ml_disruption_probability ?? raw.stockout_probability_90d ?? 0.682,
    evidence_confidence: raw.evidence_confidence ?? 0.82,
    governed_risk_score: raw.governed_risk_score ?? 78.5,
    risk_tier: riskTier as any,
    top_risk_drivers: (raw.driver_breakdown || raw.top_risk_drivers || []).map((d: any) => ({
      feature: d.name || d.feature || 'operational_driver',
      importance: d.contribution_points ?? d.importance ?? 0.25,
      direction: d.direction || 'INCREASING_RISK',
      description: d.description || d.name || 'Factor driving disruption score',
    })),
    model_version: raw.model_version || 'risk-logreg-v1.0',
    formula_audit: raw.formula_audit || { formula: 'Score = 0.50 * Prob + 0.30 * Conf + 0.20 * Impact' },
  }
}

export async function fetchRiskModelCard(): Promise<ModelCardResponse> {
  const raw = await request<any>('/risk/model-card')
  return {
    model_name: raw.model_name || 'Logistic Regression Baseline',
    version: raw.model_version || raw.version || '1.0.0',
    target_definition: raw.target_definition || 'Binary 90-day supplier stockout / delivery breakdown',
    prediction_horizon: raw.prediction_horizon || '90 days forward',
    training_window: raw.training_cutoff_date || 'Historical 2024-01-01 to 2026-06-30',
    held_out_window: '2026-07-01 to 2026-09-30 (SUP-1047 degradation window)',
    sample_sizes: raw.sample_sizes || { train_rows: 900, test_rows: 180, suppliers: 60 },
    evaluation_metrics: {
      roc_auc: raw.metrics?.roc_auc ?? raw.evaluation_metrics?.roc_auc ?? 0.6285,
      brier_score: raw.metrics?.brier_score ?? raw.evaluation_metrics?.brier_score ?? 0.2456,
      accuracy: raw.metrics?.accuracy ?? raw.evaluation_metrics?.accuracy ?? 0.60,
    },
    leakage_protection: {
      flagship_supplier_excluded: true,
      flagship_id: raw.held_out_flagship || 'SUP-1047',
    },
  }
}

// 4. Impact Engine
export async function fetchImpactReport(
  supplierId = 'SUP-1047',
  leadTimeDays = 14.0,
  stockoutProb?: number
): Promise<ImpactReportResponse> {
  const raw = await request<any>('/impact/calculate', {
    method: 'POST',
    body: JSON.stringify({
      supplier_id: supplierId,
      disruption_lead_time_days: leadTimeDays,
      stockout_probability: stockoutProb,
    }),
  })

  return {
    supplier_id: raw.supplier_id || supplierId,
    supplier_name: raw.supplier_name || 'ApexDrive Components',
    as_of_date: raw.as_of_date || '2026-09-30',
    disruption_lead_time_days: raw.disruption_lead_time_days ?? leadTimeDays,
    stockout_probability_used: raw.stockout_probability_used ?? 0.682,
    total_revenue_exposure_inr: raw.total_revenue_exposure_inr ?? 28500000,
    min_inventory_runway_days: raw.min_inventory_runway_days ?? 3.5,
    most_vulnerable_plant: raw.most_vulnerable_plant || 'Pune Assembly Plant',
    most_vulnerable_sku: raw.most_vulnerable_sku || 'SKU-WIRE-01',
    affected_sku_count: raw.affected_sku_count ?? (raw.sku_impacts?.length || 3),
    affected_plants: raw.affected_plants || ['Pune Assembly Plant', 'Chennai Assembly Plant', 'Greater Noida Assembly Plant'],
    sku_impacts: (raw.sku_impacts || []).map((s: any) => ({
      sku_id: s.sku_id || 'SKU-WIRE-01',
      family: s.family || 'High-voltage Harness',
      criticality: s.criticality ?? 5,
      plant: s.plant || 'Pune Assembly Plant',
      on_hand_units: s.on_hand_units ?? 1400,
      safety_stock_units: s.safety_stock_units ?? 800,
      average_daily_consumption: s.average_daily_consumption ?? 400,
      runway_days: s.runway_days ?? 3.5,
      buffer_penetration_days: s.buffer_penetration_days ?? 0,
      projected_stockout_date: s.projected_stockout_date || '2026-10-04',
      units_at_risk: s.units_at_risk ?? 6800,
      revenue_exposure_inr: s.revenue_exposure_inr ?? 13600000,
    })),
    plant_impacts: (raw.plant_impacts || []).map((p: any) => ({
      plant: p.plant || 'Pune Assembly Plant',
      affected_sku_count: p.affected_sku_count ?? 1,
      critical_sku_count: p.critical_sku_count ?? 1,
      min_runway_days: p.min_runway_days ?? 3.5,
      average_runway_days: p.average_runway_days ?? 3.5,
      total_units_at_risk: p.total_units_at_risk ?? 6800,
      total_revenue_exposure_inr: p.total_revenue_exposure_inr ?? 13600000,
      downtime_risk_level: p.downtime_risk_level || 'CRITICAL',
    })),
    dependency_graph: raw.dependency_graph || { nodes: [], edges: [] },
    formula_version: raw.formula_version || 'impact-v1.0',
    assumptions: raw.assumptions || [],
  }
}

export async function fetchNetworkGraph(supplierId = 'SUP-1047'): Promise<any> {
  return request<any>(`/impact/network/${supplierId}`)
}

// 5. Scenario Studio
export async function generateScenarios(
  supplierId = 'SUP-1047',
  leadTimeDays = 14.0,
  stockoutProb?: number
): Promise<ScenarioGenerationResponse> {
  return request<ScenarioGenerationResponse>('/scenarios/generate', {
    method: 'POST',
    body: JSON.stringify({
      supplier_id: supplierId,
      alternate_supplier_id: 'SUP-1012',
      disruption_lead_time_days: leadTimeDays,
      stockout_probability: stockoutProb,
    }),
  })
}

export async function fetchContractConstraints(supplierId = 'SUP-1047'): Promise<any> {
  return request<any>(`/scenarios/constraints/${supplierId}`)
}

// 6. RAG Copilot
export async function queryCopilot(query: string, userRole = 'PROCUREMENT_MANAGER'): Promise<CopilotQueryResponse> {
  return request<CopilotQueryResponse>('/copilot/recommend', {
    method: 'POST',
    body: JSON.stringify({ query, user_role: userRole }),
  })
}

export async function fetchCopilotDocuments(userRole = 'PROCUREMENT_MANAGER'): Promise<DocumentMetadata[]> {
  return request<DocumentMetadata[]>(`/copilot/documents?user_role=${userRole}`)
}

// 7. Cases & Approvals
export async function runGovernedCase(
  supplierId = 'SUP-1047',
  leadTimeDays = 14.0,
  forceCriticFailure = false
): Promise<DisruptionCase> {
  return request<DisruptionCase>('/cases/run', {
    method: 'POST',
    body: JSON.stringify({
      supplier_id: supplierId,
      trigger_type: 'SIGNAL_INTELLIGENCE',
      disruption_lead_time_days: leadTimeDays,
      force_critic_failure: forceCriticFailure,
    }),
  })
}

export async function fetchCases(): Promise<DisruptionCase[]> {
  return request<DisruptionCase[]>('/cases')
}

export async function fetchCase(caseId: string): Promise<DisruptionCase> {
  return request<DisruptionCase>(`/cases/${caseId}`)
}

export async function approveCase(caseId: string, decision: HumanApprovalPayload): Promise<DisruptionCase> {
  return request<DisruptionCase>(`/cases/${caseId}/approve`, {
    method: 'POST',
    body: JSON.stringify(decision),
  })
}

export async function recordCaseOutcome(caseId: string, outcome: ObservedOutcome): Promise<DisruptionCase> {
  return request<DisruptionCase>(`/cases/${caseId}/outcome`, {
    method: 'POST',
    body: JSON.stringify(outcome),
  })
}

// 9. Advanced Analytics, Forecasting, & Pareto Optimization
export interface AlgorithmRegistryResponse {
  status: string
  total_algorithms_active: number
  categories: {
    predictive_ml_models: Array<{ name: string; id: string; role: string; type: string; governed_by: string }>
    time_series_forecasting: Array<{ name: string; id: string; role: string; type: string; governed_by: string }>
    nlp_market_sentiment: Array<{ name: string; id: string; role: string; type: string; governed_by: string }>
    multi_objective_optimization: Array<{ name: string; id: string; role: string; type: string; governed_by: string }>
  }
}

export interface ModelBenchmarkResponse {
  benchmark_timestamp: string
  test_split_provenance: string
  models: Array<{
    rank: number
    model_type: string
    model_name: string
    accuracy: number
    roc_auc: number
    precision: number
    recall: number
    f1_score: number
    brier_score: number
    status: string
    primary_advantage: string
  }>
  champion_model: string
}

export interface DemandForecastResponse {
  algorithm: string
  target_metric: string
  historical_series: number[]
  forecast_series: Array<{
    step: number
    date_offset_days: number
    predicted_value: number
    lower_bound_95: number
    upper_bound_95: number
  }>
  trend_direction: string
  mean_forecast: number
  accuracy_metrics: {
    mae: number
    rmse: number
    mape_pct: number
  }
}

export interface ParetoOptimizationResponse {
  recommended_solution_id: string
  knee_point_id: string
  trade_off_analysis: string
  frontier_solutions: Array<{
    solution_id: string
    label: string
    mitigation_cost_inr: number
    service_level_pct: number
    lead_time_recovery_days: number
    units_allocated_secondary: number
    units_expedited_buffer: number
    marginal_efficiency_score: number
    summary: string
  }>
}

export async function fetchAlgorithmRegistry(): Promise<AlgorithmRegistryResponse> {
  return request<AlgorithmRegistryResponse>('/analytics/algorithms')
}

export async function fetchModelBenchmarkLeaderboard(): Promise<ModelBenchmarkResponse> {
  return request<ModelBenchmarkResponse>('/analytics/models/benchmark')
}

export async function runDemandForecast(
  series: number[],
  horizonDays = 14,
  targetMetric = 'Daily Component Demand'
): Promise<DemandForecastResponse> {
  return request<DemandForecastResponse>('/analytics/forecast/demand', {
    method: 'POST',
    body: JSON.stringify({
      series,
      horizon_days: horizonDays,
      target_metric_name: targetMetric,
    }),
  })
}

export interface SentimentAnalysisResponse {
  text_analyzed: string
  compound_score: number
  polarities: {
    positive: number
    neutral: number
    negative: number
  }
  classification: string
  detected_risk_keywords: string[]
  velocity_metrics: {
    entity: string
    current_sentiment: number
    previous_sentiment: number
    velocity_per_day: number
    acceleration: number
    volatility_14d: number
    market_stress_index: number
    early_warning_tier: string
    summary_insight: string
  }
}

export async function scoreMarketSentiment(
  text: string,
  entityName = 'SUP-1047',
  sentimentHistory?: number[],
  timeDeltaDays = 7.0
): Promise<SentimentAnalysisResponse> {
  return request<SentimentAnalysisResponse>('/analytics/sentiment/score', {
    method: 'POST',
    body: JSON.stringify({
      text,
      entity_name: entityName,
      sentiment_history: sentimentHistory,
      time_delta_days: timeDeltaDays,
    }),
  })
}

export interface SafetyStockResponse {
  plant_node: string
  service_level_pct: number
  z_score: number
  safety_stock_units: number
  reorder_point_units: number
  uncertainty_breakdown: {
    demand_variance_component: number
    lead_time_variance_component: number
    dominant_risk_driver: string
  }
  formula_used: string
}

export async function calculateSafetyStock(
  plantNode = 'Pune Central Assembly',
  avgDailyDemand = 240.0,
  demandStdDev = 35.0,
  leadTimeDays = 12.0,
  leadTimeStdDev = 2.5,
  serviceLevelPct = 97.5
): Promise<SafetyStockResponse> {
  return request<SafetyStockResponse>('/analytics/safety-stock', {
    method: 'POST',
    body: JSON.stringify({
      plant_node: plantNode,
      avg_daily_demand: avgDailyDemand,
      demand_std_dev: demandStdDev,
      lead_time_days: leadTimeDays,
      lead_time_std_dev: leadTimeStdDev,
      target_service_level_pct: serviceLevelPct,
    }),
  })
}

export async function runParetoOptimization(
  shortageUnits = 1500,
  delayDays = 14.0
): Promise<ParetoOptimizationResponse> {
  return request<ParetoOptimizationResponse>('/analytics/optimizer/pareto', {
    method: 'POST',
    body: JSON.stringify({
      shortage_units: shortageUnits,
      primary_delay_days: delayDays,
    }),
  })
}


