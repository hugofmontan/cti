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
        label="Fator Crescimento Real (%)"
        type="number"
        step={0.5}
        value={Number((premissas.venda_softwares.fator_crescimento_real * 100).toFixed(2))}
        onChange={(e) => onFatorChange(Number(e.target.value) / 100)}
        hint="Ex: 4.50 = 4.50% real + inflacao"
      />
    </Panel>
  )
}
