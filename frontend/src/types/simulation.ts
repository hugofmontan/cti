import type { Premissas } from './premissas'

export interface DRERow {
  ano: number
  receita_bruta: number
  deducoes?: number
  impostos_sv?: number
  receita_liquida: number
  incentivos?: number
  gastos_pessoal?: number
  outras_desp_diretas?: number
  mc1: number
  mc1_pct_rl?: number
  remuneracao_socios?: number
  mc2: number
  mc2_pct_rl?: number
  outras_desp_adm?: number
  honorarios_adm?: number
  rateio_adm?: number
  ebitda: number
  da_consolidada?: number
  depreciacao_amort?: number
  depreciacao_amortizacao?: number
  ebit: number
  receita_financeira?: number
  despesa_financeira?: number
  lair: number
  irpj_csll?: number
  lucro_liquido: number
  ebitda_pct_rl?: number
  lucro_liquido_pct_rl?: number
  /** Headcount (média / premissa) — histórico via `historical-dre`, projeção via simulação. */
  n_funcionarios?: number
  [key: string]: string | number | undefined
}

export interface FluxoRow {
  ano: number
  ebit: number
  ir_sobre_ebit: number
  nopat: number
  da_total: number
  capex: number
  delta_ncg: number
  fcff: number
  lucro_liquido: number
  dividendos: number
  caixa_final: number
  [key: string]: string | number | undefined
}

export interface BPRow {
  ano: number
  caixa?: number
  clientes?: number
  partes_relacionadas?: number
  adiantamentos?: number
  impostos_recuperar?: number
  outros_ac?: number
  ativo_circulante_total?: number
  ativo_fiscal_diferido?: number
  imobilizado?: number
  depr_acumulada?: number
  ativo_nao_circulante_total?: number
  total_ativo?: number
  contas_a_pagar?: number
  fornecedores?: number
  obrig_trabalhistas?: number
  obrig_fiscais?: number
  provisoes?: number
  outras_obrigacoes?: number
  passivo_circulante_total?: number
  receitas_diferidas?: number
  passivo_nao_circulante_total?: number
  pl?: number
  total_passivo_pl?: number
  [key: string]: string | number | undefined
}

export interface Multiplos {
  EV_EBITDA_2026?: number
  EV_RL_2026?: number
  P_E_2026?: number
  FCFF_Yield_2026?: number
  [key: string]: number | undefined
}

export interface DCFResult {
  wacc: number
  g: number
  enterprise_value: number
  equity_value: number
  soma_vp_fcffs: number
  vp_fcff_por_ano: Record<string, number>
  multiplos: Multiplos
}

export interface SimulateResponse {
  premissas_efetivas: Premissas
  dre: Record<string, DRERow[]>
  consolidado: DRERow[]
  bp: BPRow[]
  bp_historico?: BPRow[]
  fluxo: FluxoRow[]
  dcf: DCFResult
  year_config?: {
    historical_year_start: number
    historical_year_end: number
    projected_year_start: number
    projected_years: number[]
  }
  warnings: string[]
}
