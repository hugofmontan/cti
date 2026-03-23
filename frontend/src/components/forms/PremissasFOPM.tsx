import type { Premissas, YearKey } from '../../types'
import { Panel } from '../ui/Panel'
import { YearlyInputGrid } from './YearlyInputGrid'

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
      <YearlyInputGrid
        label="Headcount"
        values={premissas.fopm.headcount_por_ano}
        onChange={onHeadcountChange}
        step={1}
        min={1}
        hint="Numero de funcionarios planejados por ano"
      />
      <YearlyInputGrid
        label="Ociosidade"
        values={premissas.fopm.ociosidade_por_ano}
        onChange={onOciosidadeChange}
        step={0.005}
        min={0}
        max={1}
        hint="Taxa de ociosidade (0-1), ex: 0.05 = 5%"
      />
    </Panel>
  )
}
