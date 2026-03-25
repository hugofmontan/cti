import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { Input } from '../ui/Input'
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
        <Input
          label="Taxa Conversao FOPM"
          type="number"
          step={0.01}
          min={0}
          max={30}
          value={Number((premissas.ams.taxa_conversao_fopm * 100).toFixed(2))}
          onChange={(e) => onTaxaConversaoChange(Number(e.target.value) / 100)}
          hint="Ex: 9.58 = 9.58%"
        />
        <Input
          label="Churn Anual"
          type="number"
          step={0.5}
          min={0}
          max={99}
          value={Number((premissas.ams.churn * 100).toFixed(2))}
          onChange={(e) => onChurnChange(Number(e.target.value) / 100)}
          hint="Ex: 0.00 = 0.00%"
        />
      </div>
    </Panel>
  )
}
