import type { DRERow } from '../../types'
import { fmtBRL } from '../../utils/formatters'
import { DRE_LINE_LABELS, DRE_DISPLAY_ORDER, YEARS } from '../../utils/constants'
import { Table } from '../ui/Table'
import styles from './ConsolidatedDRE.module.css'

interface ConsolidatedDREProps {
  consolidado: DRERow[]
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

export function ConsolidatedDRE({ consolidado }: ConsolidatedDREProps) {
  // Transform data: rows are DRE lines, columns are years
  const tableData: TableRow[] = DRE_DISPLAY_ORDER.map((key) => {
    const row: TableRow = {
      linha: DRE_LINE_LABELS[key] || key,
    }

    for (const yearData of consolidado) {
      const year = String(yearData.ano)
      const value = yearData[key as keyof DRERow]
      row[year] = typeof value === 'number' ? fmtBRL(value) : '-'
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
    ...YEARS.map((year) => ({
      key: year,
      header: year,
      align: 'right' as const,
    })),
  ]

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>DRE Consolidado</h2>
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
