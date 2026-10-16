import { useEffect, useMemo, useState } from 'react'
import { scenarios } from './data/demo'
import Workspace from './Workspace'
import { BrandLogo } from './components/BrandLogo'

type IconName = 'arrow' | 'activity' | 'shield' | 'layers' | 'chart' | 'route' | 'check' | 'spark' | 'search' | 'boxes' | 'clock' | 'workflow' | 'play' | 'chevron' | 'target' | 'database' | 'refresh' | 'menu' | 'x' | 'lock'

const paths: Record<IconName, string> = {
  arrow: 'M5 12h14M13 5l7 7-7 7',
  activity: 'M3 12h4l3-8 4 16 3-8h4',
  shield: 'M12 3 20 6v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-3Z M8.5 12l2.2 2.2 4.8-5',
  layers: 'm12 3 9 5-9 5-9-5 9-5Z M3 12l9 5 9-5 M3 16l9 5 9-5',
  chart: 'M4 19V5 M4 19h17 M7 15l4-4 3 2 6-7',
  route: 'M5 18a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM19 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM7 16c5 0 2-9 10-9',
  check: 'm5 12 4 4L19 6',
  spark: 'm12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z M19 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3Z',
  search: 'm20 20-4.5-4.5 M18 10.5A7.5 7.5 0 1 1 3 10.5a7.5 7.5 0 0 1 15 0Z',
  boxes: 'm3 7 9-4 9 4-9 4-9-4Z M3 7v10l9 4 9-4V7 M12 11v10',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M12 7v5l3 2',
  workflow: 'M6 4h12v5H6z M2 15h8v5H2z M14 15h8v5h-8z M12 9v3M6 12h12M6 12v3M18 12v3',
  play: 'm8 5 11 7-11 7V5Z',
  chevron: 'm9 18 6-6-6-6',
  target: 'M12 3v3M12 18v3M3 12h3M18 12h3M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z M12 10v2l2 1',
  database: 'M12 3c5 0 9 1.3 9 3s-4 3-9 3-9-1.3-9-3 4-3 9-3Z M3 6v12c0 1.7 4 3 9 3s9-1.3 9-3V6 M3 12c0 1.7 4 3 9 3s9-1.3 9-3',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M5.5 9a7 7 0 0 1 11.8-2L20 12M4 12l2.7 5a7 7 0 0 0 11.8-2',
  menu: 'M4 6h16M4 12h16M4 18h16',
  x: 'M6 6l12 12M18 6 6 18',
  lock: 'M5 10h14v11H5z M8 10V7a4 4 0 0 1 8 0v3 M12 14v3',
}

