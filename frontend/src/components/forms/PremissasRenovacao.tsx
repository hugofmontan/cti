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
          label="Spread Real (%)"
          type="number"
          step={0.1}
          min={-10}
          max={10}
          value={Number((premissas.renovacao.spread_real * 100).toFixed(2))}
          onChange={(e) => onSpreadChange(Number(e.target.value) / 100)}
          hint="Ex: 2 = 2 p.p. alem da inflacao"
        />
        <Input
          label="Churn Anual (%)"
          type="number"
          step={0.1}
          min={0}
          max={99}
          value={Number((premissas.renovacao.churn * 100).toFixed(2))}
          onChange={(e) => onChurnChange(Number(e.target.value) / 100)}
          hint="Taxa de churn (0-1) aplicada ao FB"
        />
      </div>
    </Panel>
  )
}
