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
          step={0.0001}
          value={premissas.ams.taxa_conversao_fopm}
          onChange={(e) => onTaxaConversaoChange(Number(e.target.value))}
          hint="Taxa de conversao FB FOPM para incremental AMS"
        />
        <Input
          label="Churn Anual"
          type="number"
          step={0.005}
          min={0}
          max={0.99}
          value={premissas.ams.churn}
          onChange={(e) => onChurnChange(Number(e.target.value))}
          hint="Churn anual na base retida (0-1)"
        />
      </div>
    </Panel>
  )
}
