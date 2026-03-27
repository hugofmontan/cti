import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { PercentInput } from '../ui/PercentInput'
import styles from './PremissasForm.module.css'

interface PremissasRenovacaoProps {
  premissas: Premissas
  onSpreadChange: (value: number) => void
  onChurnChange: (value: number) => void
}

export function PremissasRenovacao({
  premissas,
  onSpreadChange,
  onChurnChange,
}: PremissasRenovacaoProps) {
  return (
    <Panel title="Renovacao - Spread Real e Churn" defaultOpen={false}>
      <div className={styles.row2}>
        <PercentInput
          label="Spread Real (%)"
          rawValue={premissas.renovacao.spread_real}
          onChange={onSpreadChange}
          min={-10}
          max={10}
          step={0.1}
          hint="Ex: 2 = 2 p.p. alem da inflacao"
        />
        <PercentInput
          label="Churn Anual (%)"
          rawValue={premissas.renovacao.churn}
          onChange={onChurnChange}
          min={0}
          max={99}
          step={0.1}
          hint="Taxa de churn (0-1) aplicada ao FB"
        />
      </div>
    </Panel>
  )
}
