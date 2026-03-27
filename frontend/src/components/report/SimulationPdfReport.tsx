import { forwardRef, useMemo } from 'react'
import type { SimulateResponse } from '../../types'
import type { DRERowMerged } from '../../utils/dreMerge'
import { listBuKeysOrdered } from '../../utils/buOperationalChartData'
import {
  BuOperationalCharts,
  DCFWaterfallChart,
  FCFFBarChart,
  MarginTrendChart,
  RevenueByBUChart,
  RevenueByBUPctChart,
} from '../charts'
import { MultiplesSection, ValuationSummary } from '../sections'
import { PremissasPdfSummary } from './PremissasPdfSummary'
import styles from './SimulationPdfReport.module.css'

export interface SimulationPdfReportProps {
  result: SimulateResponse
  mergedDre: Record<string, DRERowMerged[]> | null
  mergedConsolidado: DRERowMerged[]
  /** Texto exibido no cabeçalho (definido no momento da exportação). */
  generatedAtLabel: string
}

export const SimulationPdfReport = forwardRef<HTMLDivElement, SimulationPdfReportProps>(
  function SimulationPdfReport(
    { result, mergedDre, mergedConsolidado, generatedAtLabel },
    ref,
  ) {
    const buKeysOrdered = useMemo(() => listBuKeysOrdered(mergedDre), [mergedDre])

    return (
      <div ref={ref} className={styles.root}>
        <header className={styles.header}>
          <h1 className={styles.title}>Relatório de simulação</h1>
          <p className={styles.subtitle}>{generatedAtLabel || '—'}</p>
        </header>

        <PremissasPdfSummary premissas={result.premissas_efetivas} />

        <ValuationSummary dcf={result.dcf} />
        <MultiplesSection dcf={result.dcf} />

        <div className={styles.chartBlock}>
          <DCFWaterfallChart dcf={result.dcf} />
        </div>
        <div className={styles.chartBlock}>
          <RevenueByBUChart dre={result.dre} mergedDre={mergedDre} />
        </div>
        <div className={styles.chartBlock}>
          <RevenueByBUPctChart dre={result.dre} mergedDre={mergedDre} />
        </div>
        <div className={styles.chartBlock}>
          <MarginTrendChart consolidado={mergedConsolidado} />
        </div>
        <div className={styles.chartBlock}>
          <FCFFBarChart fluxo={result.fluxo} />
        </div>

        {buKeysOrdered.length > 0 ? (
          <section className={styles.buPdfSection}>
            <h2 className={styles.buPdfTitle}>Detalhamento por BU</h2>
            <p className={styles.buPdfLead}>
              Faturamento bruto e funcionários; EBITDA e margem EBITDA — mesmo conteúdo do painel Detalhamento por BU no
              dashboard.
            </p>
            {buKeysOrdered.map((buKey) => (
              <div key={buKey} className={styles.chartBlock}>
                <BuOperationalCharts buKey={buKey} rows={mergedDre?.[buKey] ?? []} />
              </div>
            ))}
          </section>
        ) : null}

        {result.warnings?.length ? (
          <div className={styles.warnings}>
            <h3 className={styles.warningsTitle}>Avisos do motor</h3>
            <ul className={styles.warningsList}>
              {result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    )
  },
)
