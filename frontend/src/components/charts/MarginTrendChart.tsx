import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DRERow } from '../../types'
import { transformMarginTrendDataSplit } from '../../utils/chartHelpers'
import { HISTORICAL_YEAR_END, SERIE_HISTORICAL_COLOR, SERIE_PROJECTED_COLOR } from '../../utils/constants'
import type { DRERowMerged } from '../../utils/dreMerge'
import { ChartContainer } from './ChartContainer'

interface MarginTrendChartProps {
  consolidado: DRERow[] | DRERowMerged[]
}

export function MarginTrendChart({ consolidado }: MarginTrendChartProps) {
  const dataBase = transformMarginTrendDataSplit(consolidado as DRERowMerged[])
  const anoHist = HISTORICAL_YEAR_END
  const anoProj = HISTORICAL_YEAR_END + 1

  // Série auxiliar só para desenhar um “link” entre o último ponto do histórico e o primeiro da projeção.
  const data = dataBase.map((row) => {
    const y = Number(row.ano)
    const linkValue =
      y === anoHist ? row.ebitda_pct_h : y === anoProj ? row.ebitda_pct_p : null
    return { ...row, ebitda_pct_link: linkValue }
  })

  return (
    <ChartContainer title="Margem EBITDA Consolidada (% Receita Liquida)" height={340}>
      <p
        style={{
          fontSize: 11,
          color: 'var(--color-neutral-600)',
          margin: '0 0 8px',
        }}
      >
        <span style={{ color: SERIE_HISTORICAL_COLOR, fontWeight: 600 }}>—</span> Histórico &nbsp;
        <span style={{ color: SERIE_PROJECTED_COLOR, fontWeight: 600 }}>—</span> Projeção
      </p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <ReferenceLine
            x={String(HISTORICAL_YEAR_END)}
            stroke="var(--color-neutral-400)"
            strokeDasharray="4 4"
            label={{ value: 'Projeção →', fill: 'var(--color-neutral-500)', fontSize: 11 }}
          />
          <XAxis
            dataKey="ano"
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => `${v.toFixed(1)}%`}
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={false}
            tickLine={false}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(2)}%`, '']}
            labelFormatter={(label) => `Ano ${label}`}
            contentStyle={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          <Line
            type="monotone"
            dataKey="ebitda_pct_h"
            stroke={SERIE_HISTORICAL_COLOR}
            name="Margem EBITDA % (histórico)"
            strokeWidth={2}
            connectNulls
            dot={{ fill: SERIE_HISTORICAL_COLOR, strokeWidth: 0, r: 4 }}
          >
            <LabelList
              dataKey="ebitda_pct_h"
              position="top"
              formatter={(v) => `${Number(v).toFixed(1)}%`}
            />
          </Line>
          <Line
            type="monotone"
            dataKey="ebitda_pct_p"
            stroke={SERIE_PROJECTED_COLOR}
            name="Margem EBITDA % (projeção)"
            strokeWidth={2}
            connectNulls
            dot={{ fill: SERIE_PROJECTED_COLOR, strokeWidth: 0, r: 4 }}
          >
            <LabelList
              dataKey="ebitda_pct_p"
              position="top"
              formatter={(v) => `${Number(v).toFixed(1)}%`}
            />
          </Line>

          <Line
            type="monotone"
            dataKey="ebitda_pct_link"
            stroke={SERIE_PROJECTED_COLOR}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
