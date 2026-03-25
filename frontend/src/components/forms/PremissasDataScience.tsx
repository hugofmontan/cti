import type { Premissas, YearKey } from '../../types'
import { Panel } from '../ui/Panel'
import { YearlySliderGrid } from './YearlySliderGrid'

interface PremissasDataScienceProps {
  premissas: Premissas
  onHeadcountChange: (year: YearKey, value: number) => void
  onOciosidadeChange: (year: YearKey, value: number) => void
}

export function PremissasDataScience({
  premissas,
  onHeadcountChange,
  onOciosidadeChange,
}: PremissasDataScienceProps) {
  return (
    <Panel title="Data Science — Headcount e ociosidade" defaultOpen={false}>
      <YearlySliderGrid
        label="Funcionarios"
        values={premissas.data_science.headcount_por_ano}
        onChange={onHeadcountChange}
        min={0}
        max={30}
        step={1}
        hint="Projetos são derivados da capacidade (HC × 160 × 12 × (1 − ociosidade) ÷ 3.840)."
        formatValue={(v) => `${Math.round(v)}`}
        numberInputScale={1}
        numberInputStep={1}
      />
      <YearlySliderGrid
        label="Ociosidade"
        values={premissas.data_science.ociosidade_por_ano}
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
