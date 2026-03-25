import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { SliderValueWithInput } from '../ui/SliderValueWithInput'
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
        <SliderValueWithInput
          label="WACC"
          value={premissas.dcf.wacc}
          onChange={onWaccChange}
          min={0.05}
          max={0.35}
          step={0.0005}
          hint="Exibido como % (modelo usa decimal)."
          displayScale={100}
          formatDisplay={(v) => `${v.toFixed(2)}%`}
          inputScale={100}
          inputStep={0.1}
          displayDecimals={2}
        />
        <SliderValueWithInput
          label="g (Perpetuidade)"
          value={premissas.dcf.g}
          onChange={onGChange}
          min={0}
          max={0.08}
          step={0.001}
          hint="Exibido como % (modelo usa decimal)."
          displayScale={100}
          formatDisplay={(v) => `${v.toFixed(2)}%`}
          inputScale={100}
          inputStep={0.1}
          displayDecimals={2}
        />
      </div>
    </Panel>
  )
}
