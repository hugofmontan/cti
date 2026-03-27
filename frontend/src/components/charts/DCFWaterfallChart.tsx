import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SimulateResponse } from '../../types'
import { fmtBRL, fmtMillions, fmtPct } from '../../utils/formatters'
import { CHART_COLORS } from '../../utils/constants'
import { ChartContainer } from './ChartContainer'
import styles from './DCFWaterfallChart.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

interface DCFWaterfallChartProps {
  dcf: SimulateResponse['dcf']
}

interface WaterfallPoint {
  name: string
  offset: number
  delta: number
  total: number
  kind: 'vp' | 'terminal' | 'total'
}

export function DCFWaterfallChart({ dcf }: DCFWaterfallChartProps) {
  const { projectedYears } = useYearConfig()

  const vpFluxos = dcf.soma_vp_fcffs
  const vpTerminal = dcf.enterprise_value - dcf.soma_vp_fcffs
  const ev = dcf.enterprise_value
  const pctFluxos = ev ? vpFluxos / ev : 0
  const pctTerminal = ev ? vpTerminal / ev : 0

  const data: WaterfallPoint[] = []
  let acumulado = 0

  // VP FCFFs (degraus positivos)
  for (const year of projectedYears) {
    const yearKey = String(year)
    const vpFcff = dcf.vp_fcff_por_ano[yearKey] || 0
    data.push({
      name: `VP ${year}`,
      offset: acumulado,
      delta: vpFcff,
      total: 0,
      kind: 'vp',
    })
    acumulado += vpFcff
  }

  // VP Terminal (último degrau antes do total)
  data.push({ name: 'VP Terminal', offset: acumulado, delta: vpTerminal, total: 0, kind: 'terminal' })
  acumulado += vpTerminal

  // Barra final do total (EV)
  data.push({
    name: 'EV Total',
    offset: 0,
    delta: 0,
    total: ev,
    kind: 'total',
  })

  return (
    <ChartContainer title="Composicao do Enterprise Value (DCF)" height={470}>
      <div className={styles.metaRow}>
        <div className={styles.metaCard}>
          <span className={styles.metaLabel}>% VP Fluxos Explicitos</span>
          <strong className={styles.metaValue}>{fmtPct(pctFluxos)}</strong>
        </div>
        <div className={styles.metaCard}>
          <span className={styles.metaLabel}>% VP Valor Terminal</span>
          <strong className={styles.metaValue}>{fmtPct(pctTerminal)}</strong>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="95%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: 'var(--color-neutral-600)' }}
            axisLine={{ stroke: 'var(--color-border-light)' }}
            tickLine={false}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tickFormatter={(v) => fmtMillions(v)}
            tick={{ fontSize: 12, fill: 'var(--color-neutral-600)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value, name, payload) => {
              const p = payload?.payload as WaterfallPoint
              const n = Number(value)
              if (name === 'total') return [fmtBRL(n), 'Enterprise Value']
              if (p?.kind === 'terminal') return [`${fmtBRL(n)} (${fmtPct(pctTerminal)})`, 'VP Terminal']
              return [`${fmtBRL(n)} (${fmtPct(ev ? n / ev : 0)})`, 'VP Fluxo']
            }}
            contentStyle={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
            }}
          />
          {/* Base invisível para criar degraus do waterfall */}
          <Bar dataKey="offset" stackId="wf" fill="transparent" />
          {/* Variação por componente */}
          <Bar dataKey="delta" stackId="wf" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`delta-${index}`}
                fill={entry.kind === 'terminal' ? CHART_COLORS.secondary : CHART_COLORS.primary}
              />
            ))}
          </Bar>
          {/* Barra final do total */}
          <Bar dataKey="total" fill={CHART_COLORS.tertiary} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
