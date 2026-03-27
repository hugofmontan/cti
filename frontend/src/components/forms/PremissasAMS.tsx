import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { PercentInput } from '../ui/PercentInput'
import styles from './PremissasForm.module.css'

interface PremissasAMSProps {
  premissas: Premissas
  onTaxaConversaoChange: (value: number) => void
  onChurnChange: (value: number) => void
}

export function PremissasAMS({
  premissas,
  onTaxaConversaoChange,
  onChurnChange,
}: PremissasAMSProps) {
  return (
    <Panel title="AMS - Conversao FOPM e Churn" defaultOpen={false}>
      <div className={styles.row2}>
        <PercentInput
          label="Taxa Conversao FOPM"
          rawValue={premissas.ams.taxa_conversao_fopm}
          onChange={onTaxaConversaoChange}
          min={0}
          max={30}
          step={0.01}
          hint="Ex: 9.58 = 9.58%"
        />
        <PercentInput
          label="Churn Anual"
          rawValue={premissas.ams.churn}
          onChange={onChurnChange}
          min={0}
          max={99}
          step={0.5}
          hint="Ex: 0.00 = 0.00%"
        />
      </div>
    </Panel>
  )
}
