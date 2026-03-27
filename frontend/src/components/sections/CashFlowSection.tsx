import type { FluxoRow } from '../../types'
import { fmtBRL } from '../../utils/formatters'
import { Table } from '../ui/Table'
import styles from './CashFlowSection.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

interface CashFlowSectionProps {
  fluxo: FluxoRow[]
}

type TableRow = {
  linha: string
  [year: string]: string | number
}

const FLUXO_LINES = [
  { key: 'ebit', label: 'EBIT' },
  { key: 'ir_sobre_ebit', label: '(-) IR/CSLL (AMS — base LAIR)' },
  { key: 'nopat', label: 'NOPAT' },
  { key: 'da_total', label: '(+) D&A' },
  { key: 'delta_ncg', label: '(-) Delta NCG' },
  { key: 'capex', label: '(-) CAPEX' },
  { key: 'fcff', label: 'FCFF' },
  { key: 'dividendos', label: '(-) Dividendos' },
  { key: 'caixa_final', label: 'Caixa Final' },
]

export function CashFlowSection({ fluxo }: CashFlowSectionProps) {
  const { projectedYears } = useYearConfig()
  const tableData: TableRow[] = FLUXO_LINES.map(({ key, label }) => {
    const row: TableRow = { linha: label }

    for (const yearData of fluxo) {
      const year = String(yearData.ano)
      const value = yearData[key as keyof FluxoRow]
      row[year] = typeof value === 'number' ? fmtBRL(value) : '-'
    }

    return row
  })

  const columns = [
    {
      key: 'linha',
      header: 'Linha',
      align: 'left' as const,
      width: '180px',
    },
    ...projectedYears.map((year) => ({
      key: String(year),
      header: String(year),
      align: 'right' as const,
    })),
  ]

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Fluxo de Caixa (FCFF)</h2>
      <Table
        columns={columns}
        data={tableData}
        striped
        highlightRows={(row) => row.linha === 'FCFF'}
      />
    </section>
  )
}
