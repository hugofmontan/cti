import type { DRERow } from '../../types'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  LabelList,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { BU_KEYS, BU_NAMES, DRE_DISPLAY_ORDER, DRE_LINE_LABELS, YEARS } from '../../utils/constants'
import { fmtBRL, fmtMillions, fmtPct } from '../../utils/formatters'
import { Tabs } from '../ui/Tabs'
import { Table } from '../ui/Table'
import { ChartContainer } from '../charts/ChartContainer'
import styles from './BUBreakdown.module.css'

interface BUBreakdownProps {
  dre: Record<string, DRERow[]>
}

type TableRow = {
  linha: string
  [year: string]: string | number
}

interface BuOperationalPoint {
  ano: string
  faturamento_bruto: number
  n_funcionarios: number
  ebitda: number
  margem_ebitda_pct: number
}

function getDreValue(row: DRERow, key: string): number | undefined {
  const direct = row[key as keyof DRERow]
  if (typeof direct === 'number') return direct

  // Payload das BUs usa chaves diferentes do consolidado.
  if (key === 'receita_bruta') {
    const v = row.faturamento_bruto
    return typeof v === 'number' ? v : undefined
  }
  if (key === 'deducoes') {
    const v = row.impostos_sv
    return typeof v === 'number' ? v : undefined
  }

  return undefined
}

export function BUBreakdown({ dre }: BUBreakdownProps) {
  const tabs = BU_KEYS.map((buKey) => {
    const rows = dre[buKey] ?? []
    const chartData: BuOperationalPoint[] = rows.map((r) => {
      const faturamentoBruto =
        typeof r.faturamento_bruto === 'number'
          ? r.faturamento_bruto
          : typeof r.receita_bruta === 'number'
            ? r.receita_bruta
            : 0
      const ebitda = typeof r.ebitda === 'number' ? r.ebitda : 0
      const receitaLiquida = typeof r.receita_liquida === 'number' ? r.receita_liquida : 0
      return {
        ano: String(r.ano),
        faturamento_bruto: faturamentoBruto,
        n_funcionarios: typeof r.n_funcionarios === 'number' ? r.n_funcionarios : 0,
        ebitda,
        margem_ebitda_pct: receitaLiquida ? ebitda / receitaLiquida : 0,
      }
    })

    const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
      const row: TableRow = { linha: DRE_LINE_LABELS[key] ?? key }
      for (const yearData of rows) {
        const year = String(yearData.ano)
        const value = getDreValue(yearData, key)
        row[year] = typeof value === 'number' ? fmtBRL(value) : '-'
      }
      return row
    })

    const columns = [
      { key: 'linha', header: 'Linha', align: 'left' as const, width: '220px' },
      ...YEARS.map((year) => ({ key: year, header: year, align: 'right' as const })),
    ]

    return {
      id: buKey,
      label: BU_NAMES[buKey],
      content: (
        <div className={styles.tabContent}>
          <Table columns={columns} data={tableData} striped compact />

          <div className={styles.chartsGrid}>
            <ChartContainer
              title={`Evolucao do Faturamento Bruto e Funcionarios — ${BU_NAMES[buKey]}`}
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <XAxis dataKey="ano" />
                  <YAxis yAxisId="valor" tickFormatter={(v) => fmtMillions(v)} />
                  <YAxis yAxisId="func" orientation="right" />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === 'n_funcionarios') return [Number(value).toFixed(1), 'Funcionarios']
                      return [fmtBRL(Number(value)), 'Faturamento Bruto']
                    }}
                  />
                  <Legend
                    formatter={(value) =>
                      value === 'n_funcionarios' ? 'Funcionarios' : 'Faturamento Bruto'
                    }
                  />
                  <Bar
                    yAxisId="valor"
                    dataKey="faturamento_bruto"
                    fill="var(--color-primary-900)"
                    name="faturamento_bruto"
                  />
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

            <ChartContainer title={`EBITDA e Margem EBITDA — ${BU_NAMES[buKey]}`} height={300}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <XAxis dataKey="ano" />
                  <YAxis yAxisId="valor" tickFormatter={(v) => fmtMillions(v)} />
                  <YAxis yAxisId="pct" orientation="right" tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === 'margem_ebitda_pct') return [fmtPct(Number(value)), 'Margem EBITDA']
                      return [fmtBRL(Number(value)), 'EBITDA']
                    }}
                  />
                  <Legend
                    formatter={(value) => (value === 'margem_ebitda_pct' ? 'Margem EBITDA' : 'EBITDA')}
                  />
                  <Bar
                    yAxisId="valor"
                    dataKey="ebitda"
                    fill="var(--color-primary-900)"
                    name="ebitda"
                  />
                  <Line
                    yAxisId="pct"
                    type="monotone"
                    dataKey="margem_ebitda_pct"
                    stroke="var(--color-negative)"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    name="margem_ebitda_pct"
                  >
                    <LabelList
                      dataKey="margem_ebitda_pct"
                      position="top"
                      formatter={(v) => fmtPct(Number(v), 1)}
                      style={{ fill: 'var(--color-negative)', fontSize: 11, fontWeight: 600 }}
                    />
                  </Line>
                </ComposedChart>
              </ResponsiveContainer>
            </ChartContainer>
          </div>
        </div>
      ),
    }
  })

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Detalhamento por BU</h2>

      <Tabs tabs={tabs} defaultTab="fopm" />
    </section>
  )
}
