import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DRERow } from '../../types'
import { fmtBRL, fmtMillions } from '../../utils/formatters'
import { transformRevenueByBUData } from '../../utils/chartHelpers'
import { BU_NAMES, CHART_COLORS } from '../../utils/constants'
import { ChartContainer } from './ChartContainer'

interface RevenueByBUChartProps {
  dre: Record<string, DRERow[]>
}

export function RevenueByBUChart({ dre }: RevenueByBUChartProps) {
  const data = transformRevenueByBUData(dre)

  return (
    <ChartContainer title="Receita Liquida por BU (Empilhado)" height={350}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
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
            formatter={(value, name) => [
              fmtBRL(Number(value)),
              BU_NAMES[name as keyof typeof BU_NAMES] || name,
            ]}
            labelFormatter={(label) => `Ano ${label}`}
            contentStyle={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
            }}
          />
          <Legend
            formatter={(value) => BU_NAMES[value as keyof typeof BU_NAMES] || value}
            wrapperStyle={{ fontSize: '12px' }}
          />
          <Area type="monotone" dataKey="fopm" stackId="1" fill={CHART_COLORS.fopm} stroke={CHART_COLORS.fopm} name="fopm" />
          <Area type="monotone" dataKey="renovacao" stackId="1" fill={CHART_COLORS.renovacao} stroke={CHART_COLORS.renovacao} name="renovacao" />
          <Area type="monotone" dataKey="ams" stackId="1" fill={CHART_COLORS.ams} stroke={CHART_COLORS.ams} name="ams" />
          <Area type="monotone" dataKey="venda_sw" stackId="1" fill={CHART_COLORS.venda_sw} stroke={CHART_COLORS.venda_sw} name="venda_sw" />
          <Area
            type="monotone"
            dataKey="data_science"
            stackId="1"
            fill={CHART_COLORS.data_science}
            stroke={CHART_COLORS.data_science}
            name="data_science"
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
