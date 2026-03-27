import { Bar, BarChart, Cell, CartesianGrid, LabelList, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts'
import type {
  AgentArtifact,
  AgentChartArtifact,
  AgentTableArtifact,
  AgentKPIPanelArtifact,
  AgentScenarioComparisonArtifact,
  AgentSensitivityMatrixArtifact,
  AgentSankeyArtifact,
} from '../../types'
import { CHART_COLORS } from '../../utils/constants'
import { fmtBRL, fmtMillions, fmtPct, fmtNumber } from '../../utils/formatters'
import { Table } from '../ui'
import { ChartContainer } from '../charts'
import styles from './AgentArtifactRenderer.module.css'
import { KPIPanelCard } from './KPIPanelCard'
import { ScenarioComparisonPanel } from './ScenarioComparisonPanel'
import { SensitivityHeatmap } from './SensitivityHeatmap'
import { SankeyChart } from './SankeyChart'

interface AgentArtifactRendererProps {
  artifacts: AgentArtifact[]
}

function renderTable(artifact: AgentTableArtifact) {
  const titleLower = artifact.title.toLowerCase()
  const prettifySeriesLabel = (rawLabel: string) => {
    const raw = String(rawLabel ?? '').trim()
    if (!raw) return raw

    const [buPartRaw, metricPartRaw] = raw.includes(' - ')
      ? raw.split(/\s-\s(.+)/, 2)
      : [raw, '']
    const buPart = buPartRaw || ''
    const metricPart = metricPartRaw || ''
    const metricMap: Record<string, string> = {
      faturamento_bruto: 'Faturamento Bruto',
      receita_liquida: 'Receita Liquida',
      ebitda: 'EBITDA',
      lucro_liquido: 'Lucro Liquido',
      headcount: 'Headcount',
      n_funcionarios: 'Headcount',
    }

    const suffixMap: Array<[string, string]> = [
      ['_yoy_pct', ' (YoY %)'],
      ['_delta_pct', ' (Delta %)'],
      ['_cagr', ' (CAGR)'],
    ]

    const metricBase = metricPart || buPart
    let base = metricBase
    let suffixLabel = ''
    for (const [suffix, label] of suffixMap) {
      if (base.endsWith(suffix)) {
        base = base.slice(0, -suffix.length)
        suffixLabel = label
        break
      }
    }

    const baseLabel = metricMap[base] ?? base.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    if (!metricPart) return baseLabel
    return `${buPart} - ${baseLabel}${suffixLabel}`
  }

  const formatNumericCell = (v: number, rowLabel: string) => {
    const rowLower = String(rowLabel || '').toLowerCase()
    const isDerivedPctRow =
      rowLower.includes('yoy_pct') ||
      rowLower.includes('delta_pct') ||
      rowLower.includes('_cagr') ||
      rowLower.includes('variacao') ||
      rowLower.includes('variação')

    // Se a linha representa métrica derivada percentual, sempre exibir em %.
    if (isDerivedPctRow) return fmtPct(v)

    // Heurística global para tabelas percentuais.
    const titleHintsPct = ['margem', 'pct', '%', 'yoy', 'cagr', 'variação anual', 'variacao anual', 'crescimento anual']
    if (titleHintsPct.some((h) => titleLower.includes(h))) {
      return fmtPct(v)
    }

    // Métricas financeiras (valores absolutos em BRL): mostramos com separador de milhar e 0 casas.
    if (
      titleLower.includes('ebitda') ||
      titleLower.includes('receita') ||
      titleLower.includes('faturamento') ||
      titleLower.includes('lucro')
    ) {
      return fmtNumber(v, 0)
    }

    return fmtNumber(v)
  }

  const columns = artifact.columns.map((column, index) => ({
    key: `col-${index}`,
    header: column,
    align: index === 0 ? 'left' as const : 'right' as const,
    render:
      index === 0
        ? (row: Record<string, unknown>) => prettifySeriesLabel(String(row['col-0'] ?? ''))
        : (row: Record<string, unknown>, _index: number) => {
            const raw = row[`col-${index}`]
            if (raw === null || raw === undefined) return '-'
            const n = typeof raw === 'number' ? raw : Number(raw)
            if (!Number.isFinite(n)) return '-'
            return formatNumericCell(n, String(row['col-0'] ?? ''))
          },
  }))
  const data = artifact.rows.map((row, rowIdx) =>
    row.reduce<Record<string, string | number | null>>((acc, value, colIdx) => {
      acc[`col-${colIdx}`] = value
      acc._id = rowIdx
      return acc
    }, {}),
  )

  return (
    <div className={styles.block}>
      <h4>{artifact.title}</h4>
      <Table columns={columns} data={data} keyField="_id" />
    </div>
  )
}

function getTickFormatter(unit: string | null | undefined) {
  // unit vem do backend e pode ser null/undefined.
  if (!unit) return (v: number) => fmtNumber(v)
  if (unit === 'BRL') return (v: number) => fmtMillions(v)
  if (unit === '%' || unit.toLowerCase() === 'pct')
    return (v: number) => {
      // Resiliencia de escala:
      // - alguns backends enviam margem como razao (0.33 -> 33%)
      // - outros enviam diretamente como percentual (33.0 -> 33%)
      const abs = Math.abs(v)
      const pct = abs > 1.0 ? v : v * 100
      return `${pct.toFixed(2)}%`
    }
  return (v: number) => fmtNumber(v)
}

function getTooltipFormatter(unit: string | null | undefined) {
  if (!unit) return (v: number) => fmtNumber(v)
  if (unit === 'BRL') return (v: number) => fmtBRL(v)
  if (unit === '%' || unit.toLowerCase() === 'pct')
    return (v: number) => {
      const abs = Math.abs(v)
      const pct = abs > 1.0 ? v : v * 100
      return `${pct.toFixed(2)}%`
    }
  return (v: number) => fmtNumber(v)
}

function renderChart(artifact: AgentChartArtifact) {
  const safeX = Array.isArray(artifact.x) ? artifact.x : []
  const safeSeries = Array.isArray(artifact.series)
    ? artifact.series.filter((s) => s && typeof s.name === 'string' && Array.isArray(s.values))
    : []

  const data = safeX.map((xVal, idx) => {
    const row: Record<string, string | number> = { x: xVal }
    safeSeries.forEach((series) => {
      row[series.name] = series.values[idx] ?? 0
    })
    return row
  })
  const colors = [
    CHART_COLORS.primary,
    CHART_COLORS.secondary,
    CHART_COLORS.tertiary,
    CHART_COLORS.quaternary,
    CHART_COLORS.data_science,
    CHART_COLORS.quinary,
  ]
  const gridProps = { strokeDasharray: '3 3', stroke: 'var(--color-border-light)' }
  const xAxisTick = { fontSize: 11, fill: 'var(--color-neutral-600)' }
  const yAxisTick = { fontSize: 12, fill: 'var(--color-neutral-600)' }
  const tooltipContentStyle = {
    backgroundColor: 'var(--color-bg-primary)',
    border: '1px solid var(--color-border-light)',
    borderRadius: 'var(--radius-md)',
    fontSize: '12px',
  }
  const numCategories = safeX.length
  const rotateXAxis = numCategories > 6 && artifact.chart_type !== 'horizontal_bar'

  const chartHeight = (() => {
    switch (artifact.chart_type) {
      case 'waterfall':
        return 440
      case 'horizontal_bar':
        return Math.max(320, numCategories * 40)
      default:
        return rotateXAxis ? 380 : 340
    }
  })()
  const chartWidth = Math.max(640, numCategories * 90)
  const chartMargin = {
    top: 24,
    right: 24,
    left: 24,
    bottom: rotateXAxis ? 56 : 24,
  }
  const inferredUnit = (() => {
    const explicit = artifact.unit?.trim()
    if (explicit) return explicit
    const title = artifact.title.toLowerCase()
    if (title.includes('margem') || title.includes('pct') || title.includes('%')) return '%'
    const flatValues = safeSeries.flatMap((s) => s.values).filter((v) => Number.isFinite(v))
    if (flatValues.length > 0) {
      const maxAbs = Math.max(...flatValues.map((v) => Math.abs(v)))
      // Heurística: séries em razão (0-1) muito provavelmente representam percentual.
      if (maxAbs <= 1.5) return '%'
    }
    return ''
  })()

  const chartElement = (() => {
    if (artifact.chart_type === 'line') {
      return (
        <LineChart data={data} width={chartWidth} height={chartHeight} margin={chartMargin}>
          <CartesianGrid {...gridProps} />
          <XAxis
            dataKey="x"
            tick={xAxisTick}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
            interval={rotateXAxis ? 0 : undefined}
            angle={rotateXAxis ? -25 : undefined}
            textAnchor={rotateXAxis ? 'end' : undefined}
            height={rotateXAxis ? 60 : undefined}
          />
          <YAxis
            tickFormatter={getTickFormatter(inferredUnit)}
            tick={yAxisTick}
            axisLine={false}
            tickLine={false}
            domain={['dataMin', 'dataMax']}
            width={90}
          />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [getTooltipFormatter(inferredUnit)(Number(value)), String(name)]}
            contentStyle={tooltipContentStyle}
          />
          <Legend />
          {safeSeries.map((series, idx) => (
            <Line
              key={series.name}
              type="monotone"
              dataKey={series.name}
              stroke={colors[idx % colors.length]}
              strokeWidth={2}
            >
              <LabelList
                dataKey={series.name}
                position="top"
                formatter={(v: unknown) => {
                  const n = Number(v)
                  if (!Number.isFinite(n)) return ''
                  if (inferredUnit === '%' || inferredUnit.toLowerCase() === 'pct') {
                    const abs = Math.abs(n)
                    const pct = abs > 1.0 ? n : n * 100
                    return `${pct.toFixed(2)}%`
                  }
                  return inferredUnit === 'BRL' ? fmtMillions(n, 1) : fmtNumber(n)
                }}
                style={{ fontSize: 11, fill: 'var(--color-neutral-700)' }}
              />
            </Line>
          ))}
        </LineChart>
      )
    }

    if (artifact.chart_type === 'horizontal_bar') {
      return (
        <BarChart
          data={safeX.map((xVal, idx) => ({
            x: xVal,
            value: safeSeries[0]?.values[idx] ?? 0,
          }))}
          width={chartWidth}
          height={chartHeight}
          layout="vertical"
          margin={chartMargin}
        >
          <CartesianGrid {...gridProps} />
          <XAxis
            type="number"
            tickFormatter={getTickFormatter(inferredUnit)}
            tick={xAxisTick}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
          />
          <YAxis dataKey="x" type="category" width={150} tick={yAxisTick} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [getTooltipFormatter(inferredUnit)(Number(value)), String(name)]}
            contentStyle={tooltipContentStyle}
          />
          <Bar dataKey="value" fill={colors[0]} />
        </BarChart>
      )
    }

    if (artifact.chart_type === 'waterfall') {
      const primary = safeSeries[0]
      const waterfallData: Array<{ name: string | number; offset: number; delta: number; total: number }> = []
      let acumulado = 0
      for (let idx = 0; idx < safeX.length; idx++) {
        const delta = primary?.values[idx] ?? 0
        waterfallData.push({ name: safeX[idx], offset: acumulado, delta, total: 0 })
        acumulado += delta
      }
      waterfallData.push({ name: 'Total', offset: 0, delta: 0, total: acumulado })

      const tickFmt = getTickFormatter(inferredUnit)
      const tooltipFmt = getTooltipFormatter(inferredUnit)
      return (
        <BarChart data={waterfallData} width={chartWidth} height={chartHeight} margin={chartMargin}>
          <CartesianGrid {...gridProps} />
          <XAxis
            dataKey="name"
            tick={xAxisTick}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
            interval={rotateXAxis ? 0 : undefined}
            angle={rotateXAxis ? -25 : undefined}
            textAnchor={rotateXAxis ? 'end' : undefined}
            height={rotateXAxis ? 60 : undefined}
          />
          <YAxis tickFormatter={tickFmt} tick={yAxisTick} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [tooltipFmt(Number(value)), String(name)]}
            contentStyle={tooltipContentStyle}
          />
          <Legend />
          <Bar dataKey="offset" stackId="wf" fill="transparent" />
          <Bar dataKey="delta" stackId="wf" radius={[4, 4, 0, 0]}>
            {waterfallData.map((entry, index) => (
              <Cell key={`cell-delta-${index}`} fill={entry.delta >= 0 ? colors[0] : colors[1]} />
            ))}
          </Bar>
          <Bar dataKey="total" fill={colors[2]} radius={[4, 4, 0, 0]} />
        </BarChart>
      )
    }

    if (artifact.chart_type === 'bar' || artifact.chart_type === 'grouped_bar' || artifact.chart_type === 'stacked_bar') {
      return (
        <BarChart data={data} width={chartWidth} height={chartHeight} margin={chartMargin}>
          <CartesianGrid {...gridProps} />
          <XAxis
            dataKey="x"
            tick={xAxisTick}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
            interval={rotateXAxis ? 0 : undefined}
            angle={rotateXAxis ? -25 : undefined}
            textAnchor={rotateXAxis ? 'end' : undefined}
            height={rotateXAxis ? 60 : undefined}
          />
          <YAxis
            tickFormatter={getTickFormatter(inferredUnit)}
            tick={yAxisTick}
            axisLine={false}
            tickLine={false}
            width={90}
          />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [getTooltipFormatter(inferredUnit)(Number(value)), String(name)]}
            contentStyle={tooltipContentStyle}
          />
          <Legend />
          {safeSeries.map((series, idx) => (
            <Bar
              key={series.name}
              dataKey={series.name}
              fill={colors[idx % colors.length]}
              stackId={artifact.chart_type === 'stacked_bar' ? 'stack' : undefined}
            />
          ))}
        </BarChart>
      )
    }

    return (
      <BarChart data={data} width={chartWidth} height={chartHeight} margin={chartMargin}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="x" tick={xAxisTick} />
        <YAxis tick={yAxisTick} />
        {safeSeries.map((series, idx) => (
          <Bar key={series.name} dataKey={series.name} fill={colors[idx % colors.length]} />
        ))}
      </BarChart>
    )
  })()

  return (
    <ChartContainer title={artifact.title} height={chartHeight}>
      <div style={{ width: '100%', overflowX: 'auto', overflowY: 'hidden' }}>
        {chartElement}
      </div>
    </ChartContainer>
  )
}

