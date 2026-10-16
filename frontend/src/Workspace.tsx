/**
 * ProcuraX Governed Decision Intelligence Workspace
 * Section 19/20: Governed Operational Suite
 * Streamlined Executive 8-Stage Decision Loop with 1-Click Guided Replay
 */
import { useEffect, useState } from 'react'
import './workspace.css'
import { fetchHealth, type HealthResponse } from './lib/api'
import { BrandLogo } from './components/BrandLogo'
import { Icon, type IconName } from './components/Icons'
import { ControlTowerView } from './components/ControlTowerView'
import { Supplier360View } from './components/Supplier360View'
import { ImpactMapView } from './components/ImpactMapView'
import { ScenarioStudioView } from './components/ScenarioStudioView'
import { EvidencePanelView } from './components/EvidencePanelView'
import { ApprovalWorkbenchView } from './components/ApprovalWorkbenchView'
import { OutcomeReviewView } from './components/OutcomeReviewView'
import { EvaluationDashboardView } from './components/EvaluationDashboardView'
import { IntegrationSettingsView } from './components/IntegrationSettingsView'
import { DataSourcesView } from './components/DataSourcesView'

// 7-Stage Governed Decision Loop Pipeline (Executive View)
export const PIPELINE_STAGES = [
  { id: 1, tab: 'Control Tower', name: 'Alert', desc: 'Signal Detection', badge: 'Active Disruption', color: '#BD3F3F' },
  { id: 2, tab: 'Supplier 360', name: 'Supplier 360', desc: 'Risk Scoring', badge: '78 / 100 Risk', color: '#9B631C' },
  { id: 3, tab: 'Impact Map', name: 'Impact', desc: 'Exposure & Runway', badge: '₹2.85 Cr at Risk', color: '#BD3F3F' },
  { id: 4, tab: 'Scenario Studio', name: 'Scenarios', desc: 'Constraint Solver', badge: '4 Feasible Plans', color: '#176B55' },
  { id: 5, tab: 'Evidence Panel', name: 'AI Evidence', desc: 'RAG & Critic Check', badge: 'Critic Verified', color: '#536F83' },
  { id: 6, tab: 'Approvals', name: 'Approvals', desc: 'Executive Sign-off', badge: 'CPO Required', color: '#197653' },
  { id: 7, tab: 'Outcome Review', name: 'Outcome', desc: 'Post-Decision Tracking', badge: 'Awaiting Outcome', color: '#536F83' },
]

interface NavItem {
  icon: IconName
  label: string
  tab: string
  desc?: string
}

const primaryNav: NavItem[] = [
  { icon: 'radio', label: 'Control Tower', tab: 'Control Tower', desc: 'Live Signals & Disruption Alert' },
  { icon: 'building', label: 'Supplier 360', tab: 'Supplier 360', desc: 'Risk Drivers & ML Model' },
  { icon: 'network', label: 'Impact Network', tab: 'Impact Map', desc: 'BOM Dependencies & Runway' },
  { icon: 'scale', label: 'Scenario Studio', tab: 'Scenario Studio', desc: 'Optimization Solver' },
  { icon: 'spark', label: 'AI Copilot & Evidence', tab: 'Evidence Panel', desc: 'Grounded Contract RAG' },
  { icon: 'shield', label: 'Executive Approvals', tab: 'Approvals', desc: 'Governed Sign-off & Audit' },
  { icon: 'history', label: 'Outcome Review', tab: 'Outcome Review', desc: 'Post-Decision Tracking' },
]

const adminNav: NavItem[] = [
  { icon: 'activity', label: 'Evaluation & Benchmarks', tab: 'Evaluation' },
  { icon: 'database', label: 'Data Sources & Scraper', tab: 'Data Sources' },
  { icon: 'settings', label: 'Integrations & DB', tab: 'Integrations' },
]

