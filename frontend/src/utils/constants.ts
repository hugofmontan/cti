import type { YearKey } from '../types'

export const YEARS: YearKey[] = ['2026', '2027', '2028', '2029', '2030']

export const BU_NAMES = {
  fopm: 'FOPM',
  renovacao: 'Renovacao',
  ams: 'AMS',
  venda_sw: 'Venda SW',
  data_science: 'Data Science',
} as const

export type BUKey = keyof typeof BU_NAMES

export const BU_KEYS: BUKey[] = ['fopm', 'renovacao', 'ams', 'venda_sw', 'data_science']

export const CHART_COLORS = {
  primary: '#2563eb',
  secondary: '#059669',
  tertiary: '#d97706',
  quaternary: '#7c3aed',
  quinary: '#64748b',
  // BU specific colors
  fopm: '#2563eb',
  renovacao: '#059669',
  ams: '#d97706',
  venda_sw: '#7c3aed',
  data_science: '#dc2626',
} as const

export const CHART_COLORS_LIGHT = {
  primary: '#60a5fa',
  secondary: '#34d399',
  tertiary: '#fbbf24',
  quaternary: '#a78bfa',
  quinary: '#94a3b8',
} as const

export const DRE_LINE_LABELS: Record<string, string> = {
  receita_bruta: 'Receita Bruta',
  deducoes: '(-) Impostos',
  receita_liquida: 'Receita Liquida',
  incentivos: '(-) Incentivos',
  gastos_pessoal: '(-) Gastos com Pessoal',
  outras_desp_diretas: '(-) Outras Despesas Diretas',
  mc1: 'MC1',
  remuneracao_socios: '(-) Remuneracao Socios',
  mc2: 'MC2',
  outras_desp_adm: '(-) Outras Despesas Administrativas',
  honorarios_adm: '(-) Honorarios ADM',
  ebitda: 'EBITDA',
  da_consolidada: '(-) D&A',
  ebit: 'EBIT',
  receita_financeira: '(+) Receita Financeira',
  despesa_financeira: '(-) Despesa Financeira',
  lair: 'LAIR',
  irpj_csll: '(-) IR/CSLL',
  lucro_liquido: 'Lucro Liquido',
}

export const DRE_DISPLAY_ORDER: (keyof typeof DRE_LINE_LABELS)[] = [
  'receita_bruta',
  'deducoes',
  'receita_liquida',
  'incentivos',
  'gastos_pessoal',
  'outras_desp_diretas',
  'mc1',
  'remuneracao_socios',
  'mc2',
  'outras_desp_adm',
  'honorarios_adm',
  'ebitda',
  'da_consolidada',
  'ebit',
  'receita_financeira',
  'despesa_financeira',
  'lair',
  'irpj_csll',
  'lucro_liquido',
]

export const API_BASE_URL = '/api'
