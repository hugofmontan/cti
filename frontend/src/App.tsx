import { useEffect, useMemo, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import styles from './App.module.css'
import { AgentPanel } from './features/agent'
import { DashboardLayout } from './shared/layout'
import {
  BUBreakdown,
  BalanceSheetSection,
  CashFlowSection,
  ConsolidatedDRE,
  DCFWaterfallChart,
  MarginTrendChart,
  MultiplesSection,
  PremissasAMS,
  PremissasDCF,
  PremissasDataScience,
  PremissasFOPM,
  PremissasMacro,
  PremissasRenovacao,
  PremissasVendaSW,
  RevenueByBUChart,
  RevenueByBUPctChart,
  UploadHistoricalPanel,
  useHistoricalDRE,
  usePremissas,
  useSimulation,
  ValuationSummary,
} from './features/simulation'
import { Alert, Button, LoadingSpinner, Panel, Tabs } from './shared/ui'
import { AGENT_ENABLED, HISTORICAL_YEARS, HISTORICAL_YEAR_END, YEARS } from './utils/constants'
import { mergeBpSeries, mergeConsolidadoSeries, mergeDreByBU } from './utils/dreMerge'
import { SimulationPdfReport } from './features/report'
import { downloadSimulationReport } from './utils/exportSimulationReport'
import { downloadSimulationPdf } from './utils/exportSimulationPdf'
import { YearConfigProvider, type YearConfig } from './shared/contexts'

export default function App() {
  const { premissas, setPremissas, result, loading, error, runSimulation } = useSimulation()
  const { historical, loading: loadingHist, error: errorHist, reload: reloadHistorical } = useHistoricalDRE()

  const yearConfig: YearConfig = useMemo(() => {
    const histYStart = historical?.historical_year_start
    const histYEnd = historical?.historical_year_end

    const simYc = result?.year_config
    const effectiveHistStart =
      histYStart ?? simYc?.historical_year_start ?? Number(HISTORICAL_YEARS[0])
    const effectiveHistEnd = histYEnd ?? simYc?.historical_year_end ?? HISTORICAL_YEAR_END

    const projectedYears =
      historical?.projected_years ??
      simYc?.projected_years ??
      YEARS.map((y) => Number(y))

    const historicalYears: number[] = []
    for (let y = effectiveHistStart; y <= effectiveHistEnd; y++) historicalYears.push(y)

    const projectedYearStart = projectedYears[0]
    const allDisplayYears = [...historicalYears, ...projectedYears]

    return {
      historicalYearStart: effectiveHistStart,
      historicalYearEnd: effectiveHistEnd,
      projectedYears,
      projectedYearStart,
      allDisplayYears,
      historicalYears,
    }
  }, [historical, result])

  const mergedConsolidado = useMemo(
    () =>
      mergeConsolidadoSeries(historical?.consolidado, result?.consolidado, {
        historicalYearEnd: yearConfig.historicalYearEnd,
        allDisplayYears: yearConfig.allDisplayYears,
      }),
    [historical?.consolidado, result?.consolidado, yearConfig.historicalYearEnd, yearConfig.allDisplayYears],
  )

  const mergedDre = useMemo(
    () =>
      mergeDreByBU(historical?.dre, result?.dre, {
        historicalYearEnd: yearConfig.historicalYearEnd,
        allDisplayYears: yearConfig.allDisplayYears,
      }),
    [historical?.dre, result?.dre, yearConfig.historicalYearEnd, yearConfig.allDisplayYears],
  )
  const mergedBp = useMemo(
    () =>
      mergeBpSeries(historical?.bp, result?.bp, {
        historicalYearEnd: yearConfig.historicalYearEnd,
        allDisplayYears: yearConfig.allDisplayYears,
      }),
    [historical?.bp, result?.bp, yearConfig.historicalYearEnd, yearConfig.allDisplayYears],
  )

  const {
    setInflacaoFocus,
    setSelicFocus,
    setAmsChurn,
    setAmsTaxaConversao,
    setDataScienceHeadcount,
    setDataScienceOciosidade,
    setDcfG,
    setDcfWacc,
    setFopmHeadcount,
    setFopmOciosidade,
    setRenovacaoChurn,
    setRenovacaoSpread,
    setVendaSoftwaresFator,
  } = usePremissas({ premissas, setPremissas })

  const pdfReportRef = useRef<HTMLDivElement>(null)
  const [pdfGeneratedAtLabel, setPdfGeneratedAtLabel] = useState('')
  const [pdfBusy, setPdfBusy] = useState(false)

  const handleExportPdf = async () => {
    if (!result) return
    flushSync(() => {
      setPdfGeneratedAtLabel(
        `Gerado em ${new Date().toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}`,
      )
    })
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
    })
    const el = pdfReportRef.current
    if (!el) return
    setPdfBusy(true)
    try {
      await downloadSimulationPdf(el)
    } finally {
      setPdfBusy(false)
    }
  }

  useEffect(() => {
    if (premissas && !result && !loading) {
      void runSimulation()
    }
  }, [premissas, result, loading, runSimulation])

  return (
    <YearConfigProvider value={yearConfig}>
      <DashboardLayout>
      <p className={styles.intro}>
        Ajuste premissas por BU, recalcule e acompanhe impacto no consolidado e no DCF.
      </p>

      {error ? (
        <Alert variant="error" title="Falha de integração">
          {error}
        </Alert>
      ) : null}

      {errorHist ? (
        <Alert variant="warning" title="Histórico">
          {errorHist} Exibindo apenas projeção.
        </Alert>
      ) : null}

      {!premissas ? <LoadingSpinner size="lg" /> : (
        <Tabs
          tabs={[
            {
              id: 'dashboard',
              label: 'Dashboard',
              content: (
                <>
                  <div className={styles.mainGrid}>
                    <div className={styles.premissasPanel}>
                      <Panel title="Premissas" collapsible={false}>
                        <PremissasMacro
                          premissas={premissas}
                          onInflacaoChange={setInflacaoFocus}
                          onSelicChange={setSelicFocus}
                        />
                        <PremissasFOPM
                          premissas={premissas}
                          onHeadcountChange={setFopmHeadcount}
                          onOciosidadeChange={setFopmOciosidade}
                        />
                        <PremissasRenovacao
                          premissas={premissas}
                          onSpreadChange={setRenovacaoSpread}
                          onChurnChange={setRenovacaoChurn}
                        />
                        <PremissasAMS
                          premissas={premissas}
                          onTaxaConversaoChange={setAmsTaxaConversao}
                          onChurnChange={setAmsChurn}
                        />
                        <PremissasVendaSW premissas={premissas} onFatorChange={setVendaSoftwaresFator} />
                        <PremissasDataScience
                          premissas={premissas}
                          onHeadcountChange={setDataScienceHeadcount}
                          onOciosidadeChange={setDataScienceOciosidade}
                        />
                        <PremissasDCF premissas={premissas} onWaccChange={setDcfWacc} onGChange={setDcfG} />
                        <div className={styles.actions}>
                          <Button variant="primary" loading={loading} onClick={() => void runSimulation()}>
                            Recalcular
                          </Button>
                          {result ? (
                            <>
                              <Button
                                type="button"
                                variant="secondary"
                                disabled={loading || pdfBusy}
                                loading={pdfBusy}
                                onClick={() => void handleExportPdf()}
                                title="Gera PDF com valuation, múltiplos, gráficos DCF, receita, margem e FCFF"
                              >
                                Exportar PDF
                              </Button>
                              <Button
                                type="button"
                                variant="ghost"
                                disabled={loading || pdfBusy}
                                onClick={() => downloadSimulationReport(result)}
                                title="Baixa JSON estruturado da última simulação"
                              >
                                Dados JSON
                              </Button>
                            </>
                          ) : null}
                        </div>
                      </Panel>

                      <UploadHistoricalPanel
                        historical={historical}
                        loadingHistorical={loadingHist}
                        loadingSimulation={loading}
                        onReloadHistorical={() => reloadHistorical()}
                        onRunSimulation={() => runSimulation()}
                      />
                    </div>

                    <div className={styles.chartsGrid}>
                      {result ? (
                        <>
                          <ValuationSummary dcf={result.dcf} />
                          <MultiplesSection dcf={result.dcf} />
                          <DCFWaterfallChart dcf={result.dcf} />
                          <RevenueByBUChart dre={result.dre} mergedDre={mergedDre} />
                          <RevenueByBUPctChart dre={result.dre} mergedDre={mergedDre} />
                          <MarginTrendChart consolidado={mergedConsolidado} />
                        </>
                      ) : (
                        <>
                          {!loadingHist && historical ? (
                            <>
                              <RevenueByBUChart dre={{}} mergedDre={mergedDre} />
                              <RevenueByBUPctChart dre={{}} mergedDre={mergedDre} />
                              <MarginTrendChart consolidado={mergedConsolidado} />
                            </>
                          ) : null}
                          <Alert variant="info">
                            Clique em Recalcular para carregar DCF e a projeção 2026–2030. Os gráficos acima
                            mostram o histórico de <code>data/original</code> quando disponível.
                          </Alert>
                        </>
                      )}
                    </div>
                  </div>

                  {historical || result ? (
                    <>
                      <ConsolidatedDRE consolidado={mergedConsolidado} />
                      <BalanceSheetSection bp={mergedBp} />
                      {result ? <CashFlowSection fluxo={result.fluxo} /> : null}
                      <BUBreakdown dre={mergedDre} />
                      {result?.warnings?.map((w) => (
                        <Alert key={w} variant="warning">
                          {w}
                        </Alert>
                      ))}
                    </>
                  ) : null}
                </>
              ),
            },
            ...(AGENT_ENABLED
              ? [
                  {
                    id: 'analista-ia',
                    label: 'Analista IA',
                    content: <AgentPanel premissas={premissas} />,
                  },
                ]
              : []),
          ]}
        />
      )}

      {result ? (
        <div className={styles.pdfCaptureHost} aria-hidden>
          <SimulationPdfReport
            ref={pdfReportRef}
            result={result}
            mergedDre={mergedDre}
            mergedConsolidado={mergedConsolidado}
            generatedAtLabel={pdfGeneratedAtLabel}
          />
        </div>
      ) : null}
      </DashboardLayout>
    </YearConfigProvider>
  )
}
