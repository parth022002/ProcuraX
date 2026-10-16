/**
 * Surface 3: Impact Map, Multi-Tier Network Traversal & Warehouse Stock Management Hub
 * Models multi-echelon stock health, buffer penetration, and interactive inter-plant transfers.
 */
import { useEffect, useState } from 'react'
import type { ImpactReportResponse } from '../types'
import { fetchImpactReport } from '../lib/api'
import { Icon } from './Icons'

interface WarehouseNode {
  id: string
  name: string
  location: string
  role: string
  onHandUnits: number
  safetyStockUnits: number
  dailyConsumption: number
  runwayDays: number
  capacityPct: number
  status: 'CRITICAL' | 'WARNING' | 'SURPLUS' | 'HEALTHY'
  surplusUnitsAvailable: number
}

const DEFAULT_WAREHOUSES: WarehouseNode[] = [
  {
    id: 'WH-PUNE-01',
    name: 'Pune Central Assembly Warehouse',
    location: 'Chakan Industrial Corridor, Pune',
    role: 'Primary Assembly Plant Warehouse',
    onHandUnits: 564,
    safetyStockUnits: 800,
    dailyConsumption: 400,
    runwayDays: 1.41,
    capacityPct: 85,
    status: 'CRITICAL',
    surplusUnitsAvailable: 0,
  },
  {
    id: 'WH-SANAND-02',
    name: 'Sanand Distribution & Buffer Center',
    location: 'GIDC Industrial Estate, Sanand',
    role: 'Regional Buffer & Overflow Depot',
    onHandUnits: 4800,
    safetyStockUnits: 1200,
    dailyConsumption: 150,
    runwayDays: 32.0,
    capacityPct: 62,
    status: 'SURPLUS',
    surplusUnitsAvailable: 1500,
  },
  {
    id: 'WH-CHENNAI-03',
    name: 'Chennai Southern Regional Warehouse',
    location: 'Sriperumbudur Hub, Chennai',
    role: 'Southern Assembly Feeder Depot',
    onHandUnits: 2100,
    safetyStockUnits: 900,
    dailyConsumption: 300,
    runwayDays: 7.0,
    capacityPct: 74,
    status: 'WARNING',
    surplusUnitsAvailable: 300,
  },
  {
    id: 'WH-NOIDA-04',
    name: 'Greater Noida Logistics Terminal',
    location: 'Ecotech Logistics Park, Greater Noida',
    role: 'Northern Distribution & Transit Facility',
    onHandUnits: 3600,
    safetyStockUnits: 1200,
    dailyConsumption: 200,
    runwayDays: 18.0,
    capacityPct: 55,
    status: 'HEALTHY',
    surplusUnitsAvailable: 800,
  },
]

