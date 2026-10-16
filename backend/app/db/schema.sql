-- ProcuraX schema draft: review and convert into versioned migrations before use.
-- Run only on a disposable/local DB until the migration strategy is established.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS suppliers (
  supplier_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  location TEXT,
  strategic_flag BOOLEAN NOT NULL DEFAULT FALSE,
  annual_spend_inr NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (annual_spend_inr >= 0),
  base_reliability NUMERIC(5,4) CHECK (base_reliability BETWEEN 0 AND 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skus (
  sku_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  unit_contribution_margin_inr NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (unit_contribution_margin_inr >= 0),
  criticality SMALLINT NOT NULL DEFAULT 1 CHECK (criticality BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
  po_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  sku_id TEXT NOT NULL REFERENCES skus(sku_id),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  order_date DATE NOT NULL,
  promised_date DATE NOT NULL,
  actual_date DATE,
  status TEXT NOT NULL,
  CHECK (promised_date >= order_date)
);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_supplier_date ON purchase_orders(supplier_id, order_date);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_sku_date ON purchase_orders(sku_id, order_date);

CREATE TABLE IF NOT EXISTS inventory (
  inventory_id TEXT PRIMARY KEY,
  sku_id TEXT NOT NULL REFERENCES skus(sku_id),
  plant TEXT NOT NULL,
  on_hand_units INTEGER NOT NULL CHECK (on_hand_units >= 0),
  safety_stock_units INTEGER NOT NULL CHECK (safety_stock_units >= 0),
  average_daily_consumption NUMERIC(12,3) NOT NULL CHECK (average_daily_consumption >= 0),
  UNIQUE (sku_id, plant)
);

CREATE TABLE IF NOT EXISTS supplier_performance (
  performance_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  period_date DATE NOT NULL,
  otif NUMERIC(5,4) CHECK (otif BETWEEN 0 AND 1),
  lead_time_days NUMERIC(10,2) NOT NULL CHECK (lead_time_days >= 0),
  defect_rate NUMERIC(5,4) CHECK (defect_rate BETWEEN 0 AND 1),
  capacity_utilisation NUMERIC(5,4) CHECK (capacity_utilisation BETWEEN 0 AND 1),
  UNIQUE (supplier_id, period_date)
);

CREATE TABLE IF NOT EXISTS external_signals (
  signal_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT,
  source_timestamp TIMESTAMPTZ NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_type TEXT NOT NULL,
  supplier_id TEXT REFERENCES suppliers(supplier_id),
  region TEXT,
  material TEXT,
  severity NUMERIC(5,4) CHECK (severity BETWEEN 0 AND 1),
  source_credibility NUMERIC(5,4) CHECK (source_credibility BETWEEN 0 AND 1),
  is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
  provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
  content_hash VARCHAR(64),
  canonical_url TEXT,
  freshness_status VARCHAR(32) NOT NULL DEFAULT 'fresh',
  age_hours NUMERIC(8,2),
  persisted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_external_signals_content_hash ON external_signals(content_hash);
CREATE INDEX IF NOT EXISTS ix_external_signals_supplier_id ON external_signals(supplier_id);
CREATE INDEX IF NOT EXISTS ix_external_signals_event_type ON external_signals(event_type);

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'investigating',
  prediction_as_of TIMESTAMPTZ NOT NULL,
  trace_id TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS risk_scores (
  risk_id TEXT PRIMARY KEY,
  case_id TEXT REFERENCES cases(case_id),
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  scored_at TIMESTAMPTZ NOT NULL,
  prediction_probability NUMERIC(7,6) CHECK (prediction_probability BETWEEN 0 AND 1),
  governed_score SMALLINT CHECK (governed_score BETWEEN 0 AND 100),
  model_version TEXT NOT NULL,
  driver_values JSONB NOT NULL DEFAULT '{}'::jsonb,
  score_config_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  scenario_type TEXT NOT NULL,
  feasible BOOLEAN NOT NULL,
  infeasibility_reason TEXT,
  objective_value_inr NUMERIC(18,2),
  constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
  assumptions JSONB NOT NULL DEFAULT '{}'::jsonb,
  solver_version TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendations (
  recommendation_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  scenario_id TEXT REFERENCES scenarios(scenario_id),
  recommendation_text TEXT NOT NULL,
  evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  abstained BOOLEAN NOT NULL DEFAULT FALSE,
  prompt_version TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approvals (
  approval_id TEXT PRIMARY KEY,
  recommendation_id TEXT NOT NULL REFERENCES recommendations(recommendation_id),
  actor_id TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('approve','modify','request_evidence','reject','escalate')),
  reason TEXT NOT NULL,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  idempotency_key TEXT UNIQUE,
  policy_result JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS outcomes (
  outcome_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  decision_id TEXT,
  observed_at TIMESTAMPTZ NOT NULL,
  actual_otif NUMERIC(5,4),
  actual_service_level NUMERIC(5,4),
  actual_cost_inr NUMERIC(18,2),
  business_result JSONB NOT NULL DEFAULT '{}'::jsonb,
  outcome_label TEXT,
  dataset_partition TEXT NOT NULL DEFAULT 'post_decision'
);

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  supplier_id TEXT REFERENCES suppliers(supplier_id),
  category TEXT,
  title TEXT NOT NULL,
  source_uri TEXT,
  version_label TEXT,
  effective_date DATE,
  expiry_date DATE,
  access_tags TEXT[] NOT NULL DEFAULT '{}',
  content_sha256 TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id),
  chunk_index INTEGER NOT NULL,
  text_content TEXT NOT NULL,
  embedding vector,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS ix_document_chunks_document ON document_chunks(document_id);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id BIGSERIAL PRIMARY KEY,
  case_id TEXT REFERENCES cases(case_id),
  actor_id TEXT,
  event_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  trace_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);
