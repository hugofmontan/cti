import type { BPRow, DRERow } from '../types'

export type DRERowMerged = Partial<DRERow> & { ano: number }

/**
 * Combina série histórica (≤ historicalYearEnd) com projeção da simulação.
 * Para anos de projeção, prevalece sempre o resultado da API.
 */
export function mergeConsolidadoSeries(
  historical: DRERow[] | null | undefined,
  projected: DRERow[] | null | undefined,
  opts: { historicalYearEnd: number; allDisplayYears: number[] },
): DRERowMerged[] {
  const histMap = new Map<number, DRERow>()
  for (const r of historical ?? []) {
    if (typeof r.ano === 'number' && r.ano <= opts.historicalYearEnd) {
      histMap.set(r.ano, r)
    }
  }
  const projMap = new Map<number, DRERow>()
  for (const r of projected ?? []) {
    if (typeof r.ano === 'number') {
      projMap.set(r.ano, r)
    }
  }

  return opts.allDisplayYears.map((y) => {
    if (y <= opts.historicalYearEnd) {
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
  opts: { historicalYearEnd: number; allDisplayYears: number[] },
): Record<string, DRERowMerged[]> {
  const keys = new Set([
    ...Object.keys(historical ?? {}),
    ...Object.keys(projected ?? {}),
  ])
  const out: Record<string, DRERowMerged[]> = {}
  for (const k of keys) {
    out[k] = mergeConsolidadoSeries(historical?.[k], projected?.[k], opts)
  }
  return out
}

export type BPRowMerged = Partial<BPRow> & { ano: number }

export function mergeBpSeries(
  historical: BPRow[] | null | undefined,
  projected: BPRow[] | null | undefined,
  opts: { historicalYearEnd: number; allDisplayYears: number[] },
): BPRowMerged[] {
  const histMap = new Map<number, BPRow>()
  for (const r of historical ?? []) {
    if (typeof r.ano === 'number' && r.ano <= opts.historicalYearEnd) {
      histMap.set(r.ano, r)
    }
  }
  const projMap = new Map<number, BPRow>()
  for (const r of projected ?? []) {
    if (typeof r.ano === 'number') {
      projMap.set(r.ano, r)
    }
  }

  return opts.allDisplayYears.map((y) => {
    if (y <= opts.historicalYearEnd) {
      const h = histMap.get(y)
      return h ? { ...h, ano: y } : { ano: y }
    }
    const p = projMap.get(y)
    return p ? { ...p, ano: y } : { ano: y }
  })
}
