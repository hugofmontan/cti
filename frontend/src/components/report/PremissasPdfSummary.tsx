import type { Premissas, YearKey } from '../../types'
import { fmtNumber, fmtPct } from '../../utils/formatters'
import styles from './PremissasPdfSummary.module.css'

interface PremissasPdfSummaryProps {
  premissas: Premissas
}

function sortedYearKeysUnion(...records: Array<Record<YearKey, number>>): YearKey[] {
  const set = new Set<string>()
  for (const r of records) {
    for (const k of Object.keys(r)) set.add(k)
  }
  return [...set].sort((x, y) => Number(x) - Number(y)) as YearKey[]
}

export function PremissasPdfSummary({ premissas }: PremissasPdfSummaryProps) {
  const macroYears = sortedYearKeysUnion(
    premissas.inflacao_focus_por_ano,
    premissas.selic_focus_por_ano,
  )
  const projYears = sortedYearKeysUnion(
    premissas.fopm.headcount_por_ano,
    premissas.data_science.headcount_por_ano,
  )

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Premissas empregadas</h2>
      <p className={styles.lead}>
        Valores efetivos enviados ao motor na última simulação (espelho das premissas ativas).
      </p>

      <h3 className={styles.subtitle}>Macro</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Ano</th>
              <th>Inflação focus</th>
              <th>Selic focus</th>
            </tr>
          </thead>
          <tbody>
            {macroYears.map((y) => (
              <tr key={y}>
                <td>{y}</td>
                <td>{fmtPct(premissas.inflacao_focus_por_ano[y] ?? 0)}</td>
                <td>{fmtPct(premissas.selic_focus_por_ano[y] ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className={styles.subtitle}>DCF</h3>
      <ul className={styles.kvList}>
        <li>
          <span>WACC</span>
          <strong>{fmtPct(premissas.dcf.wacc)}</strong>
        </li>
        <li>
          <span>g (perpetuidade)</span>
          <strong>{fmtPct(premissas.dcf.g)}</strong>
        </li>
      </ul>

      <h3 className={styles.subtitle}>Renovação</h3>
      <ul className={styles.kvList}>
        <li>
          <span>Spread real</span>
          <strong>{fmtPct(premissas.renovacao.spread_real)}</strong>
        </li>
        <li>
          <span>Churn anual</span>
          <strong>{fmtPct(premissas.renovacao.churn)}</strong>
        </li>
      </ul>

      <h3 className={styles.subtitle}>AMS</h3>
      <ul className={styles.kvList}>
        <li>
          <span>Taxa de conversão FOPM</span>
          <strong>{fmtPct(premissas.ams.taxa_conversao_fopm)}</strong>
        </li>
        <li>
          <span>Churn</span>
          <strong>{fmtPct(premissas.ams.churn)}</strong>
        </li>
      </ul>

      <h3 className={styles.subtitle}>Venda de softwares</h3>
      <ul className={styles.kvList}>
        <li>
          <span>Fator de crescimento real</span>
          <strong>{fmtPct(premissas.venda_softwares.fator_crescimento_real)}</strong>
        </li>
      </ul>

      <h3 className={styles.subtitle}>FOPM</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Ano</th>
              <th>Headcount</th>
              <th>Ociosidade</th>
            </tr>
          </thead>
          <tbody>
            {projYears.map((y) => (
              <tr key={`fopm-${y}`}>
                <td>{y}</td>
                <td>{fmtNumber(premissas.fopm.headcount_por_ano[y] ?? 0, 0)}</td>
                <td>{fmtPct(premissas.fopm.ociosidade_por_ano[y] ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className={styles.subtitle}>Data Science</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Ano</th>
              <th>Headcount</th>
              <th>Ociosidade</th>
            </tr>
          </thead>
          <tbody>
            {projYears.map((y) => (
              <tr key={`ds-${y}`}>
                <td>{y}</td>
                <td>{fmtNumber(premissas.data_science.headcount_por_ano[y] ?? 0, 0)}</td>
                <td>{fmtPct(premissas.data_science.ociosidade_por_ano[y] ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