export function AgentArtifactRenderer({ artifacts }: AgentArtifactRendererProps) {
  if (!artifacts.length) return null
  return (
    <div className={styles.container}>
      {artifacts.map((artifact, idx) => {
        if (artifact.type === 'table') return <div key={idx}>{renderTable(artifact)}</div>
        if (artifact.type === 'chart') return <div key={idx}>{renderChart(artifact)}</div>
        if (artifact.type === 'kpi_panel') return <KPIPanelCard key={idx} artifact={artifact as AgentKPIPanelArtifact} />
        if (artifact.type === 'scenario_comparison')
          return <ScenarioComparisonPanel key={idx} artifact={artifact as AgentScenarioComparisonArtifact} />
        if (artifact.type === 'sensitivity_matrix')
          return <SensitivityHeatmap key={idx} artifact={artifact as AgentSensitivityMatrixArtifact} />
        if (artifact.type === 'sankey')
          return <SankeyChart key={idx} artifact={artifact as AgentSankeyArtifact} />

        // KPI simples ("kpi")
        return (
          <div key={idx} className={styles.kpi}>
            <strong>{artifact.title}</strong>
            <span>{(artifact as any).value}</span>
            {(artifact as any).subtitle ? <small>{(artifact as any).subtitle}</small> : null}
          </div>
        )
      })}
    </div>
  )
}
