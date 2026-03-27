import type { BPRow } from '../../types'
import { fmtBRLThousandsAccounting } from '../../utils/formatters'
import { Table } from '../ui/Table'
import tableStyles from '../ui/Table.module.css'
import styles from './BalanceSheetSection.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

type BpRowMerged = Partial<BPRow> & { ano: number }
type TableRow = { key: string; linha: string; [year: string]: string | number | null }

const BP_LINES: Array<{ key: keyof BPRow; label: string }> = [
  { key: 'ativo_circulante_total', label: 'Ativo Circulante - Total' },
  { key: 'caixa', label: 'Caixa e Equivalentes de Caixa' },
  { key: 'clientes', label: 'Contas a Receber (Clientes)' },
  { key: 'partes_relacionadas', label: 'Partes Relacionadas' },
  { key: 'adiantamentos', label: 'Adiantamentos' },
  { key: 'impostos_recuperar', label: 'Impostos a Recuperar' },
  { key: 'outros_ac', label: 'Outros Ativos Circulantes' },
  { key: 'ativo_nao_circulante_total', label: 'Ativo Não Circulante - Total' },
  { key: 'ativo_fiscal_diferido', label: 'Ativo Fiscal Diferido' },
  { key: 'imobilizado', label: 'Imobilizado e Intangível (Bruto)' },
  { key: 'depr_acumulada', label: 'Depreciação e Amortização Acumulada' },
  { key: 'total_ativo', label: 'Total do Ativo' },
  { key: 'passivo_circulante_total', label: 'Passivo Circulante - Total' },
  { key: 'contas_a_pagar', label: 'Contas a Pagar' },
  { key: 'fornecedores', label: 'Fornecedores' },
  { key: 'obrig_trabalhistas', label: 'Obrigações Trabalhistas e Sociais' },
  { key: 'obrig_fiscais', label: 'Obrigações Fiscais' },
  { key: 'provisoes', label: 'Provisões' },
  { key: 'outras_obrigacoes', label: 'Outras Obrigações' },
  { key: 'passivo_nao_circulante_total', label: 'Passivo Não Circulante - Total' },
  { key: 'receitas_diferidas', label: 'Receitas Diferidas' },
  { key: 'pl', label: 'Patrimônio Líquido' },
  { key: 'total_passivo_pl', label: 'Total do Passivo e PL' },
]

const HIGHLIGHT_ROWS = new Set([
  'ativo_circulante_total',
  'ativo_nao_circulante_total',
  'total_ativo',
  'passivo_circulante_total',
  'passivo_nao_circulante_total',
  'pl',
  'total_passivo_pl',
])

interface BalanceSheetSectionProps {
  bp: BpRowMerged[]
}

export function BalanceSheetSection({ bp }: BalanceSheetSectionProps) {
  const { historicalYearStart, historicalYearEnd, allDisplayYears, projectedYears } = useYearConfig()
  const projectedYearEnd = projectedYears[projectedYears.length - 1]

  const tableData: TableRow[] = BP_LINES.map(({ key, label }) => {
    const row: TableRow = { key: String(key), linha: label }
    for (const yearData of bp) {
      const year = String(yearData.ano)
      const value = yearData[key]
      row[year] = typeof value === 'number' && !Number.isNaN(value) ? value : null
    }
    return row
  })

  const columns = [
    {
      key: 'linha',
      header: 'Linha',
      align: 'left' as const,
      width: '260px',
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

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Balanço Patrimonial</h2>
      <p className={styles.legend}>
        <span className={styles.legendSwatch} data-variant="historical" />
        Histórico ({historicalYearStart}–{historicalYearEnd})
        <span className={styles.legendGap} />
        <span className={styles.legendSwatch} data-variant="projected" />
        Projeção ({historicalYearEnd + 1}–{projectedYearEnd})
        <span className={styles.legendGap} />
        <strong>Valores exibidos em R$ mil</strong>
      </p>
      <Table
        columns={columns}
        data={tableData}
        className={styles.bpTable}
        striped
        highlightRows={(row) => HIGHLIGHT_ROWS.has(String((row as TableRow).key))}
      />
    </section>
  )
}
