import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DRERow } from '../../types'
import { transformMarginTrendData } from '../../utils/chartHelpers'
import { CHART_COLORS } from '../../utils/constants'
import { ChartContainer } from './ChartContainer'

interface MarginTrendChartProps {
  consolidado: DRERow[]
}

export function MarginTrendChart({ consolidado }: MarginTrendChartProps) {
  const data = transformMarginTrendData(consolidado)

  return (
    <ChartContainer title="Margem EBITDA Consolidada (% Receita Liquida)" height={300}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis
            dataKey="ano"
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => `${v.toFixed(0)}%`}
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={false}
            tickLine={false}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(2)}%`]}
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
            dataKey="ebitda_pct"
            stroke={CHART_COLORS.primary}
            name="Margem EBITDA %"
            strokeWidth={2}
            dot={{ fill: CHART_COLORS.primary, strokeWidth: 0, r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
