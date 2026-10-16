# Repository structure

```text
ProcuraX_Starter_Kit/
├── PROJECT.md                       # Scope, users, objective, constraints, status
├── AGENTS.md                        # Persistent coding-agent rules
├── README.md                        # Setup, run, test, current limitations
├── .env.example                     # Placeholder configuration only
├── .gitignore
├── Makefile
├── docker-compose.yml               # Optional PostgreSQL/pgvector + Redis
├── .github/workflows/ci.yml         # Backend tests + frontend production build
├── docs/
│   ├── REQUIREMENTS.md               # FR-01..FR-15 + non-functional rules
│   ├── USER_FLOWS.md                 # Main journey and failure paths
│   ├── ARCHITECTURE.md               # Components and Mermaid data/decision flow
│   ├── DATABASE.md                   # Entities, relationships, leakage/provenance rules
│   ├── API_CONTRACTS.md              # Versioned endpoint contract and scaffold status
│   ├── DESIGN_SYSTEM.md              # UI palette and interaction principles
│   ├── IMPLEMENTATION_PLAN.md        # Sprints 0-9 and next actions
│   ├── TESTING.md                    # Unit/data/model/RAG/agent/API/E2E gates
│   ├── DECISIONS.md                  # Defaults, ADRs and open questions
│   ├── SECURITY_AND_DATA.md          # Secret, access, source and action controls
│   ├── BUILD_STATUS.md               # Evidence-backed scaffold status
│   ├── CODING_AGENT_START_PROMPT.md  # Safe first task for Codex/Cursor/etc.
│   ├── BLUEPRINT_TRACEABILITY.md     # v3.5 sections → repository files
│   └── REPOSITORY_STRUCTURE.md       # This file
├── backend/
│   ├── pyproject.toml                 # Python deps and test/lint configuration
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                    # FastAPI app + CORS + router
│   │   ├── core/config.py             # Environment settings
│   │   ├── api/v1/                    # Versioned route registrations
│   │   ├── schemas/                   # Shared response contracts
│   │   ├── services/                  # Business & intelligence service packages
│   │   │   ├── signal_intelligence/   # Signal ingestion, NLP, entity resolution
│   │   │   ├── risk_model/            # Baseline ML & calibrated 0-100 scoring
│   │   │   ├── impact_engine.py       # Versioned exposure & runway calculations
│   │   │   ├── optimizer/             # MILP/OR-Tools scenario constraint solver
│   │   │   ├── rag_copilot/           # Hybrid retrieval, citation & abstention
│   │   │   ├── agent_orchestrator/    # LangGraph state machine & 8-stage loop
│   │   │   ├── policy_engine.py       # Deterministic RBAC & approval thresholds
│   │   │   └── critic.py              # Multi-hypothesis evidence evaluator
│   │   └── db/schema.sql              # Draft schema; not auto-applied
│   └── tests/                         # Unit & integration test suites
├── frontend/
│   ├── package.json                   # React + Vite + TypeScript
│   ├── index.html / vite.config.ts / tsconfig.json
│   ├── public/procurax-neon-emblem.webp # Contained 3D neon emblem
│   └── src/
│       ├── App.tsx                    # Landing page + live preview switch
│       ├── Workspace.tsx              # Interactive 8-stage Control Tower
│       ├── data/demo.ts               # Explicitly synthetic UI values
│       ├── lib/api.ts                 # Health API client
│       ├── types.ts
│       └── styles.css
├── configs/                           # Thresholds, solver bounds, model configs
│   ├── data/
│   ├── models/
│   └── scenarios/
├── prompts/                           # Versioned prompts with injection guardrails
│   └── procurement_copilot/           # RAG extraction & explanation prompts
├── evaluation/                        # Benchmarks, ground truth, test cases
│   └── benchmarks/                    # Fixed RAG & decision replay benchmark sets
├── infra/                             # Deployment runbooks & container orchestration
├── scripts/
│   ├── generate_synthetic_data.py     # Fixed seed/as-of/scale generator + checksums
│   └── verify_repo.py                 # Required-file sanity check
├── data/
│   ├── raw/                           # Source inputs; ignored by Git
│   ├── generated/                     # Generated CSVs & checksums; ignored by Git
│   ├── curated/                       # Normalized entity tables; ignored by Git
│   ├── features/                      # Model-ready feature store; ignored by Git
│   └── processed/                     # Cleaned transformation outputs
├── models/
│   └── registry/                      # Serialized ML model artifacts & cards
└── artifacts/                         # Benchmark & evaluation runs; ignored by Git
```

## Why this split
The frontend handles presentation and user interactions; FastAPI owns request validation and services; deterministic Python utilities own domain calculations; PostgreSQL stores workflow state; pgvector is an optional retrieval store. ML, optimisation, RAG and orchestration are separate boundaries so the LLM cannot replace numerical or policy authority.
