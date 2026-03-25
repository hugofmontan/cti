import type { Premissas } from './premissas'

export interface AgentChartSeries {
  name: string
  values: number[]
}

export interface AgentChartArtifact {
  type: 'chart'
  title: string
  chart_type: 'line' | 'bar'
  x: Array<string | number>
  series: AgentChartSeries[]
  unit?: string | null
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

export type AgentArtifact = AgentChartArtifact | AgentTableArtifact | AgentKPIArtifact

export interface AgentMessage {
  role: 'user' | 'assistant'
  content: string
  /** Apenas mensagens do assistente: gráficos/tabelas retornados pela API. */
  artifacts?: AgentArtifact[]
  warnings?: string[]
  /** Metadados da última resposta da API (assistente). */
  responseSource?: 'openai' | 'deterministic' | 'fallback'
  intent?: string | null
  scenarioId?: string | null
  validationRepaired?: boolean
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
  response_source?: 'openai' | 'deterministic' | 'fallback'
  intent?: string | null
  scenario_id?: string | null
  validation_repaired?: boolean
}
