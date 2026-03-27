import type { DRERow, FluxoRow, SimulateResponse } from '../types'
import { BU_KEYS, CHART_COLORS } from './constants'
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

/**
 * Transform DRE data for stacked revenue by BU (%) chart.
 *
 * Os valores aqui são compartilhamento em decimal (0..1), somando ~1 por ano.
 * Isso permite que o `fmtPct` funcione diretamente para exibição (valor decimal).
 */
export interface RevenueByBUPctChartData {
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
  dre: Record<string, DRERow[]>,
  projectedYears: number[],
): RevenueByBUChartData[] {
  const result: RevenueByBUChartData[] = []

  for (const yearNum of projectedYears) {
    const dataPoint: RevenueByBUChartData = {
      ano: String(yearNum),
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
 * Receita líquida por BU em % (participação) — valores em decimal (0..1).
 */
export function transformRevenueByBUPctData(
  dre: Record<string, DRERow[]>,
  projectedYears: number[],
): RevenueByBUPctChartData[] {
  const result: RevenueByBUPctChartData[] = []

  for (const yearNum of projectedYears) {
    const rlByBu: Record<string, number> = {
      fopm: 0,
      renovacao: 0,
      ams: 0,
      venda_sw: 0,
      data_science: 0,
    }

    let total = 0

    for (const buKey of BU_KEYS) {
      const buData = dre[buKey]
      if (buData) {
        const yearRow = buData.find((row) => row.ano === yearNum)
        const rl = yearRow?.receita_liquida
        const v = typeof rl === 'number' ? rl : 0
        rlByBu[buKey] = v
        total += v
      }
    }

    const denom = total
    const share = (v: number) => (denom === 0 ? 0 : v / denom)

    const dataPoint: RevenueByBUPctChartData = {
      ano: String(yearNum),
      fopm: share(rlByBu.fopm),
      renovacao: share(rlByBu.renovacao),
      ams: share(rlByBu.ams),
      venda_sw: share(rlByBu.venda_sw),
      data_science: share(rlByBu.data_science),
      total: denom === 0 ? 0 : 1,
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
  opts: { historicalYearEnd: number },
): MarginTrendSplitData[] {
  return consolidado.map((row) => {
    const rl = row.receita_liquida
    const e = _pctLine(row.ebitda, rl)
    const eb = _pctLine(row.ebit, rl)
    const ll = _pctLine(row.lucro_liquido, rl)
    const isHist = row.ano <= opts.historicalYearEnd
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
  allDisplayYears: number[],
): RevenueByBUChartData[] {
  return allDisplayYears.map((y) => {
    const dataPoint: RevenueByBUChartData = {
      ano: String(y),
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
 * Receita líquida por BU em % (participação) — valores em decimal (0..1).
 */
export function transformRevenueByBUPctDataMerged(
  mergedDre: Record<string, DRERowMerged[]>,
  allDisplayYears: number[],
): RevenueByBUPctChartData[] {
  return allDisplayYears.map((y) => {
    const rlByBu: Record<string, number> = {
      fopm: 0,
      renovacao: 0,
      ams: 0,
      venda_sw: 0,
      data_science: 0,
    }

    let total = 0

    for (const buKey of BU_KEYS) {
      const rows = mergedDre[buKey]
      const row = rows?.find((r) => r.ano === y)
      const rl = row?.receita_liquida
      const v = typeof rl === 'number' ? rl : 0
      rlByBu[buKey] = v
      total += v
    }

    const denom = total
    const share = (v: number) => (denom === 0 ? 0 : v / denom)

    return {
      ano: String(y),
      fopm: share(rlByBu.fopm),
      renovacao: share(rlByBu.renovacao),
      ams: share(rlByBu.ams),
      venda_sw: share(rlByBu.venda_sw),
      data_science: share(rlByBu.data_science),
      total: denom === 0 ? 0 : 1,
    }
  })
}

/**
 * Transform DCF data for waterfall chart
 */
export function transformWaterfallData(
  dcf: SimulateResponse['dcf'],
  projectedYears: number[],
): WaterfallChartData[] {
  const data: WaterfallChartData[] = []

  // Add VP FCFFs by year
  for (const year of projectedYears) {
    const yearKey = String(year)
    const vpFcff = dcf.vp_fcff_por_ano[yearKey] || 0
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
