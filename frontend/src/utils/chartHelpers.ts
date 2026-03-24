import type { DRERow, FluxoRow, SimulateResponse } from '../types'
import { ALL_DISPLAY_YEARS, BU_KEYS, CHART_COLORS, HISTORICAL_YEAR_END, YEARS } from './constants'
import type { DRERowMerged } from './dreMerge'

export interface FCFFChartData {
  ano: string
  fcff: number
}

export interface RevenueByBUChartData {
  ano: string
  fopm: number
  renovacao: number
  ams: number
  venda_sw: number
  data_science: number
  total: number
}

export interface MarginTrendChartData {
  ano: string
  ebitda_pct: number
  ebit_pct: number
  ll_pct: number
}

/** Série com duas linhas (histórico vs projeção) para cores distintas. */
export interface MarginTrendSplitData {
  ano: string
  ebitda_pct_h: number | null
  ebitda_pct_p: number | null
  ebit_pct_h: number | null
  ebit_pct_p: number | null
  ll_pct_h: number | null
  ll_pct_p: number | null
}

export interface WaterfallChartData {
  name: string
  value: number
  fill: string
}

/**
 * Transform fluxo data for FCFF bar chart
 */
export function transformFCFFData(fluxo: FluxoRow[]): FCFFChartData[] {
  return fluxo.map((row) => ({
    ano: String(row.ano),
    fcff: Number(row.fcff),
  }))
}

/**
 * Transform DRE data for stacked revenue by BU chart
 */
export function transformRevenueByBUData(
  dre: Record<string, DRERow[]>
): RevenueByBUChartData[] {
  const result: RevenueByBUChartData[] = []

  for (const year of YEARS) {
    const yearNum = parseInt(year)
    const dataPoint: RevenueByBUChartData = {
      ano: year,
      fopm: 0,
      renovacao: 0,
      ams: 0,
      venda_sw: 0,
      data_science: 0,
      total: 0,
    }

    for (const buKey of BU_KEYS) {
      const buData = dre[buKey]
      if (buData) {
        const yearRow = buData.find((row) => row.ano === yearNum)
        if (yearRow) {
          dataPoint[buKey] = yearRow.receita_liquida
          dataPoint.total += yearRow.receita_liquida
        }
      }
    }

    result.push(dataPoint)
  }

  return result
}

function _pctLine(numer?: number, denom?: number): number {
  if (typeof numer !== 'number' || typeof denom !== 'number' || denom === 0) return 0
  return (numer / denom) * 100
}

/**
 * Transform consolidado data for margin trend line chart
 */
export function transformMarginTrendData(
  consolidado: DRERow[]
): MarginTrendChartData[] {
  return consolidado.map((row) => ({
    ano: String(row.ano),
    ebitda_pct: _pctLine(row.ebitda, row.receita_liquida),
    ebit_pct: _pctLine(row.ebit, row.receita_liquida),
    ll_pct: _pctLine(row.lucro_liquido, row.receita_liquida),
  }))
}

/**
 * Margens com colunas separadas para histórico (até 2025) e projeção (2026+).
 */
export function transformMarginTrendDataSplit(
  consolidado: DRERowMerged[],
): MarginTrendSplitData[] {
  return consolidado.map((row) => {
    const rl = row.receita_liquida
    const e = _pctLine(row.ebitda, rl)
    const eb = _pctLine(row.ebit, rl)
    const ll = _pctLine(row.lucro_liquido, rl)
    const isHist = row.ano <= HISTORICAL_YEAR_END
    return {
      ano: String(row.ano),
      ebitda_pct_h: isHist ? e : null,
      ebitda_pct_p: !isHist ? e : null,
      ebit_pct_h: isHist ? eb : null,
      ebit_pct_p: !isHist ? eb : null,
      ll_pct_h: isHist ? ll : null,
      ll_pct_p: !isHist ? ll : null,
    }
  })
}

/**
 * Receita líquida por BU — histórico + projeção (série completa).
 */
export function transformRevenueByBUDataMerged(
  mergedDre: Record<string, DRERowMerged[]>,
): RevenueByBUChartData[] {
  return ALL_DISPLAY_YEARS.map((ys) => {
    const y = Number(ys)
    const dataPoint: RevenueByBUChartData = {
      ano: ys,
      fopm: 0,
      renovacao: 0,
      ams: 0,
      venda_sw: 0,
      data_science: 0,
      total: 0,
    }
    for (const buKey of BU_KEYS) {
      const rows = mergedDre[buKey]
      const row = rows?.find((r) => r.ano === y)
      const rl = row?.receita_liquida
      const v = typeof rl === 'number' ? rl : 0
      dataPoint[buKey] = v
      dataPoint.total += v
    }
    return dataPoint
  })
}

/**
 * Transform DCF data for waterfall chart
 */
export function transformWaterfallData(
  dcf: SimulateResponse['dcf']
): WaterfallChartData[] {
  const data: WaterfallChartData[] = []

  // Add VP FCFFs by year
  for (const year of YEARS) {
    const vpFcff = dcf.vp_fcff_por_ano[year] || 0
    data.push({
      name: `VP FCFF ${year}`,
      value: vpFcff,
      fill: CHART_COLORS.primary,
    })
  }

  // Add terminal value
  data.push({
    name: 'VP Terminal',
    value: dcf.enterprise_value - dcf.soma_vp_fcffs,
    fill: CHART_COLORS.secondary,
  })

  // Add total (Enterprise Value)
  data.push({
    name: 'Enterprise Value',
    value: dcf.enterprise_value,
    fill: CHART_COLORS.tertiary,
  })

  return data
}

/**
 * Transform DRE data for EBITDA comparison by BU
 */
export function transformEBITDAByBUData(
  dre: Record<string, DRERow[]>
): Record<string, { ano: string; ebitda: number }[]> {
  const result: Record<string, { ano: string; ebitda: number }[]> = {}

  for (const buKey of BU_KEYS) {
    const buData = dre[buKey]
    if (buData) {
      result[buKey] = buData.map((row) => ({
        ano: String(row.ano),
        ebitda: row.ebitda,
      }))
    }
  }

  return result
}

/**
 * Get chart bar colors for BUs
 */
export function getBUColors(): Record<string, string> {
  return {
    fopm: CHART_COLORS.fopm,
    renovacao: CHART_COLORS.renovacao,
    ams: CHART_COLORS.ams,
    venda_sw: CHART_COLORS.venda_sw,
    data_science: CHART_COLORS.data_science,
  }
}
