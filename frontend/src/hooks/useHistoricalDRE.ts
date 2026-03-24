import { useCallback, useEffect, useState } from 'react'
import type { DRERow } from '../types'
import { API_BASE_URL } from '../utils/constants'

/** Série 2018–2030: headcounts por BU e pool histórico (rateio) — `data/historico/headcount_funcionarios_bu.csv`. */
export interface HeadcountOperacionalRow {
  ano: number
  func_fopm: number
  func_renovacao: number
  func_ams: number
  func_venda_sw: number
  func_data_science: number
  rateio_pool?: number | null
}

export interface HistoricalDREBundle {
  consolidado: DRERow[]
  dre: Record<string, DRERow[]>
  headcount_operacional_bu?: HeadcountOperacionalRow[]
  historical_year_start: number
  historical_year_end: number
  projected_year_start: number
}

interface UseHistoricalDREReturn {
  historical: HistoricalDREBundle | null
  loading: boolean
  error: string | null
  reload: () => Promise<void>
}

export function useHistoricalDRE(): UseHistoricalDREReturn {
  const [historical, setHistorical] = useState<HistoricalDREBundle | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/historical-dre`)
      if (!res.ok) {
        throw new Error(await res.text())
      }
      const data = (await res.json()) as HistoricalDREBundle
      setHistorical(data)
    } catch {
      setError('Nao foi possivel carregar /api/historical-dre.')
      setHistorical(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  return { historical, loading, error, reload }
}