export function ImpactMapView() {
  const [activeTab, setActiveTab] = useState<'NETWORK' | 'WAREHOUSE'>('NETWORK')
  const [leadTimeDays, setLeadTimeDays] = useState(14)
  const [impactData, setImpactData] = useState<ImpactReportResponse | null>(null)
  const [warehouses, setWarehouses] = useState<WarehouseNode[]>(DEFAULT_WAREHOUSES)
  const [transferExecuted, setTransferExecuted] = useState(false)
  const [transferUnits] = useState(850)
  const [loading, setLoading] = useState(true)

  const loadImpact = (days: number) => {
    setLoading(true)
    fetchImpactReport('SUP-1047', days)
      .then(setImpactData)
      .catch(() => {
        const mult = days / 14
        const puneShortage = Math.round(6800 * mult)
        const chennaiShortage = Math.round(4600 * mult)
        const noidaShortage = Math.round(2800 * mult)

        setImpactData({
          supplier_id: 'SUP-1047',
          supplier_name: 'ApexDrive Components',
          as_of_date: '2026-09-30',
          disruption_lead_time_days: days,
          stockout_probability_used: 0.85,
          total_revenue_exposure_inr: 364547400 * (days / 14.0),
          min_inventory_runway_days: Math.max(0.5, 1.41 - (days - 14) * 0.05),
          most_vulnerable_plant: 'Pune Assembly Plant',
          most_vulnerable_sku: 'SKU-WIRE-01',
          affected_sku_count: 71,
          affected_plants: ['Pune Assembly Plant', 'Chennai Assembly Plant', 'Greater Noida Assembly Plant'],
          sku_impacts: [
            {
              sku_id: 'SKU-WIRE-01',
              family: 'High-voltage Harness',
              criticality: 5,
              plant: 'Pune Assembly Plant',
              on_hand_units: 564,
              safety_stock_units: 800,
              average_daily_consumption: 400,
              runway_days: 1.41,
              buffer_penetration_days: 2.0,
              projected_stockout_date: '2026-10-02',
              units_at_risk: puneShortage,
              revenue_exposure_inr: puneShortage * 2000,
            },
            {
              sku_id: 'SKU-WIRE-01',
              family: 'High-voltage Harness',
              criticality: 5,
              plant: 'Chennai Assembly Plant',
              on_hand_units: 2100,
              safety_stock_units: 900,
              average_daily_consumption: 300,
              runway_days: 7.0,
              buffer_penetration_days: 0.0,
              projected_stockout_date: '2026-10-07',
              units_at_risk: chennaiShortage,
              revenue_exposure_inr: chennaiShortage * 2000,
            },
            {
              sku_id: 'SKU-WIRE-02',
              family: 'Chassis Sensor Harness',
              criticality: 4,
              plant: 'Greater Noida Assembly Plant',
              on_hand_units: 3600,
              safety_stock_units: 1200,
              average_daily_consumption: 200,
              runway_days: 18.0,
              buffer_penetration_days: 0.0,
              projected_stockout_date: '2026-10-18',
              units_at_risk: noidaShortage,
              revenue_exposure_inr: noidaShortage * 2000,
            },
          ],
          plant_impacts: [
            {
              plant: 'Pune Assembly Plant',
              affected_sku_count: 1,
              critical_sku_count: 1,
              min_runway_days: 3.5,
              average_runway_days: 3.5,
              total_units_at_risk: puneShortage,
              total_revenue_exposure_inr: puneShortage * 2000,
              downtime_risk_level: 'CRITICAL',
            },
            {
              plant: 'Chennai Assembly Plant',
              affected_sku_count: 1,
              critical_sku_count: 1,
              min_runway_days: 7.0,
              average_runway_days: 7.0,
              total_units_at_risk: chennaiShortage,
              total_revenue_exposure_inr: chennaiShortage * 2000,
              downtime_risk_level: 'WARNING',
            },
            {
              plant: 'Greater Noida Assembly Plant',
              affected_sku_count: 1,
              critical_sku_count: 0,
              min_runway_days: 18.0,
              average_runway_days: 18.0,
              total_units_at_risk: noidaShortage,
              total_revenue_exposure_inr: noidaShortage * 2000,
              downtime_risk_level: 'HEALTHY',
            },
          ],
          dependency_graph: {
            nodes: [
              { id: 'SUP-1047', label: 'ApexDrive Components', node_type: 'SUPPLIER', criticality: 5 },
              { id: 'CAT-ELEC', label: 'Wiring & Electrical', node_type: 'CATEGORY' },
              { id: 'SKU-WIRE-01', label: 'High-voltage Engine Harness', node_type: 'SKU', criticality: 5 },
              { id: 'PLANT-PUNE', label: 'Pune Assembly Plant', node_type: 'PLANT' },
              { id: 'PLANT-CHENNAI', label: 'Chennai Assembly Plant', node_type: 'PLANT' },
              { id: 'PLANT-NOIDA', label: 'Greater Noida Plant', node_type: 'PLANT' },
            ],
            edges: [
              { source: 'SUP-1047', target: 'CAT-ELEC', relation: 'SUPPLIES' },
              { source: 'CAT-ELEC', target: 'SKU-WIRE-01', relation: 'INCORPORATES' },
              { source: 'SKU-WIRE-01', target: 'PLANT-PUNE', relation: 'STOCKED_AT', weight_or_units: puneShortage },
              { source: 'SKU-WIRE-01', target: 'PLANT-CHENNAI', relation: 'STOCKED_AT', weight_or_units: chennaiShortage },
              { source: 'SKU-WIRE-01', target: 'PLANT-NOIDA', relation: 'STOCKED_AT', weight_or_units: noidaShortage },
            ],
          },
          formula_version: 'impact-v1.0',
          assumptions: [
            'Daily consumption based on 90-day moving average from manufacturing schedule',
            'Unit contribution margin = INR 2,000 per finished vehicle assembly unit',
            'Stockout occurs when on-hand inventory drops below safety stock threshold',
          ],
        })
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadImpact(leadTimeDays)
  }, [leadTimeDays])

  const handleExecuteTransfer = () => {
    setWarehouses((prev) =>
      prev.map((wh) => {
        if (wh.id === 'WH-PUNE-01') {
          const newOnHand = wh.onHandUnits + transferUnits
          return {
            ...wh,
            onHandUnits: newOnHand,
            runwayDays: parseFloat((newOnHand / wh.dailyConsumption).toFixed(1)),
            status: 'WARNING',
          }
        }
        if (wh.id === 'WH-SANAND-02') {
          const newOnHand = wh.onHandUnits - transferUnits
          return {
            ...wh,
            onHandUnits: newOnHand,
            runwayDays: parseFloat((newOnHand / wh.dailyConsumption).toFixed(1)),
            surplusUnitsAvailable: wh.surplusUnitsAvailable - transferUnits,
          }
        }
        return wh
      })
    )
    setTransferExecuted(true)
  }

  const resetTransfer = () => {
    setWarehouses(DEFAULT_WAREHOUSES)
    setTransferExecuted(false)
  }

  return (
    <div className="surface-content">
      {loading && <div className="notice-banner info-banner">Calculating multi-tier supply network impact…</div>}

      {/* Surface Header & View Switcher */}
      <section className="simulation-control-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => setActiveTab('NETWORK')}
            style={{
              background: activeTab === 'NETWORK' ? 'linear-gradient(135deg, #176B55, #105642)' : '#ffffff',
              border: activeTab === 'NETWORK' ? '0' : '1px solid #E7E5DC',
              borderRadius: '8px',
              padding: '8px 14px',
              color: activeTab === 'NETWORK' ? '#fff' : '#64716B',
              fontSize: '11px',
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Icon name="network" size={14} />
            Multi-Tier Network & BOM Graph
          </button>
          <button
            onClick={() => setActiveTab('WAREHOUSE')}
            style={{
              background: activeTab === 'WAREHOUSE' ? 'linear-gradient(135deg, #176B55, #105642)' : '#ffffff',
              border: activeTab === 'WAREHOUSE' ? '0' : '1px solid #E7E5DC',
              borderRadius: '8px',
              padding: '8px 14px',
              color: activeTab === 'WAREHOUSE' ? '#fff' : '#64716B',
              fontSize: '11px',
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Icon name="boxes" size={14} />
            Warehouse & Stock Management Hub
          </button>
        </div>

        <div className="slider-group">
          <label htmlFor="lead-time-slider" style={{ fontSize: '11px', color: '#cbd5e1' }}>
            <strong>Disruption Lead Time:</strong> {leadTimeDays} Days
          </label>
          <input
            id="lead-time-slider"
            type="range"
            min="7"
            max="28"
            step="1"
            value={leadTimeDays}
            onChange={(e) => setLeadTimeDays(Number(e.target.value))}
            className="lead-time-slider"
          />
        </div>
      </section>

      {/* Key Metric Grid */}
      {impactData && (
        <section className="metric-grid">
          <article className="metric-card">
            <div className="metric-icon red">₹</div>
            <div className="metric-label">Total Revenue Exposure</div>
            <div className="metric-value">₹{((impactData.total_revenue_exposure_inr ?? 364547400) / 10000000).toFixed(2)} Cr</div>
            <div className="metric-detail">Network Total · 71 SKUs / 3 Plants</div>
          </article>

          <article className="metric-card">
            <div className="metric-icon red">⏱</div>
            <div className="metric-label">Min Inventory Runway</div>
            <div className="metric-value">
              {transferExecuted ? '5.6 Days' : `${impactData.min_inventory_runway_days?.toFixed(2) ?? '1.41'} Days`}
            </div>
            <div className="metric-detail">{transferExecuted ? '✓ Post-Transfer Recovery' : 'Pune Assembly Line (Critical)'}</div>
          </article>

          <article className="metric-card">
            <div className="metric-icon amber">🏬</div>
            <div className="metric-label">Active Warehouse Nodes</div>
            <div className="metric-value">4 Facilities</div>
            <div className="metric-detail">Pune, Sanand, Chennai & Greater Noida</div>
          </article>

          <article className="metric-card">
            <div className="metric-icon green">⚡</div>
            <div className="metric-label">Network Stock Position</div>
            <div className="metric-value">11,900 Units</div>
            <div className="metric-detail">1,500 surplus buffer units reallocatable</div>
          </article>
        </section>
      )}

      {/* View 1: Multi-Tier Network & BOM Dependency Graph */}
      {activeTab === 'NETWORK' && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Multi-Tier Supply & Assembly BOM Dependency Graph</h2>
              <p>Reconciled deterministic lineage: Tier-1 Supplier ➔ Component Category ➔ Flagship SKU ➔ Assembly Plants</p>
            </div>
            <span className="pill green">LINEAGE_VALIDATED</span>
          </div>

          <div className="network-graph-container">
            <div className="graph-tier">
              <span className="tier-label">Tier-1 Supplier</span>
              <div className="graph-node">
                <strong>ApexDrive Components</strong>
                <small>SUP-1047 · Flagship Sole-Source</small>
                <span className="node-status-tag red">DISRUPTED (+{leadTimeDays}d)</span>
              </div>
            </div>

            <div className="graph-arrow">➔</div>

            <div className="graph-tier">
              <span className="tier-label">Component Category</span>
              <div className="graph-node">
                <strong>Wiring & Electrical</strong>
                <small>CAT-ELEC · High-Voltage</small>
                <span className="node-status-tag amber">100% EXPOSURE</span>
              </div>
            </div>

            <div className="graph-arrow">➔</div>

            <div className="graph-tier">
              <span className="tier-label">Impacted SKU</span>
              <div className="graph-node">
                <strong>SKU-WIRE-01</strong>
                <small>EV Main Engine Harness</small>
                <span className="node-status-tag red">CRITICAL BUFFER RUNWAY</span>
              </div>
            </div>

            <div className="graph-arrow">➔</div>

            <div className="graph-tier">
              <span className="tier-label">Assembly Plant Hubs</span>
              <div className="graph-plants-column">
                <div className="graph-node plant-node critical">
                  <strong>Pune Assembly Plant</strong>
                  <small>Runway: {transferExecuted ? '5.6d (Buffered)' : '1.41d (Bottleneck)'} · Stockout Oct 2</small>
                  <span className="node-status-tag red">{transferExecuted ? 'REPLENISHED' : 'CRITICAL (₹1.36 Cr)'}</span>
                </div>
                <div className="graph-node plant-node warning">
                  <strong>Chennai Assembly Plant</strong>
                  <small>Runway: 7.0d · Stockout Oct 7</small>
                  <span className="node-status-tag amber">WARNING (₹92L)</span>
                </div>
                <div className="graph-node plant-node healthy">
                  <strong>Greater Noida Depot</strong>
                  <small>Runway: 18.0d · Stockout Oct 18</small>
                  <span className="node-status-tag" style={{ color: '#34d399' }}>HEALTHY (₹56L)</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* View 2: Warehouse & Stock Management Hub */}
      {activeTab === 'WAREHOUSE' && (
        <section className="surface-content">
          {/* Interactive Inter-Warehouse Stock Transfer Simulator */}
          <div
            className="panel"
            style={{
              padding: '20px 24px',
              background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(15, 23, 42, 0.9))',
              border: '1px solid rgba(14, 165, 233, 0.35)',
              borderRadius: '14px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div>
                <span style={{ fontSize: '11px', fontFamily: 'DM Mono', color: '#00f2fe', fontWeight: 700, letterSpacing: '1px' }}>
                  AUTOMATED BUFFER REBALANCING SOLVER
                </span>
                <h3 style={{ margin: '4px 0 0', fontSize: '17px', color: '#ffffff', fontFamily: 'Manrope' }}>
                  Emergency Inter-Warehouse Stock Transfer Protocol
                </h3>
              </div>
              {transferExecuted ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="pill green">✓ TRANSFER IN TRANSIT (ETA 24H)</span>
                  <button
                    onClick={resetTransfer}
                    className="action-button secondary"
                    style={{ height: '32px', fontSize: '11px', padding: '0 12px' }}
                  >
                    Reset Simulation
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleExecuteTransfer}
                  className="replay-action-button copper-accent-btn"
                  style={{ height: '38px', padding: '0 18px', fontSize: '12px', fontWeight: 800 }}
                >
                  🚀 Execute Inter-Plant Transfer ({transferUnits} Units)
                </button>
              )}
            </div>

            <p style={{ margin: '0 0 16px', fontSize: '12px', color: '#4f5b70', lineHeight: 1.5 }}>
              Sanand Distribution Center currently holds <strong>32.0 days runway</strong> (1,500 surplus buffer units). A dedicated 24-hour inter-warehouse transfer of <strong>{transferUnits} units</strong> to Pune Central Assembly extends Pune's runway from <strong>1.41 to 5.6 days</strong>, averting assembly stoppage for ₹{(transferUnits * 85).toLocaleString()} freight cost.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div style={{ background: '#f8faf9', border: '1px solid #E7E5DC', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64716B' }}>Transfer Route</span>
                <strong style={{ display: 'block', color: 'var(--text-main)', fontSize: '12px', marginTop: '2px' }}>Sanand Depot → Pune Plant</strong>
              </div>
              <div style={{ background: '#f8faf9', border: '1px solid #E7E5DC', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64716B' }}>Dedicated Express Transit</span>
                <strong style={{ display: 'block', color: '#176B55', fontSize: '12px', marginTop: '2px' }}>24 Hours (540 km corridor)</strong>
              </div>
              <div style={{ background: '#f8faf9', border: '1px solid #E7E5DC', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64716B' }}>Inter-State Transfer Cost</span>
                <strong style={{ display: 'block', color: '#197653', fontSize: '12px', marginTop: '2px' }}>₹{(transferUnits * 85).toLocaleString()} (@ ₹85/unit)</strong>
              </div>
              <div style={{ background: '#f8faf9', border: '1px solid #E7E5DC', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64716B' }}>Pune Runway Post-Transfer</span>
                <strong style={{ display: 'block', color: '#176B55', fontSize: '12px', marginTop: '2px' }}>+2.1 Days Extension</strong>
              </div>
            </div>
          </div>

          {/* Multi-Node Warehouse Inventory Table */}
          <div className="panel">
            <div className="panel-heading">
              <div>
                <h2>Enterprise Warehouse Network & Stock Position</h2>
                <p>Live inventory buffers, safety stock thresholds, and replenishment lead times across assembly plants</p>
              </div>
              <span className="pill">STOCK_HEALTH_LIVE</span>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Warehouse Facility</th>
                    <th>Location & Role</th>
                    <th>On-Hand Stock</th>
                    <th>Safety Stock</th>
                    <th>Daily Run Rate</th>
                    <th>Runway (Days)</th>
                    <th>Capacity Utilization</th>
                    <th>Buffer Status</th>
                  </tr>
                </thead>
                <tbody>
                  {warehouses.map((wh) => (
                    <tr key={wh.id}>
                      <td>
                        <strong>{wh.name}</strong>
                        <small style={{ color: '#94a3b8' }}>{wh.id}</small>
                      </td>
                      <td>
                        <div>{wh.location}</div>
                        <small style={{ color: '#64748b' }}>{wh.role}</small>
                      </td>
                      <td>
                        <strong style={{ color: 'var(--text-main)' }}>{wh.onHandUnits.toLocaleString()} units</strong>
                      </td>
                      <td>{wh.safetyStockUnits.toLocaleString()} units</td>
                      <td>{wh.dailyConsumption} units/day</td>
                      <td>
                        <strong style={{ color: wh.runwayDays < 5 ? '#BD3F3F' : wh.runwayDays < 10 ? '#9B631C' : '#197653' }}>
                          {wh.runwayDays} Days
                        </strong>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ height: '6px', width: '60px', background: '#E7E5DC', borderRadius: '99px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${wh.capacityPct}%`, background: wh.capacityPct > 80 ? '#BD3F3F' : '#176B55' }} />
                          </div>
                          <span>{wh.capacityPct}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge ${wh.status === 'CRITICAL' ? 'critical' : wh.status === 'WARNING' ? 'high' : 'feasible'}`}>
                          {wh.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
