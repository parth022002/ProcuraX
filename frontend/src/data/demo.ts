import type { Alert, Scenario } from '../types'

// Entire dataset is illustrative/synthetic UI data. Replace with API responses after endpoints pass tests.
export const alerts: Alert[] = [
  { supplierId: 'SUP-1047', supplier: 'ApexDrive Components', category: 'High-voltage Harnesses', score: 39.7, issue: 'Raw-material & Tooling Bottleneck', impact: 'Network ₹36.45 Cr', updated: '2h ago', status: 'Critical' },
  { supplierId: 'SUP-1012', supplier: 'ElectroMotion Systems', category: 'Approved Alternate Source', score: 24.0, issue: 'Capacity validation', impact: '50% Spare Capacity', updated: '5h ago', status: 'Review' },
  { supplierId: 'SUP-1033', supplier: 'Gamma Plastics', category: 'Moulded parts', score: 58.2, issue: 'Quality deterioration', impact: 'Medium Exposure', updated: '1d ago', status: 'High' },
]

export const scenarios: Scenario[] = [
  { name: 'Do nothing', detail: 'Keep current allocation', costDelta: 'Baseline', riskReduction: '0%', status: 'Feasible' },
  { name: 'Alternate supplier', detail: 'Shift feasible share to approved alternate', costDelta: '+8%', riskReduction: '65%', status: 'Feasible' },
  { name: 'Expedite / inventory', detail: 'Transfer stock and expedite selected orders', costDelta: '+12%', riskReduction: '58%', status: 'Review' },
  { name: 'Hybrid mitigation', detail: 'Supplier shift + targeted buffer transfer', costDelta: '+6%', riskReduction: '72%', status: 'Feasible' },
]
