import { useCallback, type Dispatch, type SetStateAction } from 'react'
import type { Premissas, YearKey } from '../types'

interface UsePremissasArgs {
  premissas: Premissas | null
  setPremissas: Dispatch<SetStateAction<Premissas | null>>
}

export function usePremissas({ premissas, setPremissas }: UsePremissasArgs) {
  // Macro setters
  const setInflacaoFocus = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            inflacao_focus_por_ano: {
              ...prev.inflacao_focus_por_ano,
              [year]: value,
            },
          }
        : prev
    )
  }, [])

  const setSelicFocus = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            selic_focus_por_ano: {
              ...prev.selic_focus_por_ano,
              [year]: value,
            },
          }
        : prev
    )
  }, [])


  // FOPM setters
  const setFopmHeadcount = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            fopm: {
              ...prev.fopm,
              headcount_por_ano: { ...prev.fopm.headcount_por_ano, [year]: value },
            },
          }
        : prev
    )
  }, [])

  const setFopmOciosidade = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            fopm: {
              ...prev.fopm,
              ociosidade_por_ano: { ...prev.fopm.ociosidade_por_ano, [year]: value },
            },
          }
        : prev
    )
  }, [])

  // Renovacao setters
  const setRenovacaoSpread = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            renovacao: { ...prev.renovacao, spread_real: value },
          }
        : prev
    )
  }, [])

  const setRenovacaoChurn = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            renovacao: { ...prev.renovacao, churn: value },
          }
        : prev
    )
  }, [])

  // AMS setters
  const setAmsTaxaConversao = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            ams: { ...prev.ams, taxa_conversao_fopm: value },
          }
        : prev
    )
  }, [])

  const setAmsChurn = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            ams: { ...prev.ams, churn: value },
          }
        : prev
    )
  }, [])

  // Venda Softwares setter
  const setVendaSoftwaresFator = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            venda_softwares: { fator_crescimento_real: value },
          }
        : prev
    )
  }, [])

  const setDataScienceHeadcount = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            data_science: {
              ...prev.data_science,
              headcount_por_ano: {
                ...prev.data_science.headcount_por_ano,
                [year]: value,
              },
            },
          }
        : prev
    )
  }, [])

  const setDataScienceOciosidade = useCallback((year: YearKey, value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            data_science: {
              ...prev.data_science,
              ociosidade_por_ano: {
                ...prev.data_science.ociosidade_por_ano,
                [year]: value,
              },
            },
          }
        : prev
    )
  }, [])

  // DCF setters
  const setDcfWacc = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            dcf: { ...prev.dcf, wacc: value },
          }
        : prev
    )
  }, [])

  const setDcfG = useCallback((value: number) => {
    setPremissas((prev) =>
      prev
        ? {
            ...prev,
            dcf: { ...prev.dcf, g: value },
          }
        : prev
    )
  }, [])

  return {
    premissas,
    // Macro
    setInflacaoFocus,
    setSelicFocus,
    // FOPM
    setFopmHeadcount,
    setFopmOciosidade,
    // Renovacao
    setRenovacaoSpread,
    setRenovacaoChurn,
    // AMS
    setAmsTaxaConversao,
    setAmsChurn,
    // Venda Softwares
    setVendaSoftwaresFator,
    setDataScienceHeadcount,
    setDataScienceOciosidade,
    // DCF
    setDcfWacc,
    setDcfG,
  }
}
