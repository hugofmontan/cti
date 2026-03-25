# Funcionamento do projeto — `artefato_calculadora`

Este documento descreve **em profundidade** como o repositório funciona: propósito, arquitetura, fluxo de dados, módulos de negócio, consolidação, DCF, API, frontend e dados de referência.

---

## 1. Propósito

O projeto é uma **ferramenta de projeção financeira** que:

1. Projeta a **DRE** (Demonstração do Resultado do Exercício) de **várias unidades de negócio (BUs)** para os anos **2026–2030**.
2. **Consolida** essas BUs numa DRE de grupo, com regras específicas abaixo do EBITDA e no resultado financeiro.
3. Deriva **fluxo de caixa livre (FCFF)** e um **valuation por DCF** (valor da empresa e do equity), com sensibilidade e múltiplos implícitos.
4. Expõe tudo via **API REST** e um **dashboard React** para ajuste de premissas e visualização.

A lógica de negócio está documentada em `docs/plano_implementacao_*.md` e espelhada no código em `projecao_bus/`.

---

## 2. Visão de arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                        │
│  Premissas → POST /api/simulate → exibe DRE, FCFF, DCF, gráficos        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP (JSON)
┌───────────────────────────────────▼─────────────────────────────────────┐
│                         API (FastAPI)                                    │
│  GET /api/health | GET /api/defaults | GET /api/historical-dre | POST /api/simulate │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                    projecao_bus.orchestrator.run_simulation              │
│  FOPM → Renovação → AMS → Venda SW → Data Science → Consolidado → DCF    │
└───────────────────────────────────────────────────────────────────────────┘
```

- **Motor numérico**: Python, principalmente `pandas.DataFrame`.
- **Sem dependência obrigatória de CSV** no fluxo principal da API: tudo roda **em memória** após a refatoração do DCF (beta/WACC por pesos de faturamento usa os DataFrames das BUs).

---

## 3. Estrutura de diretórios (resumo)

| Caminho | Papel |
|--------|--------|
| `projecao_bus/` | Pacote principal: uma BU por módulo + `consolidado.py` + `orchestrator.py` + `shared.py` |
| `projecao_bus/dcf/` | Pipeline BP → NCGL → FCFF → valuation DCF + WACC sensibilidade |
| `api/` | FastAPI: `app.py` (factory), `routes/simulation.py`, `schemas.py` |
| `frontend/` | SPA React: formulários de premissas, gráficos, tabelas |
| `data/historico/` | CSVs de histórico usados para **drivers** (ex.: FOPM lê `dre_fopm_historico.csv`) |
| `data/original/` | Planilhas/DREs originais de referência (não são entrada obrigatória de runtime) |
| `docs/` | Planos de implementação e esta documentação |
| `tests/` | Testes de smoke (FOPM, orquestrador, API) |

Pastas geradas (`projecoes/`, `dcf_output/`) podem existir quando alguém roda `projetar_e_salvar_*` ou `run_dcf_pipeline(salvar_csv=True)`; são ignoradas pelo git.

---

## 4. Horizonte e premissas macro compartilhadas

### 4.1 Anos

Todas as projeções usam **2026–2030** como `ANOS_PADRAO` / `ANOS` no orquestrador.

### 4.2 Inflação Focus (`shared.py`)

`INFLACAO_FOCUS` é um dicionário ano → taxa anual usada em várias BUs para reajuste de custos, tickets, etc.

### 4.3 Alíquota ISV genérica FOPM/Renovação/Venda SW/Data Science

`ALIQUOTA_ISV = 0.1743` em `shared.py` aplica-se onde o plano define imposto sobre vendas nesse modelo.

**Exceção**: AMS usa alíquota própria no módulo `ams.py` (não a `ALIQUOTA_ISV` global).

### 4.4 Validação de anos

`_validar_anos()` garante que todos os anos pedidos existem em `INFLACAO_FOCUS`.

---

## 5. Módulos de unidade de negócio (BUs)

Cada BU tem funções do tipo `projetar_dre_*` que retornam um `DataFrame` com **uma linha por ano** e colunas alinhadas ao plano (receita, custos, margens, EBITDA, etc.).

### 5.1 FOPM Brasil (`fopm.py`)

- **Entrada histórica**: `data/historico/dre_fopm_historico.csv` — usado para calcular **ratios** (incentivos/RL, outras diretas/RL, etc.) e bases (custo por funcionário, horas por NF, ticket médio).
- **Drivers operacionais**: headcount planejado, ociosidade, horas alocadas, NF, ticket médio em cascata com inflação.
- **Premissas** expostas no orquestrador: `headcount_por_ano`, `ociosidade_por_ano` (merge com defaults).
- **Saída**: colunas de operação até lucro líquido simplificado na BU (sem IRPJ como AMS).

### 5.2 Renovação (`renovacao.py`)

- Receita a partir de base 2025 + **reajuste** (inflação + spread) e **churn** opcional.
- Usa `ALIQUOTA_ISV` e `INFLACAO_FOCUS` de `shared`.
- Premissas: `spread_real`, `churn`.

### 5.3 AMS (`ams.py`)

- **Depende do FOPM**: o faturamento incremental AMS é uma fração do **FB FOPM** (`taxa_conversao_fopm`); há base retida 2025, reajuste, churn, ticket, horas, D&A por hora, IRPJ/CSLL sobre LAIR, receita/despesa financeira próprias.
- Importa `projetar_dre_fopm_brasil` de `.fopm` e utilitários de `.shared`.
- Premissas: `taxa_conversao_fopm`, `churn`.

### 5.4 Venda de Softwares (`venda_softwares.py`)

- Crescimento nominal com **fator real** + inflação.
- Premissa: `fator_crescimento_real`.

### 5.5 Data Science (`data_science.py`)

- Receita = **projetos inteiros × ticket médio**; o número de projetos é **derivado** de `headcount_por_ano` e `ociosidade_por_ano`: `floor(N × 160 × 12 × (1 − ociosidade) / 3.840)`.
- Premissas no orquestrador: `headcount_por_ano`, `ociosidade_por_ano` (default 15% fixo por ano).

### 5.6 Administrativa (`administrativa.py`)

- Existe como BU para **rateio e referência** no plano; **não entra na soma** do consolidado operacional (o consolidado trata rateio como cancelamento interno — ver seção 6).
- Pode ser gerada e salva em CSV via `projetar_e_salvar_administrativa`, mas **não** faz parte do `dfs` do `run_simulation` atual.

---

## 6. Consolidado (`consolidado.py`)

### 6.1 BUs que entram na soma

Chaves: `fopm`, `renovacao`, `ams`, `venda_sw`, `data_science`.

Para cada ano:

- Soma linha a linha: receita bruta, deduções, RL, incentivos, pessoal, outras diretas, MC1, remuneração sócios, MC2, outras ADM, honorários, **EBITDA**.

### 6.2 Rateio administrativo

Na consolidação, o **rateio some a zero** (transferência interna entre BUs e ADM); não há linha de rateio agregada no consolidado do modelo.

### 6.3 D&A consolidada e EBIT

- **`da_consolidada`** vem do **BP** (`montar_bp` → coluna `da_total`): cascata de D&A do CAPEX de expansão (20% × 5 anos por safra), **não** da D&A da AMS nem do CFP.
- `ebit = ebitda - da_consolidada` (mesma D&A usada no FCFF / DCF).

### 6.4 Resultado financeiro e LAIR

- **Receita financeira** = `Caixa_final[t-1]` × SELIC Focus × `SPREAD_RENDIMENTO_CAIXA` (quebra de circularidade: usa o **saldo de caixa após FCFF e dividendos** do ano anterior, não o LL).
- **Despesa financeira** fixa (`DESPESA_FINANCEIRA_FIXA`).
- `lair = ebit + receita_financeira - despesa_financeira`.

### 6.5 IRPJ, lucro líquido e caixa

- **IRPJ/CSLL consolidado** = soma dos `irpj_csll` das BUs operacionais (na prática, só a AMS é **> 0**).
- `lucro_liquido = lair - irpj_csll`.
- **Participações** = percentual do LL (`RATIO_PARTICIPACOES`) — **linha de DRE**; **não** entram no saldo de caixa desta cadeia.
- **Caixa** (mesmo valor da coluna `caixa_final` do fluxo):  
  `NOPAT = EBIT × (1 − 34%)`, `FCFF = NOPAT + D&A_total − CAPEX − ΔNCG`,  
  `dividendos = 50% × lucro_liquido`,  
  `caixa = caixa_anterior + FCFF − dividendos` (caixa base 2025).

Funções principais:

- `projetar_dre_consolidado_de_dfs(dfs, ...)` — usada pelo orquestrador (sem CSV).
- `projetar_dre_consolidado(...)` — lê CSVs em `projecoes/` se quiser rodar standalone.

---

## 7. Orquestrador (`orchestrator.py`)

`run_simulation(premissas)`:

1. **Merge** de `premissas_padrao()` com o JSON do usuário (`_deep_merge`).
2. Projeta **nesta ordem**:
   - FOPM → Renovação → AMS (usa FOPM) → Venda SW → Data Science.
3. Monta `dfs` com chaves `fopm`, `renovacao`, `ams`, `venda_sw`, `data_science`.
4. Chama `projetar_dre_consolidado_de_dfs`.
5. Chama `run_dcf_pipeline_from_frames(df_cons, df_ams, dfs_bu=dfs, wacc=..., g=..., salvar_csv=False)`.

`resultado_para_json` serializa DataFrames para listas de dicts e extrai métricas de DCF para o frontend.

**Warnings**: churn muito alto em Renovação ou AMS gera avisos textuais.

---

## 8. Pipeline DCF (`projecao_bus/dcf/`)

### 8.1 Visão geral

A cadeia documentada em `pipeline.py`:

1. **BP** (`bp.py`): monta balanço patrimonial operacional simplificado e necessidades de **CapEx** e **D&A** total a partir do consolidado e de funcionários.
2. **NCGL** (`ncgl.py`): necessidade de capital de giro líquido e **variação** ano a ano.
3. **Fluxo** (`fluxo.py`):  
   - **NOPAT = EBIT consolidado × (1 − 34%)** (IR sintético sobre o EBIT).  
   - FCFF = NOPAT + D&A total − CapEx − ΔNCG.  
   - Dividendos = LL consolidado × `PAYOUT_DIVIDENDOS` (50%).  
   - Caixa do fluxo = caixa anterior + FCFF − dividendos (igual ao `caixa` do consolidado).
4. **Valuation** (`dcf_valuation.py`): valor presente dos FCFFs 2026–2030, **valor terminal** (Gordon), **Enterprise Value**, **Equity Value** (caixa 2025 − dívida líquida), **múltiplos** implícitos (EV/EBITDA, etc.).
5. **Sensibilidade** (`sensitivity.py`): matriz WACC × g e cenários de gabarito.
6. **WACC** (`wacc.py`): para **beta ponderado por ano**, usa **faturamento bruto** por BU; com o orquestrador, isso vem de `faturamentos_bu_de_dfs(dfs_bu, ...)` — **sem** ler `projecoes/*.csv`.

Constantes importantes estão em `dcf/constants.py` (WACC fixo, g perpetuidade, payout, caixa base 2025, etc.).

### 8.2 Modo CSV legado

`run_dcf_pipeline()` lê consolidado e AMS de `projecoes/` — útil para scripts offline; a **API** usa apenas `run_dcf_pipeline_from_frames` com DataFrames.

---

## 9. API (`api/`)

- **Factory**: `api/app.py` → `create_app()` registra CORS e o router.
- **Rotas** (`api/routes/simulation.py`):
  - `GET /api/health`
  - `GET /api/defaults` → mesmo conteúdo que `premissas_padrao()`
  - `GET /api/historical-dre` → consolidado e DREs por BU (2018–2025) lidos de `data/original/*.csv` via `projecao_bus.historical_dre.load_historical_dre_bundle()`
  - `POST /api/simulate` → corpo `{ "premissas": { ... } }` (opcional); executa `run_simulation` e retorna JSON flatten via `resultado_para_json`.
- **Compat**: `api/main.py` reexporta `app` para `uvicorn api.main:app`.

Execução típica:

```bash
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

A raiz `/` não tem rota (404 é esperado). Documentação interativa: `/docs`.

---

## 10. Frontend (`frontend/`)

- **Vite + React + TypeScript**.
- `API_BASE_URL` = `/api` em `src/utils/constants.ts` — o dev server do Vite costuma **proxy** para o backend na mesma origem ou porta configurada.
- Fluxo:
  1. `useSimulation` carrega `GET /api/defaults` e guarda premissas.
  2. `useHistoricalDRE` carrega `GET /api/historical-dre` e mescla com a projeção nas tabelas e gráficos (colunas 2018–2025 em tom azul, 2026–2030 em tom verde).
  3. Ao montar / ao recalcular, `POST /api/simulate` com `{ premissas }`.
  4. Resposta alimenta gráficos (receita por BU, margens, waterfall DCF) e tabelas (DRE consolidado, fluxo, múltiplos).

---

## 11. Utilitários compartilhados (`shared.py`)

- `INFLACAO_FOCUS`, `ALIQUOTA_ISV`
- `_validar_anos`
- `salvar_projecao_csv` → grava em `projecoes/` sob `projecao_bus/` (quando se usa `projetar_e_salvar_*` no CLI)

Isso evita imports circulares e o antigo padrão `from fopm import ...` fora do pacote.

---

## 12. Testes e qualidade

- `tests/test_fopm.py`: colunas essenciais do DataFrame FOPM.
- `tests/test_orchestrator.py`: chaves do retorno de `run_simulation`.
- `tests/test_api.py`: `/api/health` e `/api/simulate` retornam JSON válido.

Comando: `pytest tests/ -v` (ou `make test`).

---

## 13. Como rodar o motor sem API

- `python -m projecao_bus.orchestrator` — executa o orquestrador como script (se existir `if __name__` no arquivo; caso contrário, importar `run_simulation` em REPL).
- Módulos individuais: `python -m projecao_bus.fopm` etc. geram CSV em `projecoes/` quando implementado `salvar_projecao_csv`.

---

## 14. Pontos de atenção para manutenção

1. **Alterar anos** além de 2030 exige atualizar `INFLACAO_FOCUS`, planos em `docs/` e possivelmente constantes do DCF.
2. **Consolidado** depende de colunas homogêneas nas cinco BUs (nomes como `faturamento_bruto`, `ebitda`, etc.).
3. **IRPJ na DRE consolidada** vem das BUs (soma dos `irpj_csll`; só AMS > 0). **NOPAT no FCFF** usa **34% sobre o EBIT consolidado**, independente desse IR de LAIR na AMS — mudanças na AMS ainda afetam LAIR consolidado e LL via `irpj_csll` da AMS.
4. **Duas fontes de verdade** para DCF offline: DataFrames (API) vs CSV (`run_dcf_pipeline`); preferir sempre o fluxo do orquestrador para consistência com a API.

---

## 15. Referência cruzada

- Planos por tema: `docs/plano_implementacao_*.md`
- Reestruturação do repo: `docs/plano_reestruturacao_artefato_calculadora.md`
- README rápido: `README.md`

---

*Última atualização: alinhado ao código em `projecao_bus/`, `api/` e `frontend/` do repositório.*
