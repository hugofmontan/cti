import type { SimulateResponse } from '../../types'
import { fmtBRL, fmtPct } from '../../utils/formatters'
import { Card, CardGroup } from '../ui/Card'
import styles from './ValuationSummary.module.css'

interface ValuationSummaryProps {
  dcf: SimulateResponse['dcf']
}

export function ValuationSummary({ dcf }: ValuationSummaryProps) {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Resumo Valuation</h2>
      <CardGroup columns={4}>
        <Card
          label="Enterprise Value"
          value={fmtBRL(dcf.enterprise_value)}
          variant="highlight"
        />
        <Card
          label="Equity Value"
          value={fmtBRL(dcf.equity_value)}
          variant="highlight"
        />
        <Card
          label="WACC"
          value={fmtPct(dcf.wacc)}
        />
        <Card
          label="g (Perpetuidade)"
          value={fmtPct(dcf.g)}
        />
      </CardGroup>
    </section>
  )
}
