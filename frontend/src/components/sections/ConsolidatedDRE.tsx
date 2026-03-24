import type { DRERow } from '../../types'
import { fmtBRL } from '../../utils/formatters'
import {
  ALL_DISPLAY_YEARS,
  DRE_DISPLAY_ORDER,
  DRE_LINE_LABELS,
  HISTORICAL_YEAR_END,
} from '../../utils/constants'
import type { DRERowMerged } from '../../utils/dreMerge'
import { Table } from '../ui/Table'
import tableStyles from '../ui/Table.module.css'
import styles from './ConsolidatedDRE.module.css'

interface ConsolidatedDREProps {
  /** Série já mesclada: histórico (≤2025) + projeção (≥2026). */
  consolidado: DRERowMerged[]
}

type TableRow = {
  linha: string
  [year: string]: string | number
}

const HIGHLIGHT_ROWS = [
  'receita_liquida',
  'mc1',
  'mc2',
  'ebitda',
  'ebit',
  'lucro_liquido',
]

function getCellValue(row: DRERowMerged, key: keyof DRERow): string {
  const value = row[key as keyof DRERowMerged]
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return fmtBRL(value)
  }
  return '—'
}

export function ConsolidatedDRE({ consolidado }: ConsolidatedDREProps) {
  const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
    const row: TableRow = {
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
      width: '200px',
    },
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

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>DRE Consolidado</h2>
      <p className={styles.legend}>
        <span className={styles.legendSwatch} data-variant="historical" />
        Histórico (2018–{HISTORICAL_YEAR_END}) — dados em{' '}
        <code>data/original</code>
        <span className={styles.legendGap} />
        <span className={styles.legendSwatch} data-variant="projected" />
        Projeção ({HISTORICAL_YEAR_END + 1}–2030) — motor da calculadora
      </p>
      <Table
        columns={columns}
        data={tableData}
        striped
        highlightRows={(row) => {
          const label = row.linha as string
          return HIGHLIGHT_ROWS.some((key) => DRE_LINE_LABELS[key] === label)
        }}
      />
    </section>
  )
}
