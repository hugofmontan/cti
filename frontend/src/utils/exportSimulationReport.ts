import type { SimulateResponse } from '../types/simulation'

export interface SimulationReportPayload {
  meta: {
    exportedAt: string
    generator: string
  }
  premissas_efetivas: SimulateResponse['premissas_efetivas']
  year_config: SimulateResponse['year_config']
  dcf: SimulateResponse['dcf']
  consolidado: SimulateResponse['consolidado']
  dre: SimulateResponse['dre']
  fluxo: SimulateResponse['fluxo']
  bp: SimulateResponse['bp']
  bp_historico: SimulateResponse['bp_historico']
  warnings: SimulateResponse['warnings']
}

export function buildSimulationReportPayload(result: SimulateResponse): SimulationReportPayload {
  return {
    meta: {
      exportedAt: new Date().toISOString(),
      generator: 'artefato-calculadora',
    },
    premissas_efetivas: result.premissas_efetivas,
    year_config: result.year_config,
    dcf: result.dcf,
    consolidado: result.consolidado,
    dre: result.dre,
    fluxo: result.fluxo,
    bp: result.bp,
    bp_historico: result.bp_historico,
    warnings: result.warnings,
  }
}

function fileNameStamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
}

/** Baixa um JSON com premissas efetivas, DCF, DRE por BU, consolidado, fluxo, BP e avisos. */
export function downloadSimulationReport(result: SimulateResponse): void {
  const payload = buildSimulationReportPayload(result)
  const text = JSON.stringify(payload, null, 2)
  const blob = new Blob([text], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `relatorio_simulacao_${fileNameStamp()}.json`
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
