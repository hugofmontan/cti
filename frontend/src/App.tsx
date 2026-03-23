import { useEffect } from 'react'
import styles from './App.module.css'
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
} from './components/charts'
import {
  BUBreakdown,
  CashFlowSection,
  ConsolidatedDRE,
  MultiplesSection,
  ValuationSummary,
} from './components/sections'
import { Alert, Button, LoadingSpinner, Panel } from './components/ui'
import { usePremissas, useSimulation } from './hooks'

export default function App() {
  const { premissas, setPremissas, result, loading, error, runSimulation } = useSimulation()

  const {
    setAmsChurn,
    setAmsTaxaConversao,
    setDataScienceProjetos,
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

      {!premissas ? (
        <LoadingSpinner size="lg" />
      ) : (
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
                  onProjetosChange={setDataScienceProjetos}
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
                  <RevenueByBUChart dre={result.dre} />
                  <MarginTrendChart consolidado={result.consolidado} />
                  <DCFWaterfallChart dcf={result.dcf} />
                </>
              ) : (
                <Alert variant="info">Clique em recalcular para carregar os resultados.</Alert>
              )}
            </div>
          </div>

          {result ? (
            <>
              <ConsolidatedDRE consolidado={result.consolidado} />
              <CashFlowSection fluxo={result.fluxo} />
              <MultiplesSection dcf={result.dcf} />
              <BUBreakdown dre={result.dre} />
              {result.warnings?.map((w) => (
                <Alert key={w} variant="warning">
                  {w}
                </Alert>
              ))}
            </>
          ) : null}
        </>
      )}
    </DashboardLayout>
  )
}
