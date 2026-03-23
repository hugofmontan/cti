import type { DRERow, FluxoRow, SimulateResponse } from '../types'
import { BU_KEYS, CHART_COLORS, YEARS } from './constants'

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

/**
 * Transform consolidado data for margin trend line chart
 */
export function transformMarginTrendData(
  consolidado: DRERow[]
): MarginTrendChartData[] {
  return consolidado.map((row) => ({
    ano: String(row.ano),
    ebitda_pct: ((row.ebitda / row.receita_liquida) * 100) || 0,
    ebit_pct: ((row.ebit / row.receita_liquida) * 100) || 0,
    ll_pct: ((row.lucro_liquido / row.receita_liquida) * 100) || 0,
  }))
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
