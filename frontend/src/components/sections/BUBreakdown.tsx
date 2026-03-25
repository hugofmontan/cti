import {
  ALL_DISPLAY_YEARS,
  BU_KEYS,
  BU_NAMES,
  DRE_DISPLAY_ORDER,
  DRE_LINE_LABELS,
  SERIE_HISTORICAL_COLOR,
  SERIE_PROJECTED_COLOR,
  HISTORICAL_YEAR_END,
} from '../../utils/constants'
import type { DRERowMerged } from '../../utils/dreMerge'
import { fmtBRL, fmtMillions, fmtPct } from '../../utils/formatters'
import { Tabs } from '../ui/Tabs'
import { Table } from '../ui/Table'
import tableStyles from '../ui/Table.module.css'
import { ChartContainer } from '../charts/ChartContainer'
import styles from './BUBreakdown.module.css'
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

interface BUBreakdownProps {
  /** Série mesclada histórico + projeção por BU. */
  dre: Record<string, DRERowMerged[]>
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
  margem_ebitda_pct_h: number | null
  margem_ebitda_pct_p: number | null
  faturamento_bruto_h: number | null
  faturamento_bruto_p: number | null
  n_funcionarios_h: number | null
  n_funcionarios_p: number | null
  ebitda_h: number | null
  ebitda_p: number | null
  /** Para estilizar barras (opcional futuro) */
  isHistorical: boolean
}

function getDreValue(row: DRERowMerged, key: string): number | undefined {
  const direct = row[key as keyof DRERowMerged]
  if (typeof direct === 'number') return direct

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
  const knownBuKeys = BU_KEYS as unknown as string[]
  const extraBuKeys = Object.keys(dre).filter((k) => !knownBuKeys.includes(k))
  const tabsBuKeys = [...knownBuKeys, ...extraBuKeys]

  const getBuLabel = (buKey: string) => {
    const lower = buKey.toLowerCase()
    if (lower === 'administrativa' || lower.includes('administr')) return 'Administrativa'

    const known = (BU_NAMES as Record<string, string>)[lower] ?? (BU_NAMES as Record<string, string>)[buKey]
    return known ?? buKey
  }

  const tabs = tabsBuKeys.map((buKey) => {
    const rows = dre[buKey] ?? []

    const chartData: BuOperationalPoint[] = ALL_DISPLAY_YEARS.map((ys) => {
      const y = Number(ys)
      const r = rows.find((row) => row.ano === y)
      const faturamentoBruto =
        typeof r?.faturamento_bruto === 'number'
          ? r.faturamento_bruto
          : typeof r?.receita_bruta === 'number'
            ? r.receita_bruta
            : 0
      const ebitda = typeof r?.ebitda === 'number' ? r.ebitda : 0
      const receitaLiquida = typeof r?.receita_liquida === 'number' ? r.receita_liquida : 0
      const margem = receitaLiquida ? ebitda / receitaLiquida : 0
      const isHistorical = y <= HISTORICAL_YEAR_END
      const faturamentoBrutoH = isHistorical ? faturamentoBruto : null
      const faturamentoBrutoP = !isHistorical ? faturamentoBruto : null

      // Algumas BUs podem expor headcount com nomes diferentes (ex.: BU administrativa -> `n_funcionarios_adm`).
      const nFuncionariosBase =
        typeof r?.n_funcionarios === 'number'
          ? r.n_funcionarios
          : typeof (r as { n_funcionarios_adm?: unknown }).n_funcionarios_adm === 'number'
            ? (r as { n_funcionarios_adm: number }).n_funcionarios_adm
            : 0

      const nFuncionariosH = isHistorical ? nFuncionariosBase : null
      const nFuncionariosP = !isHistorical ? nFuncionariosBase : null
      const ebitdaH = isHistorical ? ebitda : null
      const ebitdaP = !isHistorical ? ebitda : null
      return {
        ano: ys,
        faturamento_bruto: faturamentoBruto,
        n_funcionarios: nFuncionariosBase,
        ebitda,
        margem_ebitda_pct: margem,
        margem_ebitda_pct_h: isHistorical ? margem : null,
        margem_ebitda_pct_p: !isHistorical ? margem : null,
        faturamento_bruto_h: faturamentoBrutoH,
        faturamento_bruto_p: faturamentoBrutoP,
        n_funcionarios_h: nFuncionariosH,
        n_funcionarios_p: nFuncionariosP,
        ebitda_h: ebitdaH,
        ebitda_p: ebitdaP,
        isHistorical,
      }
    })

    const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
      const row: TableRow = { linha: DRE_LINE_LABELS[key] ?? key }
      for (const yearData of rows) {
        const year = String(yearData.ano)
        const value = getDreValue(yearData, key)
        row[year] = typeof value === 'number' ? fmtBRL(value) : '—'
      }
      return row
    })

    const columns = [
      { key: 'linha', header: 'Linha', align: 'left' as const, width: '220px' },
      ...ALL_DISPLAY_YEARS.map((year) => {
        const y = Number(year)
        const isHist = y <= HISTORICAL_YEAR_END
        return {
          key: year,
          header: year,
          align: 'right' as const,
          headerClassName: isHist ? tableStyles.colHistoricalHeader : tableStyles.colProjectedHeader,
          cellClassName: isHist ? tableStyles.colHistorical : tableStyles.colProjected,
        }
      }),
    ]

    return {
      id: buKey,
      label: getBuLabel(buKey),
      content: (
        <div className={styles.tabContent}>
          <p className={styles.tableLegend}>
            <span className={styles.swatchHist} /> Histórico
            <span className={styles.swatchGap} />
            <span className={styles.swatchProj} /> Projeção
          </p>
          <Table columns={columns} data={tableData} striped compact />

          <div className={styles.chartsGrid}>
            <ChartContainer
              title={`Evolucao do Faturamento Bruto e Funcionarios — ${getBuLabel(buKey)}`}
              height={320}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <ReferenceLine
                    x={String(HISTORICAL_YEAR_END)}
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

            <ChartContainer title={`EBITDA e Margem EBITDA — ${getBuLabel(buKey)}`} height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <ReferenceLine
                    x={String(HISTORICAL_YEAR_END)}
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
