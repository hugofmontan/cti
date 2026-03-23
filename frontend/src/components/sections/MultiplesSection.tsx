import type { SimulateResponse } from '../../types'
import { fmtNumber, fmtPct } from '../../utils/formatters'
import { Card, CardGroup } from '../ui/Card'
import styles from './MultiplesSection.module.css'

interface MultiplesSectionProps {
  dcf: SimulateResponse['dcf']
}

export function MultiplesSection({ dcf }: MultiplesSectionProps) {
  const multiplos = dcf.multiplos || {}

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Multiplos</h2>
      <CardGroup columns={4}>
        <Card
          label="EV / EBITDA"
          value={multiplos.EV_EBITDA_2026 ? `${fmtNumber(multiplos.EV_EBITDA_2026, 1)}x` : '-'}
        />
        <Card
          label="EV / Receita"
          value={multiplos.EV_RL_2026 ? `${fmtNumber(multiplos.EV_RL_2026, 2)}x` : '-'}
        />
        <Card
          label="P/E"
          value={multiplos.P_E_2026 ? `${fmtNumber(multiplos.P_E_2026, 1)}x` : '-'}
        />
        <Card
          label="FCFF Yield"
          value={multiplos.FCFF_Yield_2026 ? fmtPct(multiplos.FCFF_Yield_2026) : '-'}
        />
      </CardGroup>
    </section>
  )
}