function Workspace({ onBack }: { onBack: () => void }) {
  const [activeTab, setActiveTab] = useState('Control Tower')
  const [selectedScenario, setSelectedScenario] = useState('SCN-D')
  const [currentStageIdx, setCurrentStageIdx] = useState(0)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState('')
  const [guidedMode, setGuidedMode] = useState(false)
  const [showAdminNav, setShowAdminNav] = useState(true)
  const [quickQueryText, setQuickQueryText] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((error: unknown) => {
        setHealthError(error instanceof Error ? error.message : 'API offline')
      })
  }, [])

  // Sync activeTab with current pipeline stage
  const jumpToStage = (stageIndex: number) => {
    const stage = PIPELINE_STAGES[stageIndex]
    if (stage) {
      setCurrentStageIdx(stageIndex)
      setActiveTab(stage.tab)
    }
  }

  const nextStage = () => {
    if (currentStageIdx < PIPELINE_STAGES.length - 1) {
      jumpToStage(currentStageIdx + 1)
    }
  }

  const prevStage = () => {
    if (currentStageIdx > 0) {
      jumpToStage(currentStageIdx - 1)
    }
  }

  const handleQuickCopilot = (text: string) => {
    setQuickQueryText(text)
    setActiveTab('Evidence Panel')
  }

  return (
    <div className="app-shell executive-theme">
      {/* Mobile Backdrop */}
      {mobileMenuOpen && (
        <div
          className="sidebar-backdrop active"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${mobileMenuOpen ? 'drawer-open' : ''}`}>
        <div className="brand-header-compact">
          <BrandLogo size="sm" variant="dark" companyName="ApexDrive" tagline="Enterprise Decision Intelligence" />
          <button
            className="sidebar-mobile-close-btn"
            aria-label="Close navigation menu"
            onClick={() => setMobileMenuOpen(false)}
          >
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* 1-Click Guided Decision Replay Button */}
        <button
          className={`btn-guided-replay-compact ${guidedMode ? 'active' : ''}`}
          onClick={() => {
            setGuidedMode(true)
            jumpToStage(0)
            setMobileMenuOpen(false)
          }}
        >
          <Icon name="play" size={13} />
          <span>{guidedMode ? 'Decision Replay Active' : 'Run 7-Stage Replay'}</span>
          <span className="live-dot" />
        </button>

        {/* Primary Operational Navigation */}
        <div className="nav-group-title">OPERATIONAL DECISION SUITE</div>
        <nav className="primary-nav" aria-label="Primary navigation">
          {primaryNav.map((item) => {
            const isActive = activeTab === item.tab
            return (
              <button
                key={item.label}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(item.tab)
                  const matchingStage = PIPELINE_STAGES.findIndex((s) => s.tab === item.tab)
                  if (matchingStage !== -1) setCurrentStageIdx(matchingStage)
                  setMobileMenuOpen(false)
                }}
              >
                <span className="nav-icon" aria-hidden="true">
                  <Icon name={item.icon} size={18} />
                </span>
                <div className="nav-text">
                  <span className="nav-title">{item.label}</span>
                  <span className="nav-sub">{item.desc}</span>
                </div>
              </button>
            )
          })}
        </nav>

        {/* Collapsible Admin & System Nav */}
        <div className="nav-group-title admin-title" onClick={() => setShowAdminNav(!showAdminNav)}>
          <span>SYSTEM & DATA CONNECTORS</span>
          <span className="toggle-indicator">{showAdminNav ? '▾' : '▸'}</span>
        </div>
        {showAdminNav && (
          <nav className="admin-nav" aria-label="System navigation">
            {adminNav.map((item) => (
              <button
                key={item.label}
                className={`admin-nav-item ${activeTab === item.tab ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(item.tab)
                  setMobileMenuOpen(false)
                }}
              >
                <span className="admin-icon">
                  <Icon name={item.icon} size={14} />
                </span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        )}

        {/* Sidebar Footer with Health & Background Algorithms Indicator */}
        <div className="sidebar-footer">
          <div className="conn-status">
            <span className={`status-dot ${health ? 'online' : 'offline'}`} />
            <div>
              <strong>{health ? 'FastAPI & AI Engines Active' : 'Fallback Engine Active'}</strong>
              <small>{health ? 'ML, Holt-Winters, NLP & Pareto in background' : (healthError || 'Connecting...')}</small>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-area">
        {/* Top Header with Single-Row Executive Command Bar */}
        <header className="executive-topbar">
          <div className="topbar-left-group">
            <button
              className="workspace-mobile-menu-btn"
              aria-label={mobileMenuOpen ? 'Close navigation drawer' : 'Open navigation drawer'}
              aria-expanded={mobileMenuOpen}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <Icon name={mobileMenuOpen ? 'x' : 'menu'} size={20} />
            </button>
            <div className="topbar-left">
              <div className="breadcrumbs">
                <span className="bc-root">ApexDrive</span>
                <span className="bc-sep">/</span>
                <span>Global Operations</span>
                <span className="bc-sep">/</span>
                <span className="bc-current">{activeTab}</span>
              </div>
              <h1 className="topbar-page-title">
                {activeTab}
                <span className="tenant-case-badge">Case #DISR-2026-1047</span>
              </h1>
            </div>
          </div>

          {/* Quick AI Copilot Search Bar */}
          <div className="topbar-copilot-search">
            <div className="copilot-search-wrap">
              <span className="search-icon">
                <Icon name="search" size={14} />
              </span>
              <input
                type="text"
                placeholder="Ask Copilot AI (e.g. Why is Hybrid recommended? Contract SLA)..."
                value={quickQueryText}
                onChange={(e) => setQuickQueryText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && quickQueryText.trim()) {
                    handleQuickCopilot(quickQueryText)
                  }
                }}
              />
              <button
                className="search-submit"
                onClick={() => {
                  if (quickQueryText.trim()) handleQuickCopilot(quickQueryText)
                }}
              >
                Ask Copilot
              </button>
            </div>
          </div>

          <div className="topbar-actions">
            <button className="btn-return-site" onClick={onBack}>
              ← Public Site
            </button>
            <div className="user-profile-badge">
              <div className="user-avatar">CPO</div>
              <div className="user-info">
                <strong>Chief Procurement Officer</strong>
                <small>Governed Role: CPO</small>
              </div>
            </div>
          </div>
        </header>

        {/* 8-Stage Governed Decision Pipeline Ribbon */}
        <div className="pipeline-ribbon-card">
          <div className="pipeline-header">
            <div className="pipeline-title-group">
              <span className="pipeline-kicker">GOVERNED DECISION LIFECYCLE</span>
              <h3>End-to-End Decision Journey · ApexDrive Components · Case #DISR-2026-1047</h3>
            </div>
            <div className="pipeline-controls">
              <button
                className="btn-step-prev"
                disabled={currentStageIdx === 0}
                onClick={prevStage}
              >
                ← Previous Stage
              </button>
              <span className="step-counter">
                Stage <strong>0{currentStageIdx + 1}</strong> / 0{PIPELINE_STAGES.length}
              </span>
              <button
                className="btn-step-next"
                disabled={currentStageIdx === PIPELINE_STAGES.length - 1}
                onClick={nextStage}
              >
                Next Stage →
              </button>
            </div>
          </div>

          {/* Stepper Timeline Bar */}
          <div className="pipeline-timeline">
            {PIPELINE_STAGES.map((stage, idx) => {
              const isCurrent = currentStageIdx === idx
              const isPast = currentStageIdx > idx
              return (
                <div
                  key={stage.id}
                  className={`timeline-step ${isCurrent ? 'current' : ''} ${isPast ? 'completed' : ''}`}
                  onClick={() => jumpToStage(idx)}
                >
                  <div className="timeline-node">
                    <span className="node-number">{isPast ? '✓' : `0${stage.id}`}</span>
                    <span className="node-glow" />
                  </div>
                  <div className="timeline-labels">
                    <span className="step-name">{stage.name}</span>
                    <span className="step-badge" style={{ color: stage.color }}>
                      {stage.badge}
                    </span>
                  </div>
                  {idx < PIPELINE_STAGES.length - 1 && <div className="timeline-connector" />}
                </div>
              )
            })}
          </div>
        </div>

        {/* Guided Step Narrative Banner (When in Guided Replay Mode) */}
        {guidedMode && (
          <div className="guided-narrative-banner">
            <div className="narrative-badge">STAGE 0{currentStageIdx + 1} GUIDED NARRATIVE</div>
            <div className="narrative-body">
              <strong>{PIPELINE_STAGES[currentStageIdx].name}: {PIPELINE_STAGES[currentStageIdx].desc}</strong>
              <p>
                {currentStageIdx === 0 && 'Signal intelligence detected port congestion and raw-material shortages for flagship supplier SUP-1047. Pune Plant inventory runway is critically down to 3.5 days.'}
                {currentStageIdx === 1 && 'Validated ML model computed a Disruption Probability of 86/100. SHAP explainability shows lead time variance and transit delays as the top drivers.'}
                {currentStageIdx === 2 && 'Exposure calculation mapped the shortage to Pune Plant and SKU-WIRE-01. Gross financial risk is €2.85 Cr without intervention.'}
                {currentStageIdx === 3 && 'Deterministic constraint solver generated 4 feasible mitigation plans. SCN-D (Hybrid Mitigation) achieves the optimal trade-off: 78% risk reduction with €420K cost.'}
                {currentStageIdx === 4 && 'Evidence Copilot grounded the recommendation against DOC-POL-DUAL-SOURCE Section 4.2 and DOC-MSA-APEX-2025. Critic verified evidence sufficiency.'}
                {currentStageIdx === 5 && 'Policy engine confirmed CPO authority. Executive sign-off authorizes partial shift of 3,500 units to secondary supplier ElectroMotion.'}
                {currentStageIdx === 6 && 'Decision execution tracked in the outcome review. Plant line maintained 98.4% uptime with €1.9M in net avoided downtime.'}
              </p>
            </div>
            <div className="narrative-actions">
              {currentStageIdx < PIPELINE_STAGES.length - 1 ? (
                <button className="btn-advance-narrative" onClick={nextStage}>
                  Advance to Stage 0{currentStageIdx + 2} ({PIPELINE_STAGES[currentStageIdx + 1].name}) →
                </button>
              ) : (
                <button className="btn-advance-narrative success" onClick={() => setGuidedMode(false)}>
                  ✓ Decision Replay Complete (Exit Guided Mode)
                </button>
              )}
            </div>
          </div>
        )}

        {/* Active View Surface Router */}
        <div className="workspace-view-container">
          {activeTab === 'Control Tower' && (
            <ControlTowerView
              onLaunchCase={() => {
                setGuidedMode(true)
                jumpToStage(1) // Advance smoothly to Supplier 360
              }}
            />
          )}

          {activeTab === 'Supplier 360' && <Supplier360View />}

          {activeTab === 'Impact Map' && <ImpactMapView />}

          {activeTab === 'Scenario Studio' && (
            <ScenarioStudioView
              onSelectScenario={(scenId) => {
                setSelectedScenario(scenId)
                jumpToStage(5) // Advance to Approvals
              }}
            />
          )}

          {activeTab === 'Evidence Panel' && <EvidencePanelView />}

          {activeTab === 'Approvals' && (
            <ApprovalWorkbenchView initialScenarioId={selectedScenario} />
          )}

          {activeTab === 'Outcome Review' && <OutcomeReviewView />}

          {activeTab === 'Evaluation' && <EvaluationDashboardView />}

          {activeTab === 'Integrations' && <IntegrationSettingsView />}

          {activeTab === 'Data Sources' && <DataSourcesView />}
        </div>

        {/* Enterprise Footer */}
        <footer className="workspace-footer">
          <div className="footer-left">
            <BrandLogo size="sm" variant="dark" showTagline={false} />
            <span>ProcuraX Governed Decision Intelligence · Master Blueprint v3.5</span>
          </div>
          <div className="footer-right">
            <span>Sense ➔ Predict ➔ Quantify ➔ Simulate ➔ Ground ➔ Govern ➔ Learn</span>
            <span className="audit-tag">● AUDIT LOGGED</span>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default Workspace
