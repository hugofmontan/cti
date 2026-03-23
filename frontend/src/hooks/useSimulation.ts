import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import type { Premissas, SimulateResponse } from '../types'
import { API_BASE_URL } from '../utils/constants'

interface UseSimulationReturn {
  premissas: Premissas | null
  setPremissas: Dispatch<SetStateAction<Premissas | null>>
  result: SimulateResponse | null
  loading: boolean
  error: string | null
  runSimulation: () => Promise<void>
}

export function useSimulation(): UseSimulationReturn {
  const [premissas, setPremissas] = useState<Premissas | null>(null)
  const [result, setResult] = useState<SimulateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load defaults on mount
  useEffect(() => {
    const loadDefaults = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/defaults`)
        if (!response.ok) {
          throw new Error('Falha ao carregar defaults')
        }
        const data: Premissas = await response.json()
        setPremissas(data)
      } catch {
        setError('Nao foi possivel carregar /api/defaults. O backend esta em execucao?')
      }
    }
    loadDefaults()
  }, [])

  const runSimulation = useCallback(async () => {
    if (!premissas) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ premissas }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText)
      }

      const data: SimulateResponse = await response.json()
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro na simulacao')
    } finally {
      setLoading(false)
    }
  }, [premissas])

  return {
    premissas,
    setPremissas,
    result,
    loading,
    error,
    runSimulation,
  }
}
