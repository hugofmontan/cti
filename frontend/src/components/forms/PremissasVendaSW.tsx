import type { Premissas } from '../../types'
import { Panel } from '../ui/Panel'
import { Input } from '../ui/Input'

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
      <Input
        label="Fator Crescimento Real"
        type="number"
        step={0.005}
        value={premissas.venda_softwares.fator_crescimento_real}
        onChange={(e) => onFatorChange(Number(e.target.value))}
        hint="Ex: 0.045 = 4.5% real + inflacao"
      />
    </Panel>
  )
}
