import type { DRERow } from '../../types'
import { fmtBRLThousandsAccounting } from '../../utils/formatters'
import {
  DRE_DISPLAY_ORDER,
  DRE_LINE_LABELS,
} from '../../utils/constants'
import type { DRERowMerged } from '../../utils/dreMerge'
import { Table } from '../ui/Table'
import tableStyles from '../ui/Table.module.css'
import styles from './ConsolidatedDRE.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

interface ConsolidatedDREProps {
  /** Série já mesclada: histórico (≤2025) + projeção (≥2026). */
  consolidado: DRERowMerged[]
}

type TableRow = {
  key: string
  linha: string
  [year: string]: string | number | null
}

const HIGHLIGHT_ROWS = [
  'receita_liquida',
  'mc1',
  'mc2',
  'ebitda',
  'ebit',
  'lucro_liquido',
]

function getCellValue(row: DRERowMerged, key: keyof DRERow): number | null {
  const value = row[key as keyof DRERowMerged]
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value
  }
  return null
}

export function ConsolidatedDRE({ consolidado }: ConsolidatedDREProps) {
  const { historicalYearStart, historicalYearEnd, allDisplayYears, projectedYears } = useYearConfig()
  const projectedYearEnd = projectedYears[projectedYears.length - 1]
  const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
    const row: TableRow = {
      key,
      linha: DRE_LINE_LABELS[key] || key,
    }

    for (const yearData of consolidado) {
      const year = String(yearData.ano)
      row[year] = getCellValue(yearData, key as keyof DRERow)
    }

    return row
  })

  const columns = [
    {
      key: 'linha',
      header: 'Linha',
      align: 'left' as const,
      width: '220px',
      render: (row: TableRow) => (
        <span className={styles.rowLabel}>{row.linha}</span>
      ),
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

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>DRE Consolidado</h2>
      <p className={styles.legend}>
        <span className={styles.legendSwatch} data-variant="historical" />
        Histórico ({historicalYearStart}–{historicalYearEnd}) — dados em{' '}
        <code>data/original</code>
        <span className={styles.legendGap} />
        <span className={styles.legendSwatch} data-variant="projected" />
        Projeção ({historicalYearEnd + 1}–{projectedYearEnd}) — motor da calculadora
        <span className={styles.legendGap} />
        <strong>Valores exibidos em R$ mil</strong>
      </p>
      <Table
        columns={columns}
        data={tableData}
        className={styles.dreTable}
        striped
        highlightRows={(row) => {
          const rowKey = String((row as TableRow).key)
          return HIGHLIGHT_ROWS.includes(rowKey)
        }}
      />
    </section>
  )
}
