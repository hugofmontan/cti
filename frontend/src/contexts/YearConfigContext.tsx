import { createContext, useContext, type ReactNode } from 'react'

import { HISTORICAL_YEAR_END, HISTORICAL_YEARS, YEARS } from '../utils/constants'

export type YearConfig = {
  historicalYearStart: number
  historicalYearEnd: number
  projectedYears: number[]
  projectedYearStart: number
  allDisplayYears: number[]
  historicalYears: number[]
}

const fallbackHistoricalYearStart = HISTORICAL_YEARS[0] ? Number(HISTORICAL_YEARS[0]) : 2018
const fallbackProjectedYears = YEARS.map((y) => Number(y))

const fallback: YearConfig = {
  historicalYearStart: fallbackHistoricalYearStart,
  historicalYearEnd: HISTORICAL_YEAR_END,
  projectedYears: fallbackProjectedYears,
  projectedYearStart: fallbackProjectedYears[0],
  allDisplayYears: [...HISTORICAL_YEARS.map((y) => Number(y)), ...fallbackProjectedYears],
  historicalYears: HISTORICAL_YEARS.map((y) => Number(y)),
}

export const YearConfigContext = createContext<YearConfig>(fallback)

export function YearConfigProvider({ value, children }: { value: YearConfig; children: ReactNode }) {
  return <YearConfigContext.Provider value={value}>{children}</YearConfigContext.Provider>
}

export function useYearConfig() {
  return useContext(YearConfigContext)
}

