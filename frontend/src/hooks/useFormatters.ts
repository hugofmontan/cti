import { useCallback } from 'react'
import {
  fmtBRL,
  fmtBRLFull,
  fmtPct,
  fmtNumber,
  fmtMillions,
  fmtThousands,
  getValueColorClass,
} from '../utils/formatters'

export function useFormatters() {
  const formatCurrency = useCallback((value: number) => fmtBRL(value), [])
  const formatCurrencyFull = useCallback(
    (value: number, decimals = 2) => fmtBRLFull(value, decimals),
    []
  )
  const formatPercent = useCallback(
    (value: number, decimals = 2) => fmtPct(value, decimals),
    []
  )
  const formatNumber = useCallback(
    (value: number, decimals = 0) => fmtNumber(value, decimals),
    []
  )
  const formatMillions = useCallback(
    (value: number, decimals = 1) => fmtMillions(value, decimals),
    []
  )
  const formatThousands = useCallback(
    (value: number, decimals = 0) => fmtThousands(value, decimals),
    []
  )
  const getColorClass = useCallback((value: number) => getValueColorClass(value), [])

  return {
    formatCurrency,
    formatCurrencyFull,
    formatPercent,
    formatNumber,
    formatMillions,
    formatThousands,
    getColorClass,
  }
}
