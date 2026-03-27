import { BU_KEYS } from './constants'
import type { DRERowMerged } from './dreMerge'

export interface BuOperationalPoint {
  ano: string
  faturamento_bruto: number
  n_funcionarios: number
  ebitda: number
  margem_ebitda_pct: number
  margem_ebitda_pct_h: number | null
  margem_ebitda_pct_p: number | null
  faturamento_bruto_h: number | null
  faturamento_bruto_p: number | null
  n_funcionarios_h: number | null
  n_funcionarios_p: number | null
  ebitda_h: number | null
  ebitda_p: number | null
  isHistorical: boolean
}

export function buildBuOperationalChartData(
  rows: DRERowMerged[],
  allDisplayYears: number[],
  historicalYearEnd: number,
): BuOperationalPoint[] {
  return allDisplayYears.map((y) => {
    const r = rows.find((row) => row.ano === y)
    const faturamentoBruto =
      typeof r?.faturamento_bruto === 'number'
        ? r.faturamento_bruto
        : typeof r?.receita_bruta === 'number'
          ? r.receita_bruta
          : 0
    const ebitda = typeof r?.ebitda === 'number' ? r.ebitda : 0
    const receitaLiquida = typeof r?.receita_liquida === 'number' ? r.receita_liquida : 0
    const margem = receitaLiquida ? ebitda / receitaLiquida : 0
    const isHistorical = y <= historicalYearEnd
    const faturamentoBrutoH = isHistorical ? faturamentoBruto : null
    const faturamentoBrutoP = !isHistorical ? faturamentoBruto : null

    const nFuncionariosBase =
      typeof r?.n_funcionarios === 'number'
        ? r.n_funcionarios
        : typeof (r as unknown as { n_funcionarios_adm?: unknown }).n_funcionarios_adm === 'number'
          ? (r as unknown as { n_funcionarios_adm: number }).n_funcionarios_adm
          : 0

    const nFuncionariosH = isHistorical ? nFuncionariosBase : null
    const nFuncionariosP = !isHistorical ? nFuncionariosBase : null
    const ebitdaH = isHistorical ? ebitda : null
    const ebitdaP = !isHistorical ? ebitda : null
    return {
      ano: String(y),
      faturamento_bruto: faturamentoBruto,
      n_funcionarios: nFuncionariosBase,
      ebitda,
      margem_ebitda_pct: margem,
      margem_ebitda_pct_h: isHistorical ? margem : null,
      margem_ebitda_pct_p: !isHistorical ? margem : null,
      faturamento_bruto_h: faturamentoBrutoH,
      faturamento_bruto_p: faturamentoBrutoP,
      n_funcionarios_h: nFuncionariosH,
      n_funcionarios_p: nFuncionariosP,
      ebitda_h: ebitdaH,
      ebitda_p: ebitdaP,
      isHistorical,
    }
  })
}

/** Mesma ordem de abas do detalhamento por BU na UI. */
export function listBuKeysOrdered(dre: Record<string, DRERowMerged[]> | null | undefined): string[] {
  if (!dre) return []
  const knownBuKeys = BU_KEYS as unknown as string[]
  const extraBuKeys = Object.keys(dre).filter((k) => !knownBuKeys.includes(k))
  return [...knownBuKeys, ...extraBuKeys]
}
