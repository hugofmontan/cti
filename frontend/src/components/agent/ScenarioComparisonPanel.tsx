import type { AgentScenarioComparisonArtifact } from '../../types'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartContainer } from '../charts'
import { Table } from '../ui'
import { fmtBRL, fmtMillions, fmtPct, fmtNumber } from '../../utils/formatters'

interface ScenarioComparisonPanelProps {
  artifact: AgentScenarioComparisonArtifact
}

function toNumberOrZero(v: unknown) {
  const n = typeof v === 'number' ? v : typeof v === 'string' ? Number(v) : NaN
  return Number.isFinite(n) ? n : 0
}

function unitForMetric(metricKey: string | undefined) {
  // Hoje o painel de comparação de cenários só usa EV e Equity.
  if (!metricKey) return null
  if (metricKey === 'enterprise_value' || metricKey === 'equity_value') return 'BRL'
  if (metricKey.includes('margin') || metricKey.includes('pct') || metricKey.includes('perc')) return '%'
  return null
}

function formatMetricValue(metricKey: string, value: unknown) {
  const n = toNumberOrZero(value)
  const unit = unitForMetric(metricKey)
  if (unit === 'BRL') return fmtBRL(n)
  if (unit === '%') return fmtPct(n)
  return fmtNumber(n)
}

function formatDeltaValue(value: unknown) {
  // delta_vs_base é uma razão (ex.: 0.15 -> +15%)
  const n = toNumberOrZero(value)
  return fmtPct(n)
}

export function ScenarioComparisonPanel({ artifact }: ScenarioComparisonPanelProps) {
  const scenarios = artifact.scenarios ?? []
  if (scenarios.length === 0) return null

  const base = scenarios.find((s) => s.label === artifact.base_label) ?? scenarios[0]
  const metricKeys = Object.keys(base.key_metrics ?? {}).slice(0, 4)

  const chartMetric = metricKeys[0] ?? null
  const chartUnit = unitForMetric(chartMetric ?? undefined)
  const chartData =
    chartMetric &&
    scenarios.map((s) => ({
      x: s.label,
      value: toNumberOrZero(s.key_metrics?.[chartMetric]),
    }))

  const scenarioLabels = scenarios.map((s) => s.label)

  const columns = [
    { key: 'metric', header: 'Métrica', align: 'left' as const },
    ...scenarioLabels.map((label) => ({
      key: label,
      header: label,
      align: 'right' as const,
    })),
  ]

  const data = metricKeys.map((m) => {
    const row: Record<string, string> = { metric: m }
    for (const s of scenarios) {
      const val = s.key_metrics?.[m]
      const delta = s.delta_vs_base?.[m]
      const valStr = val === undefined || val === null ? '-' : formatMetricValue(m, val)
      const deltaStr = delta === undefined || delta === null ? '' : ` (Δ ${formatDeltaValue(delta)})`
      row[s.label] = `${valStr}${deltaStr}`
    }
    return row
  })

  const xAxisTick = { fontSize: 11, fill: 'var(--color-neutral-600)' }
  const yAxisTick = { fontSize: 12, fill: 'var(--color-neutral-600)' }
  const tooltipContentStyle = {
    backgroundColor: 'var(--color-bg-primary)',
    border: '1px solid var(--color-border-light)',
    borderRadius: 'var(--radius-md)',
    fontSize: '12px',
  }

  const tickFormatter =
    chartUnit === 'BRL'
      ? (v: number) => fmtMillions(v)
      : chartUnit === '%'
        ? (v: number) => fmtPct(v)
        : (v: number) => fmtNumber(v)

  const tooltipFormatter =
    chartUnit === 'BRL'
      ? (v: number) => fmtBRL(v)
      : chartUnit === '%'
        ? (v: number) => fmtPct(v)
        : (v: number) => fmtNumber(v)

  return (
    <div>
      <h4 style={{ marginBottom: 'var(--spacing-2)' }}>{artifact.title}</h4>
      {chartMetric && chartData ? (
        <ChartContainer title={`Comparativo: ${chartMetric}`} height={320}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis dataKey="x" tick={xAxisTick} axisLine={{ stroke: 'var(--color-border-light)' }} tickLine={false} />
              <YAxis tickFormatter={tickFormatter} tick={yAxisTick} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value: unknown) => [tooltipFormatter(Number(value)), 'Valor']}
                contentStyle={tooltipContentStyle}
              />
              {scenarios.length > 0 ? <Bar dataKey="value" fill="var(--color-accent)" /> : null}
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      ) : null}

      <div style={{ marginTop: 'var(--spacing-3)' }}>
        <Table columns={columns} data={data} keyField="metric" striped compact />
      </div>
    </div>
  )
}

