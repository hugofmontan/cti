import type { Premissas, YearKey } from '../../types'
import { Panel } from '../ui/Panel'
import { YearlyInputGrid } from './YearlyInputGrid'

interface PremissasDataScienceProps {
  premissas: Premissas
  onProjetosChange: (year: YearKey, value: number) => void
}

export function PremissasDataScience({
  premissas,
  onProjetosChange,
}: PremissasDataScienceProps) {
  return (
    <Panel title="Data Science - Total de Projetos por Ano" defaultOpen={false}>
      <YearlyInputGrid
        label="Projetos"
        values={premissas.data_science.total_projetos_por_ano}
        onChange={onProjetosChange}
        step={1}
        min={0}
        hint="Quantidade total de projetos planejados por ano"
      />
    </Panel>
  )
}
