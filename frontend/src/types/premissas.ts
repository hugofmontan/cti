export type YearKey = `${number}`

export interface FOPMPremissas {
  headcount_por_ano: Record<YearKey, number>
  ociosidade_por_ano: Record<YearKey, number>
}

export interface RenovacaoPremissas {
  spread_real: number
  churn: number
}

export interface AMSPremissas {
  taxa_conversao_fopm: number
  churn: number
}

export interface VendaSoftwaresPremissas {
  fator_crescimento_real: number
}

export interface DataSciencePremissas {
  headcount_por_ano: Record<YearKey, number>
  ociosidade_por_ano: Record<YearKey, number>
}

export interface DCFPremissas {
  wacc: number
  g: number
}

export interface Premissas {
  inflacao_focus_por_ano: Record<YearKey, number>
  selic_focus_por_ano: Record<YearKey, number>
  fopm: FOPMPremissas
  renovacao: RenovacaoPremissas
  ams: AMSPremissas
  venda_softwares: VendaSoftwaresPremissas
  data_science: DataSciencePremissas
  dcf: DCFPremissas
}
