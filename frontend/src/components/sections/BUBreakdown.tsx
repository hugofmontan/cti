import { BU_KEYS, DRE_DISPLAY_ORDER, DRE_LINE_LABELS } from '../../utils/constants'
import type { DRERowMerged } from '../../utils/dreMerge'
import { getBuLabel } from '../../utils/buLabels'
import { fmtBRLThousandsAccounting } from '../../utils/formatters'
import { Tabs } from '../ui/Tabs'
import { Table } from '../ui/Table'
import tableStyles from '../ui/Table.module.css'
import { BuOperationalCharts } from '../charts/BuOperationalCharts'
import styles from './BUBreakdown.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

interface BUBreakdownProps {
  /** Série mesclada histórico + projeção por BU. */
  dre: Record<string, DRERowMerged[]>
}

type TableRow = {
  key: string
  linha: string
  [year: string]: string | number | null
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
  const { historicalYearEnd, allDisplayYears } = useYearConfig()

  const knownBuKeys = BU_KEYS as unknown as string[]
  const extraBuKeys = Object.keys(dre).filter((k) => !knownBuKeys.includes(k))
  const tabsBuKeys = [...knownBuKeys, ...extraBuKeys]
  const highlightRows = ['receita_liquida', 'mc1', 'mc2', 'ebitda', 'ebit', 'lucro_liquido']

  const tabs = tabsBuKeys.map((buKey) => {
    const rows = dre[buKey] ?? []

    const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
      const row: TableRow = { key, linha: DRE_LINE_LABELS[key] ?? key }
      for (const yearData of rows) {
        const year = String(yearData.ano)
        const value = getDreValue(yearData, key)
        row[year] = typeof value === 'number' ? value : null
      }
      return row
    })

    const columns = [
      {
        key: 'linha',
        header: 'Linha',
        align: 'left' as const,
        width: '220px',
        render: (row: TableRow) => <span className={styles.rowLabel}>{row.linha}</span>,
      },
      ...allDisplayYears.map((y) => {
        const isHist = y <= historicalYearEnd
        return {
          key: String(y),
          header: String(y),
          align: 'right' as const,
          headerClassName: isHist ? tableStyles.colHistoricalHeader : tableStyles.colProjectedHeader,
          cellClassName: isHist ? tableStyles.colHistorical : tableStyles.colProjected,
          render: (row: TableRow) => {
            const raw = row[String(y)]
            const value = typeof raw === 'number' ? raw : null
            if (value === null) return '—'
            const className = value < 0 ? styles.negativeValue : styles.numericValue
            return (
              <span className={className}>
                {fmtBRLThousandsAccounting(value, { zeroAsDash: true, decimals: 0 })}
              </span>
            )
          },
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
            <span className={styles.swatchGap} />
            <strong>R$ mil</strong>
          </p>
          <Table
            columns={columns}
            data={tableData}
            className={styles.dreTable}
            striped
            compact
            highlightRows={(row) => highlightRows.includes(String((row as TableRow).key))}
          />

          <BuOperationalCharts buKey={buKey} rows={rows} />
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
