import type { Premissas } from './premissas'

export interface AgentChartSeries {
  name: string
  values: number[]
}

export interface AgentChartArtifact {
  type: 'chart'
  title: string
  chart_type: 'line' | 'bar' | 'waterfall' | 'stacked_bar' | 'grouped_bar' | 'horizontal_bar'
  x: Array<string | number>
  series: AgentChartSeries[]
  unit?: string | null
  reference_line?: Record<string, unknown> | null
}

export interface AgentTableArtifact {
  type: 'table'
  title: string
  columns: string[]
  rows: Array<Array<string | number | null>>
  formats?: Record<string, string>
}

export interface AgentKPIArtifact {
  type: 'kpi'
  title: string
  value: string
  subtitle?: string | null
}

export interface AgentKPIPanelArtifact {
  type: 'kpi_panel'
  title: string
  items: AgentKPIArtifact[]
  highlight_index?: number | null
}

export interface AgentScenarioResult {
  label: string
  scenario_id?: string | null
  premise_deltas?: Record<string, unknown>
  key_metrics?: Record<string, number | string>
  delta_vs_base?: Record<string, number | string>
}

export interface AgentScenarioComparisonArtifact {
  type: 'scenario_comparison'
  title: string
  base_label: string
  scenarios: AgentScenarioResult[]
}

export interface AgentSensitivityMatrixArtifact {
  type: 'sensitivity_matrix'
  title: string
  row_param: string
  col_param: string
  row_values: number[]
  col_values: number[]
  matrix: number[][]
  highlight?: Record<string, unknown> | null
  row_axis_meta?: { base_year?: string; base_value?: number | null } | null
  col_axis_meta?: { base_year?: string; base_value?: number | null } | null
}

export interface AgentSankeyArtifact {
  type: 'sankey'
  title: string
  nodes: Array<{ id: string; label: string; color?: string }>
  links: Array<{ source: string; target: string; value: number; label?: string }>
  unit?: string | null
  year?: number | string | null
  bu?: string | null
}

export type AgentArtifact =
  | AgentChartArtifact
  | AgentTableArtifact
  | AgentKPIArtifact
  | AgentKPIPanelArtifact
  | AgentScenarioComparisonArtifact
  | AgentSensitivityMatrixArtifact
  | AgentSankeyArtifact

export interface AgentMessage {
  role: 'user' | 'assistant'
  content: string
  /** Apenas mensagens do assistente: gráficos/tabelas retornados pela API. */
  artifacts?: AgentArtifact[]
  warnings?: string[]
  dataLineage?: AgentDataLineageItem[] | null
  /** Metadados da última resposta da API (assistente). */
  responseSource?: 'openai' | 'deterministic' | 'fallback'
  intent?: string | null
  scenarioId?: string | null
  validationRepaired?: boolean
  dissertativeMode?: boolean
}

export interface AgentQueryRequest {
  question: string
  premissas?: Premissas | null
  history?: AgentMessage[]
  locale?: string
}

export interface AgentQueryResponse {
  answer_markdown: string
  artifacts: AgentArtifact[]
  confidence: 'high' | 'medium' | 'low'
  data_used: string[]
  warnings: string[]
  data_lineage?: AgentDataLineageItem[] | null
  response_source?: 'openai' | 'deterministic' | 'fallback'
  intent?: string | null
  scenario_id?: string | null
  validation_repaired?: boolean
  tools_executed?: string[]
}

export interface AgentDataLineageItem {
  label: string
  value: number
  source: string
  scenario_id?: string | null
}
