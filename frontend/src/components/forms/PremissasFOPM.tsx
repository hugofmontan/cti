import type { Premissas, YearKey } from '../../types'
import { Panel } from '../ui/Panel'
import { YearlySliderGrid } from './YearlySliderGrid'

interface PremissasFOPMProps {
  premissas: Premissas
  onHeadcountChange: (year: YearKey, value: number) => void
  onOciosidadeChange: (year: YearKey, value: number) => void
}

export function PremissasFOPM({
  premissas,
  onHeadcountChange,
  onOciosidadeChange,
}: PremissasFOPMProps) {
  return (
    <Panel title="FOPM - Funcionarios e Ociosidade (2026-2030)" defaultOpen={false}>
      <YearlySliderGrid
        label="Headcount"
        values={premissas.fopm.headcount_por_ano}
        onChange={onHeadcountChange}
        min={0}
        max={100}
        step={1}
        hint="Numero de funcionarios planejados por ano (slider)."
        formatValue={(v) => `${Math.round(v)}`}
        numberInputScale={1}
        numberInputStep={1}
      />
      <YearlySliderGrid
        label="Ociosidade"
        values={premissas.fopm.ociosidade_por_ano}
        onChange={onOciosidadeChange}
        min={0}
        max={0.5}
        step={0.01}
        hint="Exibido como porcentagem (mantemos o modelo em decimal)."
        formatValue={(v) => `${Math.round(v * 100)}%`}
        numberInputScale={100}
        numberInputStep={1}
      />
    </Panel>
  )
}
