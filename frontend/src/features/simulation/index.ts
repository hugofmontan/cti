/**
 * Feature simulation: premissas, hooks e visualização do motor.
 * Implementações permanecem em `components/` e `hooks/`; este barrel expõe a API pública da feature.
 */
export {
  PremissasAMS,
  PremissasDCF,
  PremissasDataScience,
  PremissasFOPM,
  PremissasMacro,
  PremissasRenovacao,
  PremissasVendaSW,
} from '../../components/forms'
export {
  DCFWaterfallChart,
  MarginTrendChart,
  RevenueByBUChart,
  RevenueByBUPctChart,
} from '../../components/charts'
export {
  BUBreakdown,
  BalanceSheetSection,
  CashFlowSection,
  ConsolidatedDRE,
  MultiplesSection,
  UploadHistoricalPanel,
  ValuationSummary,
} from '../../components/sections'
export { useHistoricalDRE, usePremissas, useSimulation } from '../../hooks'
