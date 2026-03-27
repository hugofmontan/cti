import { useMemo } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  LabelList,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DRERowMerged } from '../../utils/dreMerge'
import { SERIE_HISTORICAL_COLOR, SERIE_PROJECTED_COLOR } from '../../utils/constants'
import { getBuLabel } from '../../utils/buLabels'
import { buildBuOperationalChartData } from '../../utils/buOperationalChartData'
import { fmtBRL, fmtMillions, fmtPct } from '../../utils/formatters'
import { useYearConfig } from '../../contexts/YearConfigContext'
import { ChartContainer } from './ChartContainer'
import styles from './BuOperationalCharts.module.css'

interface BuOperationalChartsProps {
  buKey: string
  rows: DRERowMerged[]
  /** Quando true, exibe título da BU acima dos gráficos (ex.: PDF com várias BUs). */
  showBuHeading?: boolean
}

export function BuOperationalCharts({ buKey, rows, showBuHeading = false }: BuOperationalChartsProps) {
  const { historicalYearEnd, allDisplayYears } = useYearConfig()

  const chartData = useMemo(
    () => buildBuOperationalChartData(rows, allDisplayYears, historicalYearEnd),
    [rows, allDisplayYears, historicalYearEnd],
  )

  const label = getBuLabel(buKey)

  return (
    <div className={styles.buBlock}>
      {showBuHeading ? <h3 className={styles.buHeading}>{label}</h3> : null}
      <div className={styles.chartsGrid}>
        <ChartContainer title={`Evolucao do Faturamento Bruto e Funcionarios — ${label}`} height={320}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <ReferenceLine
                x={String(historicalYearEnd)}
                stroke="var(--color-neutral-400)"
                strokeDasharray="4 4"
              />
              <XAxis dataKey="ano" />
              <YAxis yAxisId="valor" tickFormatter={(v) => fmtMillions(v)} />
              <YAxis yAxisId="func" orientation="right" />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'n_funcionarios')
                    return [Number(value).toFixed(1), 'Funcionarios']
                  return [fmtBRL(Number(value)), 'Faturamento Bruto']
                }}
              />
              <Legend
                formatter={(value) =>
                  value === 'n_funcionarios'
                    ? 'Funcionarios'
                    : value === 'faturamento_bruto_h'
                      ? 'Faturamento Bruto (Hist.)'
                      : value === 'faturamento_bruto_p'
                        ? 'Faturamento Bruto (Proj.)'
                        : '—'
                }
              />
              <Bar yAxisId="valor" dataKey="faturamento_bruto_h" fill={SERIE_HISTORICAL_COLOR} name="faturamento_bruto_h" />
              <Bar yAxisId="valor" dataKey="faturamento_bruto_p" fill={SERIE_PROJECTED_COLOR} name="faturamento_bruto_p" />

              <Line
                yAxisId="func"
                type="monotone"
                dataKey="n_funcionarios"
                stroke="var(--color-warning)"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="n_funcionarios"
              >
                <LabelList
                  dataKey="n_funcionarios"
                  position="top"
                  formatter={(v) => Number(v).toFixed(1)}
                  style={{ fill: 'var(--color-warning)', fontSize: 11, fontWeight: 600 }}
                />
              </Line>
            </ComposedChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer title={`EBITDA e Margem EBITDA — ${label}`} height={320}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <ReferenceLine
                x={String(historicalYearEnd)}
                stroke="var(--color-neutral-400)"
                strokeDasharray="4 4"
              />
              <XAxis dataKey="ano" />
              <YAxis yAxisId="valor" tickFormatter={(v) => fmtMillions(v)} />
              <YAxis
                yAxisId="pct"
                orientation="right"
                tickFormatter={(v) => `${Math.round(v * 100)}%`}
              />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'margem_ebitda_pct_h' || name === 'margem_ebitda_pct_p' || name === 'margem_ebitda_pct')
                    return [fmtPct(Number(value)), 'Margem EBITDA']
                  return [fmtBRL(Number(value)), 'EBITDA']
                }}
              />
              <Legend
                formatter={(value) => {
                  if (
                    value === 'margem_ebitda_pct_h' ||
                    value === 'margem_ebitda_pct_p' ||
                    value === 'margem_ebitda_pct'
                  )
                    return 'Margem EBITDA'
                  if (value === 'ebitda_h') return 'EBITDA (Hist.)'
                  if (value === 'ebitda_p') return 'EBITDA (Proj.)'
                  return 'EBITDA'
                }}
              />
              <Bar yAxisId="valor" dataKey="ebitda_h" fill={SERIE_HISTORICAL_COLOR} name="ebitda_h" />
              <Bar yAxisId="valor" dataKey="ebitda_p" fill={SERIE_PROJECTED_COLOR} name="ebitda_p" />
              <Line
                yAxisId="pct"
                type="monotone"
                dataKey="margem_ebitda_pct"
                stroke="var(--color-warning)"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="margem_ebitda_pct"
              >
                <LabelList
                  dataKey="margem_ebitda_pct"
                  position="top"
                  formatter={(v) => fmtPct(Number(v), 1)}
                  style={{ fill: 'var(--color-warning)', fontSize: 11, fontWeight: 600 }}
                />
              </Line>
            </ComposedChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>
    </div>
  )
}
