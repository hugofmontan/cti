import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { Input } from '../ui/Input'
import styles from './PremissasForm.module.css'

interface PremissasDCFProps {
  premissas: Premissas
  onWaccChange: (value: number) => void
  onGChange: (value: number) => void
}

export function PremissasDCF({
  premissas,
  onWaccChange,
  onGChange,
}: PremissasDCFProps) {
  return (
    <Panel title="DCF - WACC e Crescimento Perpetuidade" defaultOpen>
      <div className={styles.row2}>
        <Input
          label="WACC"
          type="number"
          step={0.0001}
          value={premissas.dcf.wacc}
          onChange={(e) => onWaccChange(Number(e.target.value))}
          hint="Decimal, ex: 0.1712 = 17.12%"
        />
        <Input
          label="g (Perpetuidade)"
          type="number"
          step={0.001}
          value={premissas.dcf.g}
          onChange={(e) => onGChange(Number(e.target.value))}
          hint="Taxa de crescimento perpetuo, decimal"
        />
      </div>
    </Panel>
  )
}
