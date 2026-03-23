import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FluxoRow } from '../../types'
import { fmtBRL, fmtMillions } from '../../utils/formatters'
import { transformFCFFData } from '../../utils/chartHelpers'
import { CHART_COLORS } from '../../utils/constants'
import { ChartContainer } from './ChartContainer'

interface FCFFBarChartProps {
  fluxo: FluxoRow[]
}

export function FCFFBarChart({ fluxo }: FCFFBarChartProps) {
  const data = transformFCFFData(fluxo)

  return (
    <ChartContainer title="FCFF por Ano">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis
            dataKey="ano"
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => fmtMillions(v)}
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value) => [fmtBRL(Number(value)), 'FCFF']}
            labelFormatter={(label) => `Ano ${label}`}
            contentStyle={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
            }}
          />
          <Bar
            dataKey="fcff"
            fill={CHART_COLORS.primary}
            name="FCFF"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
