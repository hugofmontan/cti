import type { Premissas, YearKey } from '../../types'
import { Panel } from '../ui/Panel'
import { YearlySliderGrid } from './YearlySliderGrid'

interface PremissasMacroProps {
  premissas: Premissas
  onInflacaoChange: (year: YearKey, value: number) => void
  onSelicChange: (year: YearKey, value: number) => void
}

export function PremissasMacro({ premissas, onInflacaoChange, onSelicChange }: PremissasMacroProps) {
  return (
    <Panel title="Macro - Inflacao Focus por ano" defaultOpen={true}>
      <YearlySliderGrid
        label="Inflacao Focus"
        values={premissas.inflacao_focus_por_ano}
        onChange={onInflacaoChange}
        min={0}
        max={0.3}
        step={0.001}
        hint="Premissa usada no motor (decimal). Exibida como porcentagem e dinâmica por horizonte ativo."
        formatValue={(v) => `${(v * 100).toFixed(2)}%`}
        numberInputScale={100}
        numberInputStep={0.01}
      />
      <YearlySliderGrid
        label="Selic Focus"
        values={premissas.selic_focus_por_ano}
        onChange={onSelicChange}
        min={0}
        max={0.3}
        step={0.001}
        hint="Premissa usada no cálculo de receita financeira (decimal). Exibida como porcentagem e dinâmica por horizonte ativo."
        formatValue={(v) => `${(v * 100).toFixed(2)}%`}
        numberInputScale={100}
        numberInputStep={0.01}
      />
    </Panel>
  )
}
