import { useCallback, useId } from 'react'
import styles from './CsvUploadGuide.module.css'

const SECTION_IDS = {
  geral: 'csv-guide-geral',
  formato: 'csv-guide-formato',
  validacao: 'csv-guide-validacao',
  arquivos: 'csv-guide-arquivos',
  headcount: 'csv-guide-headcount',
  consistencia: 'csv-guide-consistencia',
  balanco: 'csv-guide-balanco',
  exemplo: 'csv-guide-exemplo',
  checklist: 'csv-guide-checklist',
} as const

const NAV_ITEMS: Array<{ id: string; label: string }> = [
  { id: SECTION_IDS.geral, label: 'Visão geral' },
  { id: SECTION_IDS.formato, label: 'Formato pivot' },
  { id: SECTION_IDS.validacao, label: 'Linhas obrigatórias' },
  { id: SECTION_IDS.arquivos, label: 'Arquivos e campo HTTP' },
  { id: SECTION_IDS.headcount, label: 'Headcount (BUs)' },
  { id: SECTION_IDS.consistencia, label: 'Anos e consistência' },
  { id: SECTION_IDS.balanco, label: 'Balanço opcional' },
  { id: SECTION_IDS.exemplo, label: 'Exemplo mínimo' },
  { id: SECTION_IDS.checklist, label: 'Checklist' },
]

const EXAMPLE_DRE_SNIPPET = `linha,2023,2024,2025
FATURAMENTO BRUTO,40812311.14,45743848.97,49188443.09
RECEITA LÍQUIDA,33952526.86,38292104.29,41280034.60
GASTOS COM PESSOAL,11294791.43,11380425.62,12531389.43
EBITDA,8738292.07,10123456.78,11234567.89
EBIT,8234567.12,9654321.09,10456723.45
LUCRO LÍQUIDO,5123456.78,6234567.89,7012345.67`

const EXAMPLE_BU_SNIPPET = `linha,2024,2025
FATURAMENTO BRUTO,24571136.45,22787020.44
RECEITA LÍQUIDA,20315716.51,18817533.41
GASTOS COM PESSOAL,5938797.23,6800730.59
EBITDA,4500123.45,5100987.65
EBIT,4200111.22,4800555.33
LUCRO LÍQUIDO,3100999.11,3550777.22
# Funcionários - Média,45.667,45.333`

const EXAMPLE_BP_SNIPPET = `categoria,conta,tipo,2024,2025
Ativo Circulante,Caixa e Equivalentes de Caixa,item,5200000,2291962
Total do Ativo,Total do Ativo,total,15581000,10855036`

