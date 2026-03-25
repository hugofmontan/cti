import { useEffect, useMemo } from 'react'
import styles from './App.module.css'
import { AgentPanel } from './components/agent'
import { DashboardLayout } from './components/layout'
import {
  PremissasAMS,
  PremissasDCF,
  PremissasDataScience,
  PremissasFOPM,
  PremissasRenovacao,
  PremissasVendaSW,
} from './components/forms'
import {
  DCFWaterfallChart,
  MarginTrendChart,
  RevenueByBUChart,
  RevenueByBUPctChart,
} from './components/charts'
import {
  BUBreakdown,
  CashFlowSection,
  ConsolidatedDRE,
  MultiplesSection,
  ValuationSummary,
} from './components/sections'
import { Alert, Button, LoadingSpinner, Panel, Tabs } from './components/ui'
import { useHistoricalDRE, usePremissas, useSimulation } from './hooks'
import { AGENT_ENABLED } from './utils/constants'
import { mergeConsolidadoSeries, mergeDreByBU } from './utils/dreMerge'

export default function App() {
  const { premissas, setPremissas, result, loading, error, runSimulation } = useSimulation()
  const { historical, loading: loadingHist, error: errorHist } = useHistoricalDRE()

  const mergedConsolidado = useMemo(
    () => mergeConsolidadoSeries(historical?.consolidado, result?.consolidado),
    [historical?.consolidado, result?.consolidado],
  )

  const mergedDre = useMemo(
    () => mergeDreByBU(historical?.dre, result?.dre),
    [historical?.dre, result?.dre],
  )

  const {
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

  useEffect(() => {
    if (premissas && !result && !loading) {
      void runSimulation()
    }
  }, [premissas, result, loading, runSimulation])

  return (
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
                        </div>
                      </Panel>
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
    </DashboardLayout>
  )
}
