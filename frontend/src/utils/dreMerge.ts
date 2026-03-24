import type { DRERow } from '../types'
import { ALL_DISPLAY_YEARS, HISTORICAL_YEAR_END } from './constants'

export type DRERowMerged = Partial<DRERow> & { ano: number }

/**
 * Combina série histórica (≤ HISTORICAL_YEAR_END) com projeção da simulação (≥ 2026).
 * Para anos de projeção, prevalece sempre o resultado da API.
 */
export function mergeConsolidadoSeries(
  historical: DRERow[] | null | undefined,
  projected: DRERow[] | null | undefined,
): DRERowMerged[] {
  const histMap = new Map<number, DRERow>()
  for (const r of historical ?? []) {
    if (typeof r.ano === 'number' && r.ano <= HISTORICAL_YEAR_END) {
      histMap.set(r.ano, r)
    }
  }
  const projMap = new Map<number, DRERow>()
  for (const r of projected ?? []) {
    if (typeof r.ano === 'number') {
      projMap.set(r.ano, r)
    }
  }

  return ALL_DISPLAY_YEARS.map((ys) => {
    const y = Number(ys)
    if (y <= HISTORICAL_YEAR_END) {
      const h = histMap.get(y)
      return h ? { ...h, ano: y } : { ano: y }
    }
    const p = projMap.get(y)
    return p ? { ...p, ano: y } : { ano: y }
  })
}

/**
 * Mesmo critério por BU (chaves: fopm, renovacao, ...).
 */
export function mergeDreByBU(
  historical: Record<string, DRERow[]> | null | undefined,
  projected: Record<string, DRERow[]> | null | undefined,
): Record<string, DRERowMerged[]> {
  const keys = new Set([
    ...Object.keys(historical ?? {}),
    ...Object.keys(projected ?? {}),
  ])
  const out: Record<string, DRERowMerged[]> = {}
  for (const k of keys) {
    out[k] = mergeConsolidadoSeries(historical?.[k], projected?.[k])
  }
  return out
}