export function CsvUploadGuide() {
  const navLabelId = useId()

  const go = useCallback((sectionId: string) => {
    const el = document.getElementById(sectionId)
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    el?.focus?.()
  }, [])

  return (
    <div className={styles.wrap}>
      <h3 className={styles.heading}>Guia do formato CSV</h3>
      <p className={styles.subheading}>
        Referência alinhada ao endpoint <code>POST /api/upload-historical</code>. Use a navegação à esquerda para pular
        direto ao tópico; o texto à direita traz regras, tabelas e exemplos copiáveis.
      </p>

      <div className={styles.layout}>
        <nav className={styles.nav} aria-labelledby={navLabelId}>
          <p id={navLabelId} className={styles.navTitle}>
            Nesta página
          </p>
          {NAV_ITEMS.map(({ id, label }) => (
            <button key={id} type="button" className={styles.navBtn} onClick={() => go(id)}>
              {label}
            </button>
          ))}
        </nav>

        <div className={styles.content}>
          <section id={SECTION_IDS.geral} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Visão geral</h4>
            <p className={styles.sectionText}>
              Você envia <strong>sete CSVs obrigatórios</strong> em um único formulário. Cada arquivo substitui a base
              ativa em <code>data/uploads/active/</code> e dispara novo cálculo do histórico + simulação. O oitavo
              arquivo (<strong>balanço patrimonial</strong>) é opcional.
            </p>
            <ul className={styles.list}>
              <li>
                Codificação recomendada: <code>UTF-8</code> (evita caracteres quebrados em rótulos como{' '}
                <code>RECEITA LÍQUIDA</code>).
              </li>
              <li>
                Separador: vírgula (<code>,</code>), padrão CSV. Valores numéricos podem usar ponto como decimal.
              </li>
              <li>O backend recusa arquivo vazio, CSV sem colunas de ano numérico ou anos finais diferentes entre os sete obrigatórios.</li>
            </ul>
          </section>

          <section id={SECTION_IDS.formato} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Formato pivot (DRE)</h4>
            <p className={styles.sectionText}>
              Cada CSV de DRE é uma tabela <strong>larga</strong>: uma coluna de rótulos e uma coluna por ano.
            </p>
            <ul className={styles.list}>
              <li>
                <strong>Primeira coluna</strong> deve chamar-se exatamente <code>linha</code> (minúsculo). Cada célula é o
                nome da conta / indicador (ex.: <code>FATURAMENTO BRUTO</code>).
              </li>
              <li>
                <strong>Demais colunas</strong> são anos inteiros no cabeçalho: <code>2018</code>, <code>2019</code>, … até
                o último ano que você quiser exibir (muitos arquivos trazem também <code>2026</code>–<code>2030</code> para
                placeholder; isso é aceito desde que a validação de “último ano com número” fique consistente — ver abaixo).
              </li>
              <li>
                Células sem dado podem ficar vazias ou com <code>-</code>; o motor ignora linhas que não precisa. O
                importante é existir <strong>pelo menos um valor numérico</strong> na coluna de um ano para que esse ano
                seja considerado na detecção do fim do histórico.
              </li>
            </ul>
            <div className={styles.callout}>
              Dica: abra um CSV de referência em <code>data/original/</code> no repositório — a estrutura dos gabaritos
              oficiais segue exatamente esse pivot.
            </div>
          </section>

          <section id={SECTION_IDS.validacao} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Linhas obrigatórias (todos os DREs)</h4>
            <p className={styles.sectionText}>
              Antes de validar, o backend <strong>normaliza</strong> rótulos: remove espaços extras e converte para
              maiúsculas. Use os nomes abaixo (acentos incluídos onde indicado) para não correr risco de rejeição.
            </p>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Rótulo em linha</th>
                    <th>Notas</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <code>FATURAMENTO BRUTO</code>
                    </td>
                    <td>Também aceito como receita bruta da BU / consolidado.</td>
                  </tr>
                  <tr>
                    <td>
                      <code>RECEITA LÍQUIDA</code>
                    </td>
                    <td>Base para margens e drivers em várias BUs.</td>
                  </tr>
                  <tr>
                    <td>
                      <code>GASTOS COM PESSOAL</code>
                    </td>
                    <td>Prefira a forma completa “COM”; abreviações heterogêneas podem falhar na checagem.</td>
                  </tr>
                  <tr>
                    <td>
                      <code>EBITDA</code>
                    </td>
                    <td>—</td>
                  </tr>
                  <tr>
                    <td>
                      <code>EBIT</code>
                    </td>
                    <td>—</td>
                  </tr>
                  <tr>
                    <td>
                      <code>LUCRO LÍQUIDO</code>
                    </td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section id={SECTION_IDS.arquivos} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Arquivos e campo no formulário</h4>
            <p className={styles.sectionText}>
              Os nomes abaixo são os <code>name</code> dos campos no <code>multipart/form-data</code> (é isso que o front
              envia ao escolher cada arquivo).
            </p>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tela</th>
                    <th>Campo HTTP</th>
                    <th>Grava como (pasta ativa)</th>
                    <th>Headcount obrigatório?</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Consolidado</td>
                    <td>
                      <code>consolidado</code>
                    </td>
                    <td>
                      <code>consolidado_original.csv</code>
                    </td>
                    <td>Não</td>
                  </tr>
                  <tr>
                    <td>FOPM</td>
                    <td>
                      <code>fopm</code>
                    </td>
                    <td>
                      <code>dre_fopm_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>Renovacao</td>
                    <td>
                      <code>renovacao</code>
                    </td>
                    <td>
                      <code>dre_renovacao_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>AMS</td>
                    <td>
                      <code>ams</code>
                    </td>
                    <td>
                      <code>dre_ams_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>Venda SW</td>
                    <td>
                      <code>venda_sw</code>
                    </td>
                    <td>
                      <code>dre_venda_softwares_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>Data Science</td>
                    <td>
                      <code>data_science</code>
                    </td>
                    <td>
                      <code>dre_data_science_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>Administrativa</td>
                    <td>
                      <code>administrativa</code>
                    </td>
                    <td>
                      <code>dre_administrativa_original.csv</code>
                    </td>
                    <td>Sim</td>
                  </tr>
                  <tr>
                    <td>Balanço (opcional)</td>
                    <td>
                      <code>balanco_patrimonial</code>
                    </td>
                    <td>
                      <code>balanco_patrimonial.csv</code>
                    </td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section id={SECTION_IDS.headcount} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Headcount nas BUs</h4>
            <p className={styles.sectionText}>
              Para todo arquivo que <strong>não</strong> é o consolidado, é obrigatório existir <strong>ao menos uma
              linha</strong> de headcount com um destes rótulos (após normalização):
            </p>
            <ul className={styles.list}>
              <li>
                <code># Funcionários - Média</code>
              </li>
              <li>
                <code>N.º Funcionários</code>
              </li>
              <li>
                <code>N.º Funcionários (premissa)</code>
              </li>
            </ul>
            <p className={styles.sectionText}>
              A linha se comporta como as outras: mesmas colunas de ano, valores numéricos (média de FTE, nº absoluto de
              colaboradores, etc.). A coluna <code>linha</code> precisa usar um dos três rótulos acima — inclusive na BU
              Administrativa — para o upload ser aceito.
            </p>
            <div className={`${styles.callout} ${styles.calloutWarn}`}>
              Sem uma dessas três linhas, o erro típico é:{' '}
              <em>CSV BU faltando linha de headcount (&apos;# Funcionários - Média&apos; ou equivalente).</em>
            </div>
          </section>

          <section id={SECTION_IDS.consistencia} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Anos e consistência entre arquivos</h4>
            <p className={styles.sectionText}>
              Para cada CSV, o backend calcula o <strong>último ano</strong> cuja coluna numérica tem ao menos um valor
              válido. Esse valor precisa ser <strong>idêntico nos sete arquivos obrigatórios</strong>; caso contrário o
              servidor retorna algo como <em>Anos finais inconsistentes entre arquivos</em>.
            </p>
            <ul className={styles.list}>
              <li>Se você estendeu histórico até 2026 em um CSV, todos os outros também precisam ter coluna 2026 populada até o mesmo “fim lógico”.</li>
              <li>O primeiro ano é inferido a partir da menor coluna numérica (ex.: 2018).</li>
              <li>Os cinco anos seguintes ao término do histórico viram horizonte de projeção na calculadora.</li>
            </ul>
          </section>

          <section id={SECTION_IDS.balanco} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Balanço patrimonial (opcional)</h4>
            <p className={styles.sectionText}>
              Formato diferente do DRE: linhas em modo “longo” com metadados + anos. Colunas fixas (nomes exatos):
            </p>
            <ul className={styles.list}>
              <li>
                <code>categoria</code> — ex.: <code>Ativo Circulante</code>
              </li>
              <li>
                <code>conta</code> — nome da linha contábil
              </li>
              <li>
                <code>tipo</code> — valores como <code>item</code>, <code>subtotal</code>, <code>total</code>
              </li>
              <li>Demais colunas: anos numéricos (<code>2021</code>, <code>2022</code>, …) com saldos.</li>
            </ul>
            <pre className={styles.pre} role="region" aria-label="Exemplo de cabeçalho e linhas de balanço">
              {EXAMPLE_BP_SNIPPET}
            </pre>
          </section>

          <section id={SECTION_IDS.exemplo} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Exemplos mínimos (ilustrativos)</h4>
            <p className={styles.sectionText}>
              Trechos enxutos só para entender o <strong>desenho</strong> das colunas; números são fictícios. O consolidado
              precisa das seis linhas obrigatórias; cada BU precisa das seis + headcount.
            </p>
            <p className={styles.sectionText}>
              <strong>Consolidado (trecho)</strong>
            </p>
            <pre className={styles.pre} role="region" aria-label="Exemplo CSV consolidado">{EXAMPLE_DRE_SNIPPET}</pre>
            <p className={styles.sectionText}>
              <strong>BU (trecho — note a última linha)</strong>
            </p>
            <pre className={styles.pre} role="region" aria-label="Exemplo CSV BU com headcount">{EXAMPLE_BU_SNIPPET}</pre>
          </section>

          <section id={SECTION_IDS.checklist} className={styles.section} tabIndex={-1}>
            <h4 className={styles.sectionTitle}>Checklist antes de enviar</h4>
            <ol className={styles.list}>
              <li>Cada arquivo é <code>.csv</code> e abre sem erro em editor com UTF-8.</li>
              <li>Coluna A renomeada para <code>linha</code> em todos os DREs.</li>
              <li>Seis rótulos obrigatórios presentes em cada um dos sete arquivos.</li>
              <li>
                Nas seis BUs (não consolidado), uma linha de headcount entre as três aceitas — com números nos anos certos.
              </li>
              <li>Último ano “com dado” bate em todos os sete obrigatórios.</li>
              <li>Se anexou balanço: colunas <code>categoria</code>, <code>conta</code>, <code>tipo</code> + anos.</li>
            </ol>
          </section>
        </div>
      </div>
    </div>
  )
}
