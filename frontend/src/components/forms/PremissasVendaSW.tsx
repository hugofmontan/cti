import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { PercentInput } from '../ui/PercentInput'

interface PremissasVendaSWProps {
  premissas: Premissas
  onFatorChange: (value: number) => void
}

export function PremissasVendaSW({
  premissas,
  onFatorChange,
}: PremissasVendaSWProps) {
  return (
    <Panel title="Venda de Softwares - Crescimento Real" defaultOpen={false}>
      <PercentInput
        label="Fator Crescimento Real (%)"
        rawValue={premissas.venda_softwares.fator_crescimento_real}
        onChange={onFatorChange}
        step={0.5}
        hint="Ex: 4.50 = 4.50% real + inflacao"
      />
    </Panel>
  )
}
