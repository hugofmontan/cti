import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { Input } from '../ui/Input'
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
        <Input
          label="Spread Real"
          type="number"
          step={0.001}
          value={premissas.renovacao.spread_real}
          onChange={(e) => onSpreadChange(Number(e.target.value))}
          hint="Ex: 0.02 = 2 p.p. alem da inflacao"
        />
        <Input
          label="Churn Anual"
          type="number"
          step={0.005}
          min={0}
          max={0.99}
          value={premissas.renovacao.churn}
          onChange={(e) => onChurnChange(Number(e.target.value))}
          hint="Taxa de churn (0-1), aplicado ao FB"
        />
      </div>
    </Panel>
  )
}