function Icon({ name, size = 20, strokeWidth = 1.8 }: { name: IconName; size?: number; strokeWidth?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>
}

const stages = [
  { id: '01', name: 'Sense', headline: 'Catch the signal before it becomes the crisis.', detail: 'Approved supplier, operational and external signals converge in one investigation, with source and timestamp attached.', icon: 'activity' as IconName },
  { id: '02', name: 'Predict', headline: 'Turn supplier signals into explainable risk.', detail: 'A validated ML model estimates disruption probability; explainability surfaces the drivers behind the score.', icon: 'chart' as IconName },
  { id: '03', name: 'Quantify', headline: 'Translate risk into business exposure.', detail: 'Map suppliers to materials, plants and SKUs to calculate inventory runway, service impact and financial exposure.', icon: 'target' as IconName },
  { id: '04', name: 'Simulate', headline: 'Compare actions—not just alerts.', detail: 'Evaluate a baseline, alternate sourcing, expedite/inventory and hybrid options under explicit constraints.', icon: 'layers' as IconName },
  { id: '05', name: 'Recommend', headline: 'Make the reasoning inspectable.', detail: 'The recommendation links back to evidence, rejected alternatives and the assumptions that shaped the decision.', icon: 'search' as IconName },
  { id: '06', name: 'Govern', headline: 'Keep authority where it belongs.', detail: 'The Critic checks evidence. The deterministic policy engine controls permissions and material actions require human approval.', icon: 'shield' as IconName },
  { id: '07', name: 'Act', headline: 'Prepare the decision for controlled execution.', detail: 'Approved decisions become structured action packets with quantities, supplier, transfer detail and audit context.', icon: 'arrow' as IconName },
  { id: '08', name: 'Learn', headline: 'Close the loop with actual outcomes.', detail: 'Capture the realised KPI and outcome after the decision timestamp to support replay, evaluation and future learning.', icon: 'refresh' as IconName },
]

const features = [
  { n: '01', icon: 'activity' as IconName, title: 'Supplier risk intelligence', text: 'Combine OTIF, lead-time, quality, capacity and credible external signals. Investigate the drivers—not just the score.', tone: 'teal' },
  { n: '02', icon: 'chart' as IconName, title: 'Impact that holds up', text: 'Trace supplier exposure through material, plant and SKU dependencies with versioned, auditable calculations.', tone: 'violet' },
  { n: '03', icon: 'layers' as IconName, title: 'Constrained scenario studio', text: 'Compare feasible mitigation options against cost, capacity, MOQ, contractual and service-level constraints.', tone: 'lime' },
  { n: '04', icon: 'shield' as IconName, title: 'Evidence + governed action', text: 'Use cited contract and policy evidence, bounded retries, abstention and explicit human approval.', tone: 'coral' },
]

function App() {
  const getInitialView = (): 'site' | 'workspace' => {
    const hash = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : ''
    const path = typeof window !== 'undefined' ? window.location.pathname.toLowerCase() : ''
    const search = typeof window !== 'undefined' ? window.location.search.toLowerCase() : ''
    if (
      hash.startsWith('#/workspace') ||
      hash.startsWith('#/app') ||
      path.startsWith('/workspace') ||
      path.startsWith('/app') ||
      search.includes('view=workspace')
    ) {
      return 'workspace'
    }
    return 'site'
  }

  const [view, setView] = useState<'site' | 'workspace'>(getInitialView)

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.toLowerCase()
      if (hash.startsWith('#/workspace') || hash.startsWith('#/app')) {
        setView('workspace')
      } else if (hash === '' || hash === '#/' || hash === '#top') {
        setView('site')
      }
    }
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const openWorkspace = (tabSlug?: string) => {
    setView('workspace')
    window.location.hash = tabSlug ? `#/workspace/${tabSlug}` : '#/workspace'
    window.scrollTo(0, 0)
  }

  const backToSite = () => {
    setView('site')
    window.location.hash = '#/'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return view === 'workspace' ? (
    <Workspace onBack={backToSite} />
  ) : (
    <LandingPage onLaunch={() => openWorkspace()} />
  )
}

function LandingPage({ onLaunch }: { onLaunch: () => void }) {
  const [activeStage, setActiveStage] = useState(0)
  const [selectedScenario, setSelectedScenario] = useState('Hybrid mitigation')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const scenario = useMemo(() => scenarios.find((item) => item.name === selectedScenario) ?? scenarios[0], [selectedScenario])
  const currentStage = stages[activeStage]

  const goTo = (id: string) => {
    setMobileNavOpen(false)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="site-shell">
      <div className="site-ambient site-ambient-one" />
      <div className="site-ambient site-ambient-two" />
      <header className="site-nav">
        <a className="site-brand" href="#top" aria-label="ProcuraX home" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
          <BrandLogo size="md" variant="dark" tagline="AI Decision Intelligence" />
        </a>
        <nav className={`site-nav-links ${mobileNavOpen ? 'is-open' : ''}`} aria-label="Website navigation">
          <button onClick={() => goTo('platform')}>Platform</button>
          <button onClick={() => goTo('decision-loop')}>Decision loop</button>
          <button onClick={() => goTo('governance')}>Trust & governance</button>
          <button
            onClick={() => {
              setMobileNavOpen(false)
              onLaunch()
            }}
            style={{
              color: '#d97706',
              fontWeight: 800,
              borderTop: mobileNavOpen ? '1px solid rgba(255,255,255,0.1)' : 'none',
              paddingTop: mobileNavOpen ? '12px' : undefined,
            }}
          >
            Launch Workspace Console →
          </button>
        </nav>
        <div className="site-nav-actions">
          <button className="site-text-button" onClick={onLaunch}>Workspace preview <Icon name="chevron" size={15}/></button>
          <button className="site-cta site-cta-small" onClick={onLaunch}>Explore ProcuraX <Icon name="arrow" size={15}/></button>
        </div>
        <button
          className="mobile-quick-workspace-btn"
          aria-label="Open Workspace Preview"
          onClick={onLaunch}
          style={{
            display: 'none',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '6px',
            backgroundColor: '#176B55',
            color: '#ffffff',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Workspace →
        </button>
        <button className="mobile-menu-button" aria-label={mobileNavOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setMobileNavOpen(!mobileNavOpen)}><Icon name={mobileNavOpen ? 'x' : 'menu'} size={22}/></button>
      </header>

      <main id="top">
        <section className="hero-section">
          <div className="hero-copy reveal-up">
            <div className="eyebrow-pill"><span className="eyebrow-pulse"/> AGENTIC AI · ENTERPRISE DECISION INTELLIGENCE · POWERED BY PROCURAX</div>
            <h1>Don’t just see the risk.<br/><span className="headline-gradient">Know the next move.</span></h1>
            <p className="hero-lead">ProcuraX turns scattered supplier signals into quantified exposure, feasible mitigation plans and evidence-backed decisions—with human control built in.</p>
            <div className="hero-actions">
              <button className="site-cta" onClick={onLaunch}>Explore the control tower <Icon name="arrow" size={17}/></button>
              <button className="site-secondary-cta" onClick={() => goTo('decision-loop')}><span className="play-icon"><Icon name="play" size={12}/></span> See how it works</button>
            </div>
            <div className="hero-proof-row"><div className="proof-avatars"><span>R</span><span>AI</span><span>✓</span></div><div><strong>Intelligence with a control layer.</strong><small>Evidence first. Human approval where it matters.</small></div></div>
            <div className="hero-caption"><span className="caption-line"/> GOVERNED SUPPLY CHAIN DECISION INTELLIGENCE</div>
          </div>

          <div className="hero-visual reveal-up delay-2" aria-label="ProcuraX visual identity and illustrative supplier investigation">
            <div className="visual-grid"/>
            <div className="visual-orbit orbit-one"/><div className="visual-orbit orbit-two"/>
            <div className="visual-glow visual-glow-a"/><div className="visual-glow visual-glow-b"/>
            <div className="hero-art-frame"><img className="hero-art" src="/procurax-neon-emblem.webp" alt="Abstract ProcuraX emblem representing supply chain intelligence, connected signals and business growth"/></div>
            <div className="float-card signal-card"><div className="float-card-icon signal-icon"><Icon name="activity" size={17}/></div><div><small>SUPPLIER SIGNAL</small><strong>Disruption detected</strong><span><i/> SUP-1047 · Tier-1 High-Voltage Harness</span></div><span className="signal-score">86</span></div>
            <div className="float-card evidence-card"><div className="evidence-check"><Icon name="check" size={14}/></div><div><small>CRITIC CHECK</small><strong>Evidence sufficient</strong><span>3 source groups reviewed</span></div></div>
            <div className="float-card action-card"><div className="action-icon"><Icon name="shield" size={16}/></div><div><small>NEXT STEP</small><strong>Approval required</strong></div><span className="action-dot"/>
            </div>
            <div className="visual-bottom-label"><span className="tiny-wave"><i/><i/><i/><i/><i/></span><span>ProcuraX Decision Intelligence Platform</span><span className="visual-bottom-status">● LIVE DEMO</span></div>
          </div>
        </section>

        <section className="ribbon-section" aria-label="Core process">
          <div className="ribbon-label">PROCURAX GOVERNED DECISION LIFECYCLE · CLOSED LOOP</div>
          <div className="process-ribbon">{stages.map((stage, i) => <button key={stage.id} className={i === activeStage ? 'ribbon-step active' : 'ribbon-step'} onClick={() => { setActiveStage(i); goTo('decision-loop') }}><span>{stage.id}</span>{stage.name}{i !== stages.length - 1 && <b>→</b>}</button>)}</div>
        </section>

        <section className="section section-preview" id="product-preview">
          <div className="section-heading-block reveal-up"><span className="section-kicker">EXECUTIVE CONTROL TOWER</span><h2>From a noisy signal<br/>to a decision you can defend.</h2><p>One clear workspace connects supplier health, financial exposure, scenario trade-offs and the evidence behind the recommendation.</p></div>
          <div className="product-frame reveal-up delay-1">
            <div className="product-window-bar"><div className="window-dots"><i/><i/><i/></div><div className="window-address"><Icon name="lock" size={12}/> app.procurax.ai / operations / control-tower</div><div className="product-live"><span/> LIVE PREVIEW</div></div>
            <div className="product-ui">
              <aside className="product-sidebar"><div className="product-mini-brand"><span className="mini-symbol"><Icon name="workflow" size={18}/></span><strong>Procura<span>X</span></strong></div><small className="product-sidebar-label">OPERATIONS COCKPIT</small><div className="product-nav-item current"><Icon name="layers" size={16}/> Control Tower</div><div className="product-nav-item"><Icon name="boxes" size={16}/> Suppliers</div><div className="product-nav-item"><Icon name="activity" size={16}/> Investigations</div><div className="product-nav-item"><Icon name="chart" size={16}/> Impact analysis</div><div className="product-nav-item"><Icon name="shield" size={16}/> Approvals</div><div className="product-sidebar-bottom"><span className="mini-status-dot"/> System Active</div></aside>
              <div className="product-main">
                <div className="product-main-top"><div><small>GLOBAL SUPPLY CHAIN OPERATIONS</small><h3>Control Tower</h3><p>Prioritise the issues that can move your supply chain.</p></div><button className="product-date"><Icon name="clock" size={13}/> Recent signals <Icon name="chevron" size={13}/></button></div>
                <div className="product-kpis"><div className="product-kpi"><span>Critical suppliers</span><strong>05 <em className="kpi-red">↑ 2</em></strong><small>Illustrative queue</small></div><div className="product-kpi"><span>Open investigations</span><strong>12</strong><small>Across supplier signals</small></div><div className="product-kpi"><span>Exposure at risk</span><strong>₹28.4<small>Cr</small></strong><small>Illustrative scenario only</small></div></div>
                <div className="product-lower-grid"><div className="product-panel risk-chart-panel"><div className="product-panel-top"><div><strong>Risk signal movement</strong><small>Illustrative index · 30 days</small></div><span className="chart-legend"><i/> Risk index</span></div><div className="chart-content"><div className="chart-y-labels"><span>100</span><span>75</span><span>50</span><span>25</span><span>0</span></div><div className="chart-plot"><div className="chart-gridlines"><i/><i/><i/><i/><i/></div><svg className="risk-svg" viewBox="0 0 500 154" preserveAspectRatio="none" aria-label="Illustrative supplier risk rises over time"><defs><linearGradient id="riskFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#176B55" stopOpacity=".25"/><stop offset="100%" stopColor="#176B55" stopOpacity="0"/></linearGradient></defs><path className="chart-area-path" d="M0,126 C28,118 42,111 64,116 S102,90 128,99 S167,83 193,92 S228,62 253,70 S295,79 315,60 S349,51 372,57 S410,23 435,30 S470,18 500,9 L500,154 L0,154Z" fill="url(#riskFill)"/><path className="chart-line-path" d="M0,126 C28,118 42,111 64,116 S102,90 128,99 S167,83 193,92 S228,62 253,70 S295,79 315,60 S349,51 372,57 S410,23 435,30 S470,18 500,9" fill="none" stroke="#176B55" strokeWidth="3" strokeLinecap="round"/><circle cx="500" cy="9" r="5" fill="#E58B45" stroke="#176B55" strokeWidth="2.5"/></svg><div className="chart-x-labels"><span>Wk 1</span><span>Wk 2</span><span>Wk 3</span><span>Wk 4</span><span>Today</span></div></div></div><div className="chart-caption"><span><i className="chart-caption-dot"/> Illustrative signal pattern</span><span>Explore investigation →</span></div></div>
                  <div className="product-panel supplier-panel"><div className="product-panel-top"><div><strong>Priority investigation</strong><small>Sorted by risk × impact</small></div><button aria-label="View priority investigations"><Icon name="arrow" size={15}/></button></div><div className="supplier-preview-row"><span className="supplier-monogram">A</span><div className="supplier-preview-name"><strong>Apex Precision Engineering</strong><small>SUP-1047 · Raw-material shortage</small><div className="risk-progress"><i style={{width:'86%'}}/></div></div><span className="supplier-score">86</span></div><div className="supplier-preview-row"><span className="supplier-monogram alt">G</span><div className="supplier-preview-name"><strong>Gamma Plastics</strong><small>SUP-1033 · Quality decline</small><div className="risk-progress amber"><i style={{width:'61%'}}/></div></div><span className="supplier-score medium-score">61</span></div><div className="supplier-preview-row"><span className="supplier-monogram blue">E</span><div className="supplier-preview-name"><strong>ElectroMotion</strong><small>SUP-1012 · Capacity check</small><div className="risk-progress green"><i style={{width:'34%'}}/></div></div><span className="supplier-score low-score">34</span></div><div className="supplier-panel-footer"><span>Example data only</span><span>Open supplier view <Icon name="arrow" size={12}/></span></div></div></div>
              </div>
            </div>
          </div>
          <div className="preview-caption"><span><Icon name="shield" size={15}/> Built for explainability and governed decisions</span><span>Illustrative UI · not live system data</span></div>
        </section>

        <section className="section decision-section" id="decision-loop">
          <div className="section-heading-block centered reveal-up"><span className="section-kicker">THE INTELLIGENCE LOOP</span><h2>Not another dashboard.<br/><span className="headline-gradient">A decision system.</span></h2><p>Every stage moves the investigation forward. Select a stage to see the role it plays in the decision.</p></div>
          <div className="stage-explorer reveal-up delay-1">
            <div
              className="stage-track"
              style={{ '--stage-progress': `${(activeStage / (stages.length - 1)) * 87.5}%` } as React.CSSProperties}
              aria-label="Interactive eight-stage decision loop"
            >
              {stages.map((stage, index) => (
                <button
                  key={stage.id}
                  type="button"
                  className={`stage-tab ${activeStage === index ? 'selected' : ''} ${index < activeStage ? 'visited' : ''}`}
                  onClick={() => setActiveStage(index)}
                >
                  <span className="stage-tab-no">{stage.id}</span>
                  <span className="stage-tab-icon"><Icon name={stage.icon} size={20}/></span>
                  <strong>{stage.name}</strong>
                </button>
              ))}
            </div>
            <div className="stage-detail-card"><div className="stage-detail-main"><div className={`stage-big-icon stage-tone-${activeStage % 4}`}><Icon name={currentStage.icon} size={25}/></div><div className="stage-detail-label">STAGE {currentStage.id} / 08</div><h3>{currentStage.headline}</h3><p>{currentStage.detail}</p><div className="stage-detail-arrows"><button disabled={activeStage === 0} onClick={() => setActiveStage(Math.max(0, activeStage - 1))}>← Previous</button><button disabled={activeStage === stages.length - 1} onClick={() => setActiveStage(Math.min(stages.length - 1, activeStage + 1))}>Next stage <Icon name="arrow" size={14}/></button></div></div><div className="stage-visual"><div className="stage-visual-core"><div className="core-pulse pulse-one"/><div className="core-pulse pulse-two"/><div className="core-orb"><Icon name={currentStage.icon} size={33}/></div><div className="core-orbit orbit-alpha"/><div className="core-orbit orbit-beta"/><span className="core-node node-a"/><span className="core-node node-b"/><span className="core-node node-c"/><span className="core-node node-d"/></div><div className="stage-visual-tag tag-a"><span/><small>{activeStage < 2 ? 'SIGNAL LAYER' : activeStage < 5 ? 'DECISION LAYER' : 'GOVERNED ACTION'}</small></div><div className="stage-visual-tag tag-b"><Icon name="check" size={13}/><small>TRACEABLE BY DESIGN</small></div></div></div>
          </div>
          <div className="loop-under-note"><span className="loop-line"/><Icon name="refresh" size={18}/><span>The outcome feeds the next decision. The loop stays closed.</span></div>
        </section>

        <section className="section capabilities-section" id="platform">
          <div className="capabilities-heading reveal-up"><div className="section-heading-block"><span className="section-kicker">THE PLATFORM</span><h2>Everything connected.<br/>Every decision accountable.</h2></div><p>Built around the supplier disruption use case—from early signals to approved mitigation and measurable outcomes.</p></div>
          <div className="capability-grid">{features.map((feature, i) => <article className={`capability-card capability-${feature.tone} reveal-up delay-${i + 1}`} key={feature.n}><div className="capability-top"><span className="capability-icon"><Icon name={feature.icon} size={21}/></span><span className="capability-number">{feature.n}</span></div><h3>{feature.title}</h3><p>{feature.text}</p><div className="capability-line"><span/><span/><span/></div><button onClick={() => { setActiveStage([0, 2, 3, 5][i]); goTo('decision-loop') }}>Explore capability <Icon name="arrow" size={14}/></button><div className="capability-glow"/></article>)}</div>
        </section>

        <section className="scenario-section" id="scenarios">
          <div className="scenario-inner"><div className="scenario-copy reveal-up"><span className="section-kicker section-kicker-dark">SCENARIO STUDIO</span><h2>Don’t guess the fix.<br/><span>Compare the trade-offs.</span></h2><p>ProcuraX puts feasible mitigation options side by side, so the team can see what changes in cost, risk and continuity before approving an action.</p><div className="scenario-proof-list"><span><Icon name="check" size={15}/> Feasibility under explicit constraints</span><span><Icon name="check" size={15}/> Comparable cost and risk measures</span><span><Icon name="check" size={15}/> A human-owned approval decision</span></div><button className="scenario-main-cta" onClick={onLaunch}>Open scenario workspace <Icon name="arrow" size={16}/></button><small className="scenario-disclaimer">Scenario values below are illustrative and not solver output.</small></div>
            <div className="scenario-ui reveal-up delay-2"><div className="scenario-ui-head"><div><span className="mini-overline">SUPPLIER SUP-1047</span><h3>Mitigation comparison</h3></div><span className="scenario-ui-chip"><i/> Illustrative</span></div><div className="scenario-options">{scenarios.map((item) => <button key={item.name} className={`scenario-option ${selectedScenario === item.name ? 'scenario-active' : ''}`} onClick={() => setSelectedScenario(item.name)}><span className="scenario-option-radio">{selectedScenario === item.name && <i/>}</span><span className="scenario-option-body"><strong>{item.name}</strong><small>{item.detail}</small></span><span className="scenario-option-metric"><b>{item.riskReduction}</b><small>risk reduction</small></span><span className="scenario-option-arrow"><Icon name="chevron" size={16}/></span></button>)}</div><div className="scenario-recommendation"><div className="scenario-rec-icon"><Icon name="spark" size={18}/></div><div className="scenario-rec-copy"><span>SELECTED OPTION</span><strong>{scenario.name}</strong><p>{scenario.detail}. Cost impact: {scenario.costDelta}; indicative risk reduction: {scenario.riskReduction}.</p></div><div className="scenario-rec-status"><span className={scenario.status === 'Feasible' ? 'scenario-status-green' : 'scenario-status-amber'}>{scenario.status}</span></div></div><div className="scenario-ui-footer"><span><Icon name="shield" size={14}/> Final feasibility must be solver-validated</span><span>Compare view <Icon name="arrow" size={12}/></span></div></div>
          </div>
        </section>

        <section className="section governance-section" id="governance">
          <div className="governance-copy reveal-up"><span className="section-kicker">AUTONOMY WITH BOUNDARIES</span><h2>AI can investigate.<br/><span>Policy decides.</span></h2><p>The Critic checks whether evidence is sufficient and identifies the next gap. It does not invent numerical outputs or authorise an action. The policy engine enforces permission; a human approves material decisions.</p><button className="governance-cta" onClick={() => goTo('trust-details')}>See the control model <Icon name="arrow" size={15}/></button></div>
          <div className="governance-visual reveal-up delay-1"><div className="governance-scanline"/><div className="governance-card-header"><span className="governance-pulse"/><span>INVESTIGATION TRACE</span><span className="governance-card-label">BOUNDED LOOP</span></div><div className="governance-flow"><div className="governance-node completed"><span className="gov-node-icon"><Icon name="search" size={16}/></span><div><strong>Retrieve evidence</strong><small>Internal data + approved sources</small></div><span className="gov-state">DONE</span></div><div className="gov-connector"><i/></div><div className="governance-node completed"><span className="gov-node-icon violet"><Icon name="activity" size={16}/></span><div><strong>Critic evaluates</strong><small>Evidence sufficient? Identify a specific gap.</small></div><span className="gov-state">CHECKED</span></div><div className="gov-connector animated-connector"><i/></div><div className="governance-node retry-node"><span className="gov-node-icon amber"><Icon name="refresh" size={16}/></span><div><strong>One targeted retry</strong><small>Only if evidence is insufficient</small></div><span className="gov-retry">MAX 1</span></div><div className="gov-connector"><i/></div><div className="governance-outcomes"><div className="gov-outcome success"><Icon name="check" size={16}/><div><strong>Evidence sufficient</strong><small>Continue decision loop</small></div></div><div className="gov-outcome escalate"><Icon name="shield" size={16}/><div><strong>Still insufficient</strong><small>Escalate to human</small></div></div></div></div><div className="governance-card-foot"><Icon name="lock" size={15}/> Policy engine retains action authority <span>● AUDIT LOGGED</span></div></div>
        </section>

        <section className="trust-strip" id="trust-details"><div className="trust-strip-title"><span className="section-kicker">BUILT TO BE DEFENSIBLE</span><h2>Trust isn't a colour.<br/>It's part of the workflow.</h2></div><div className="trust-points"><div><span className="trust-icon"><Icon name="database" size={19}/></span><strong>Traceable data</strong><small>Source, timestamp, lineage and cutoff controls.</small></div><div><span className="trust-icon"><Icon name="shield" size={19}/></span><strong>Policy enforcement</strong><small>Deterministic rules and named approvals.</small></div><div><span className="trust-icon"><Icon name="refresh" size={19}/></span><strong>Replayable outcomes</strong><small>Versioned decisions and measured feedback.</small></div></div></section>

        <section className="closing-cta"><div className="closing-orb orb-left"/><div className="closing-orb orb-right"/><div className="closing-content reveal-up"><span className="section-kicker section-kicker-dark">A BETTER WAY TO DECIDE</span><h2>Turn uncertainty into<br/><span>your next clear move.</span></h2><p>Explore the ProcuraX decision workspace. Start with one supplier incident and follow the evidence all the way to outcome.</p><button className="closing-button" onClick={onLaunch}>Enter workspace preview <Icon name="arrow" size={16}/></button><small>Illustrative prototype · synthetic scenario · core business services still in development</small></div><div className="closing-path"><i/><i/><i/><i/><i/><i/><span/></div></section>
      </main>
      <footer className="site-footer"><a className="site-brand footer-brand" href="#top" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}><BrandLogo size="md" variant="dark" tagline="AI Decision Intelligence" /></a><div className="footer-tagline">See the signal. Understand the impact. Govern the action.</div><div className="footer-meta"><span>© 2026 ProcuraX Concept</span><span><i/> Enterprise Decision Intelligence Platform</span></div></footer>
    </div>
  )
}

export default App
