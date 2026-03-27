import type { AgentSensitivityMatrixArtifact } from '../../types'
import { Table } from '../ui'
import { fmtMillions, fmtNumber } from '../../utils/formatters'

interface SensitivityHeatmapProps {
  artifact: AgentSensitivityMatrixArtifact
}

function colorForRatio(ratio: number) {
  // 0 -> verde, 0.5 -> amarelo, 1 -> vermelho
  const t = Math.max(0, Math.min(1, ratio))
  const hue = t <= 0.5 ? 120 - (t / 0.5) * 60 : 60 - ((t - 0.5) / 0.5) * 60
  return `hsl(${hue}, 85%, 88%)`
}

function formatSensitivityParamValue(param: string, v: number) {
  const p = (param || '').toLowerCase()
  const abs = Math.abs(v)
  if (p.includes('headcount') || p.includes('n_funcionarios')) {
    // Headcount é uma contagem (unidade inteira), não percentual.
    return fmtNumber(Math.round(v), 0)
  }

  // Resiliência de escala para percentuais:
  // - se vier como razão (0.02), mostramos 2.00%
  // - se vier como percentual (2.0 ou 5.0), mostramos 2.00% ou 5.00%
  const pct = abs <= 1.0 ? v * 100 : v
  const isGrowthParam = p === 'g' || p.endsWith('.g')
  if (p.includes('ociosidade') || p.includes('churn') || p.includes('spread') || p.includes('wacc') || isGrowthParam) {
    return `${pct.toFixed(2)}%`
  }

  return fmtNumber(v, 2)
}

function prettyParamLabel(param: string) {
  const p = (param || '').toLowerCase()
  if (p.includes('wacc')) return 'WACC'
  if (p === 'g' || p.includes('g')) return 'G'
  // Fallback: mantendo upper-case para ficar consistente
  return (param || '').toUpperCase()
}

function formatCell(v: unknown) {
  if (typeof v === 'number' && Number.isFinite(v)) return fmtMillions(v, 1)
  return '-'
}

function isHeadcountParam(param: string) {
  const p = (param || '').toLowerCase()
  return p.includes('headcount') || p.includes('n_funcionarios')
}

function formatHeadcountAxisLegend(values: number[], baseValue: number) {
  if (!Number.isFinite(baseValue) || baseValue === 0) return null
  const maxItems = 8
  const trimmed =
    values.length > maxItems ? [...values.slice(0, Math.floor(maxItems / 2)), ...values.slice(-Math.ceil(maxItems / 2))] : values

  const parts = trimmed.map((v) => {
    const vInt = Math.round(v)
    const deltaPct = ((vInt - baseValue) / baseValue) * 100
    const sign = deltaPct >= 0 ? '+' : ''
    return `${vInt} (${sign}${deltaPct.toFixed(2)}%)`
  })

  const ellipsis = values.length > maxItems ? ' … ' : ''
  return `${parts.join(', ')}${ellipsis}`
}

export function SensitivityHeatmap({ artifact }: SensitivityHeatmapProps) {
  const { row_values: rowValues, col_values: colValues, matrix } = artifact
  const flat = matrix.flat().filter((v) => typeof v === 'number' && Number.isFinite(v))
  const min = flat.length ? Math.min(...flat) : 0
  const max = flat.length ? Math.max(...flat) : 1
  const denom = max - min || 1

  const columns = [
    {
      key: 'row',
      header: prettyParamLabel(artifact.row_param),
      align: 'left' as const,
      render: (row: Record<string, any>) => {
        const v = row?.row
        return typeof v === 'number' && Number.isFinite(v) ? formatSensitivityParamValue(artifact.row_param, v) : '-'
      },
    },
    ...colValues.map((v, colIdx) => ({
      key: `col-${colIdx}`,
      header: `${prettyParamLabel(artifact.col_param)}=${formatSensitivityParamValue(artifact.col_param, v)}`,
      align: 'right' as const,
      render: (row: Record<string, any>) => {
        const value = row[`col-${colIdx}`] as number | undefined
          // Queremos vermelho para valores menores.
          // ratio=1 (vermelho) => value=min; ratio=0 (verde) => value=max
          const ratio = typeof value === 'number' ? (max - value) / denom : 0
        return (
          <div
            style={{
              padding: '4px 6px',
              borderRadius: 6,
              background: colorForRatio(ratio),
              width: '100%',
            }}
          >
            {formatCell(value)}
          </div>
        )
      },
    })),
  ]

  const data = rowValues.map((rv, rowIdx) => {
    const row: Record<string, any> = { row: rv }
    for (let j = 0; j < colValues.length; j++) {
      row[`col-${j}`] = matrix[rowIdx]?.[j] ?? null
    }
    return row
  })

  return (
    <div>
      <h4 style={{ marginBottom: 'var(--spacing-2)' }}>{artifact.title}</h4>
      <Table columns={columns} data={data} keyField="row" striped compact />
      {(artifact.row_axis_meta?.base_value ?? null) !== null || (artifact.col_axis_meta?.base_value ?? null) !== null ? (
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
          {isHeadcountParam(artifact.row_param) && typeof artifact.row_axis_meta?.base_value === 'number' ? (
            <div>
              Base headcount ({artifact.row_axis_meta?.base_year ?? 'base'}): {Math.round(artifact.row_axis_meta.base_value)}.{' '}
              Eixo escala proporcional do caso base: {formatHeadcountAxisLegend(rowValues, artifact.row_axis_meta.base_value) ?? ''}
            </div>
          ) : null}
          {isHeadcountParam(artifact.col_param) && typeof artifact.col_axis_meta?.base_value === 'number' ? (
            <div style={{ marginTop: 6 }}>
              Base headcount ({artifact.col_axis_meta?.base_year ?? 'base'}): {Math.round(artifact.col_axis_meta.base_value)}.{' '}
              Eixo escala proporcional do caso base: {formatHeadcountAxisLegend(colValues, artifact.col_axis_meta.base_value) ?? ''}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

