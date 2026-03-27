# Funcionamento do Projeto e do Agente (Analista IA) — Documento Técnico Completo
## 0. Objetivo deste documento
Este documento explica, de ponta a ponta, como funciona todo o projeto `artefato_calculadora` e, principalmente, como o **agente (Analista IA)** opera: desde a entrada no endpoint HTTP, passando por **roteamento de intent**, **pré-cálculo determinístico (artifacts)**, **arquitetura de contexto enviada ao LLM**, **validação/normalização do JSON**, execução de **scenario_action** (quando existe), e finalmente como o **frontend renderiza artifacts**.
O foco especial é a **arquitetura de contexto do agente** (estrutura e propósito de cada campo).
Referências principais:
- `api/services/agent_orchestrator.py`
- `api/services/agent_intent.py`
- `api/services/agent_context.py`
- `api/services/openai_client.py`
- `api/services/agent_output_normalizer.py`
- `api/services/agent_deterministic.py`
- `api/prompts/agent_system_prompt.md`
- `api/schemas.py`
- `frontend/src/components/agent/AgentArtifactRenderer.tsx`
- `frontend/src/components/agent/SensitivityHeatmap.tsx`
- `frontend/src/components/agent/ScenarioComparisonPanel.tsx`
- `frontend/src/types/agent.ts`
---
## 1. Visão geral do sistema (arquitetura em blocos)
### 1.1 Componentes principais
- **Motor financeiro e projeções** (`projecao_bus/`)
  - Projeta DRE por BU.
  - Consolida (soma / visão de grupo).
  - Calcula FCFF, DCF e sensibilidades/múltiplos.
- **API FastAPI** (`api/`)
  - Endpoint de simulação numérica.
  - Endpoint do agente: `POST /api/agent/query`.
  - Schemas Pydantic para payload e resposta do agente.
- **Frontend React** (`frontend/`)
  - Visualiza resultados de simulação.
  - Renderiza `artifacts` retornados pela API do agente.
- **Dados** (`data/`)
  - `data/original/`: CSVs originais (base de histórico).
  - `data/historico/`: históricos consumidos em rotas auxiliares.
### 1.2 Fluxo principal do sistema numérico
1. Entrada de premissas (ex.: churn, spread real, taxa conversão etc.).
2. Projeções por BU (2026–2030).
3. Consolidação.
4. DCF (EV, Equity, sensibilidade, múltiplos).
5. Retorno JSON com estrutura numérica (consumida pelo agente e pelo dashboard).
---
## 2. API do Projeto (visão funcional)
### 2.1 Endpoints relevantes
- Rotas de simulação (ex.: em `api/routes/simulation.py`)
  - `GET /api/health`
  - `GET /api/defaults`
  - `GET /api/historical-dre`
  - `POST /api/simulate`
- Endpoint do agente:
  - `POST /api/agent/query` (implementado via `api/routes/agent.py`)
Arquivo:
- `api/routes/agent.py`
### 2.2 Contratos do agente (schemas)
Arquivo:
- `api/schemas.py`
O agente retorna um `AgentQueryResponse` com campos:
- `answer_markdown`: texto final em Markdown
- `artifacts`: lista opcional de artefatos (table/chart/kpi/kpi_panel/scenario_comparison/sensitivity_matrix)
- `confidence`: `high | medium | low`
- `data_used`: lista de “caminhos”/fontes numéricas (strings)
- `warnings`: lista de strings
- `data_lineage` (opcional): rastreio com `{label, value, source, scenario_id}`
- `response_source`: `openai | deterministic | fallback`
- `intent`: string do intent roteado
- `scenario_id`: id do cenário (hash)
- `scenario_action` (opcional): quando o LLM solicita rodar novo cenário
---
## 3. Frontend: como artifacts aparecem para o usuário
### 3.1 Renderização central
Arquivo:
- `frontend/src/components/agent/AgentArtifactRenderer.tsx`
Ele decide por `artifact.type`:
- `table` -> componente `Table`
- `chart` -> `renderChart()` (Recharts: LineChart/BarChart)
- `kpi_panel` -> `KPIPanelCard`
- `scenario_comparison` -> `ScenarioComparisonPanel`
- `sensitivity_matrix` -> `SensitivityHeatmap`
### 3.2 Contrato do tipo `sensitivity_matrix`
Arquivo:
- `frontend/src/types/agent.ts`
`AgentSensitivityMatrixArtifact` contém:
- `row_param` (ex.: `wacc`)
- `col_param` (ex.: `g`)
- `row_values` (lista)
- `col_values` (lista)
- `matrix` (matriz numérica)
E o frontend renderiza como tabela “heatmap”:
- `frontend/src/components/agent/SensitivityHeatmap.tsx`
---
## 4. O Agente (Analista IA): visão operacional
### 4.1 Endpoint e validações iniciais
Arquivo:
- `api/routes/agent.py`
Processos no endpoint:
- Confere `AGENT_ENABLED`
- Rate limit por IP (`check_rate_limit`)
- Valida mínimo de tamanho de `question` (≥ 3)
- Normaliza `history` em lista de dicionários (via `model_dump`)
- Chama o orquestrador:
  - `run_agent_query(...)` em `api/services/agent_orchestrator.py`
---
## 5. Pipeline do Agente (orquestração completa)
Arquivo central:
- `api/services/agent_orchestrator.py`
Função:
- `run_agent_query(question, premissas, history, session_memory)`
### 5.1 Pipeline em ordem (com paralelismo)
O orquestrador executa:
1. Roteamento de intenção:
   - `routed = route_question(question)` (`api/services/agent_intent.py`)
   - `visual_profile = INTENT_VISUAL_PROFILE.get(routed.intent, {})`
2. Montagem de memória técnica (opcional):
   - `session_memory_from_dict(session_memory)`
   - usa `infer_technical_level(...)` ao analisar histórico e pergunta
3. Simulação e histórico em paralelo:
   - `run_simulation(premissas=premissas)`
   - `load_historical_dre_bundle()`
4. Geração do `sim_json`:
   - `sim_json = resultado_para_json(sim)`
5. Computa `scenario_id`:
   - `compute_scenario_id(sim_json)` (hash)
6. Detecção de anomalies (atualmente desligada por `should_attach_anomalies=False`)
7. Pré-cálculo determinístico do intent:
   - `precomputed = compute_intent_artifacts(routed, question, sim_json, historical_bundle, scenario_id)`
8. Construção do contexto do LLM:
   - `context = build_agent_context(...)` (`api/services/agent_context.py`)
   - injeta `visual_profile` e `precomputed_artifacts` no contexto
9. Chamada do LLM (OpenAI), validação e merging:
   - `OpenAIClient.generate_structured(...)`
   - `normalize_agent_response_dict(...)`
   - `AgentQueryResponse.model_validate(...)`
   - se sucesso, faz merge dos artifacts determinísticos que o LLM não trouxe
10. Se o LLM retorna `scenario_action`, o backend executa fase 2:
   - `execute_llm_scenario(...)` e `build_phase2_context(...)`
   - nova chamada ao LLM com contexto de execução e sem gerar novo scenario_action
---
## 6. Roteamento de intenção e `entities`
Arquivo:
- `api/services/agent_intent.py`
### 6.1 `Intent` (enum) e `INTENT_VISUAL_PROFILE`
- `Intent` enum possui intents para gráficos/tabelas/KPIs e análises financeiras.
- `INTENT_VISUAL_PROFILE` define qual tipo de visual a UI deve esperar por intent.
- Exemplo:
  - `Intent.MARGIN_EBITDA_EVOLUTION_BU_VS_CONSOLIDATED` -> `{ "default": "chart", "type": "line" }`
  - `Intent.STRESS_TEST` -> `{ "default": "chart", "type": "sensitivity_matrix" }`
### 6.2 Heurísticas do `route_question`
O roteador:
- Normaliza acentos (`unicodedata.normalize`) para captar “evolução”, “evolucao”, etc.
- Detecta BUs via aliases:
  - `fopm`, `renovacao`, `ams`, `venda_sw`, `data_science`
- Detecta anos via regex (2012–2030 e incluindo 2030)
- Decide o intent com regras baseadas em palavras:
  - margem + ebitda + evolução/plot + consolidado -> novo intent (BU vs consolidado)
  - stress/sensibilidade -> `Intent.STRESS_TEST`
  - etc.
### 6.3 `entities` típicas
- `bu` (quando aplicável)
- `start_year`, `end_year` (para evolução no horizonte)
- `year` (para métricas pontuais)
- `impact_direction` (positive/negative/any)
- `bus_mentioned` (lista)
- `metric`, `bu_a`, `bu_b`, etc.
---
## 7. Pré-cálculo determinístico de artifacts (segurança numérica)
Arquivo:
- `api/services/agent_deterministic.py`
Função:
- `compute_intent_artifacts(...)`
### 7.1 Propósito
- Quando há um handler para o intent, o backend computa números/artifacts com base no `sim_json`.
- Isso reduz alucinação e garante que os gráficos/tabelas sigam os dados reais do motor.
### 7.2 Contrato: `PrecomputedResult`
Retorna:
- `artifacts`: lista de `AgentArtifact`
- `context_hint`: texto auxiliar numérico (p/ colocar no contexto do LLM)
- `data_used`: lista de “caminhos” para rastreabilidade
### 7.3 Mesclagem com resposta do LLM
Arquivo:
- `api/services/agent_orchestrator.py`
A função `merge_responses(...)`:
- Se `precomputed_artifacts` não for vazio:
  - cria `existing_types` a partir dos artifacts do LLM
  - adiciona apenas artifacts cujo `type` ainda não exista na lista final
Isso evita duplicação por tipo.
---
## 8. Arquitetura de Contexto do Agente (foco principal)
Arquivo:
- `api/services/agent_context.py`
### 8.1 O que o LLM recebe
O `OpenAIClient` constrói mensagens assim:
- `system`: conteúdo de `api/prompts/agent_system_prompt.md`
- `user`: concatena:
  - Pergunta (`prompt`)
  - `system_context_markdown` (texto fonte principal do cenário)
  - JSON com metadados auxiliares:
    - `context.items()` menos `system_context_markdown`
Arquivo:
- `api/services/openai_client.py`
### 8.2 Estrutura do objeto `context` (chaves principais)
A função `build_agent_context(...)` retorna um dict com:
- `meta_context`
- `conversation_context`
- `system_context_markdown`
- `visual_profile`
- `precomputed_artifacts`
- `technical_level` (se houver `session_memory`)
- `data_context` (varia por intent detectado “internamente” pela função `detect_intent()` dentro de `agent_context.py`)
- (opcional) `extra_context_hint` embutido no `system_context_markdown`
#### 8.2.1 `meta_context` (estrutura)
Em `build_agent_context`:
- `model_version`: `"sim-v1"`
- `currency`: `"BRL"`
- `years`: `[2026, 2027, 2028, 2029, 2030]`
- `bus`: `BU_KEYS`
- `generated_at`: timestamp ISO
- `intent_hint`: valor de `detect_intent(question)` (heurística simples para “valuation”, “comparison”, “table”, “timeseries” etc.)
- `router_intent`: `router_intent` vindo do roteador do orquestrador (intent específico)
- `scenario_id`: hash do cenário
- `definitions`: dicionário com definições úteis para linguagem do LLM, ex.:
  - `margem_ebitda: "ebitda / receita_liquida"`
  - `fcff: "nopat + da_total - capex - delta_ncg"`
#### 8.2.2 `conversation_context`
- `history_summary`: resumo das últimas entradas do histórico
- Formato:
  - `[f'{role}: {conteudo_truncado[:120]}' ...]`
A intenção é reduzir tokens sem perder “tema”/nível técnico.
#### 8.2.3 `system_context_markdown` (texto fonte principal)
Gerado por `_build_system_context(simulation_data)`.
Inclui, tipicamente:
- **Resumo executivo** com tabela de DRE consolidada por ano
  - `Fat. Bruto`, `Receita Liquida`, `EBITDA`, `Mg EBITDA`, `Lucro Liquido`
- **Métricas por BU (2026 vs 2030)**
  - Por BU, calcula e apresenta deltas percentuais em valores de:
    - Fat. Bruto
    - EBITDA
- **Valuation (DCF)**
  - `Enterprise Value`, `Equity Value`, `EV/EBITDA implicito`, `WACC`, `g` (perpetuidade)
- **Premissas-chave utilizadas**
  - Exemplo: churn/spread_real/taxa_conversao etc. (quando existirem)
- **Métricas derivadas**
  - Participação da BU na RL consolidada 2026 vs 2030
  - Impacto aproximado na margem consolidada via deltas de EBITDA
- **Seção “SUA FUNCAO”**
  - regras gerais de resposta:
    - usar dados concretos
    - comparar tendências
    - ser quantitativo quando possível
    - gerar tabela/gráfico conforme `visual_profile` (quando disponível) e pedido explícito
Além disso, quando `extra_context_hint` existe (vindo de `compute_intent_artifacts`):
- ele é adicionado ao `system_context_markdown` sob um bloco:
  - “Dados pre-computados para esta intent”.
#### 8.2.4 `visual_profile`
- Vem de `INTENT_VISUAL_PROFILE.get(routed.intent, {})` no orquestrador.
- É um “hint” estrutural:
  - qual tipo de visual é padrão para aquela intent
  - exemplo: line/bar/waterfall/table etc.
#### 8.2.5 `precomputed_artifacts`
- Inseridos no contexto para que o LLM:
  - use números exatos (quando já calculados)
  - e/ou entenda quais artifacts já existem para a resposta final
A lista é serializada como dicts (via `model_dump()` quando aplicável).
#### 8.2.6 `technical_level`
- Se `session_memory` estiver presente:
  - o sistema detecta nível técnico e ajusta linguagem
- Caso contrário:
  - `technical_level = "auto"`
#### 8.2.7 `data_context` (varia por intent “detectada” no contexto)
Em `build_agent_context`, o código faz:
- se `intent == "valuation"`:
  - `{"dcf": ..., "consolidado": ...}`
- se `intent in {"comparison", "timeseries", "table"}`:
  - `{"dre": ..., "consolidado": ...}`
- caso contrário:
  - `{"dcf": ..., "dre": ..., "consolidado": ..., "fluxo": ...}`
Observação importante:
- Esse `intent` é o resultado de `detect_intent(question)` dentro de `agent_context.py`, não necessariamente o `router_intent` do roteador principal.
- O `router_intent` aparece em `meta_context.router_intent`, mas `data_context` depende da heurística “detect_intent” do contexto.
### 8.3 Arquitetura do prompt (system prompt do LLM)
Arquivo:
- `api/prompts/agent_system_prompt.md`
O system prompt implementa regras como:
- sempre responder em PT-BR, com tom consultivo
- usar somente dados do contexto enviado
- não inventar números
- contrato JSON obrigatório:
  - `answer_markdown, confidence, artifacts, data_used, warnings, data_lineage (opcional)`
- regras de geração de artefatos:
  - se `visual_profile.default` não for nulo, gerar o artifact correspondente
  - se `precomputed_artifacts` não estiver vazio, usar seus valores exatos e não recalc
E seção específica por intent (incluindo `stress_test`):
- orienta a LLM a construir a sensibilidade a partir de `dcf.sensitivity_matrix` (heatmap/`ArtifactSensitivityMatrix`).
---
## 9. Validação e Robustez do JSON do LLM
### 9.1 `OpenAIClient.generate_structured`
Arquivo:
- `api/services/openai_client.py`
Características:
- usa `response_format={"type":"json_object"}`
- lê `agent_system_prompt.md` em runtime
- tenta parsear JSON com robustez:
  - remove code fences ```json ... ```
  - extrai primeiro objeto JSON `{...}` quando necessário
Se houver truncamento por tokens (`finish_reason == "length"`):
- re-tenta com mais tokens.
### 9.2 Normalização do output antes do Pydantic
Arquivo:
- `api/services/agent_output_normalizer.py`
O normalizador:
- garante que `answer_markdown` exista e seja string
- converte `confidence` para `high/medium/low` (ou mapeia números)
- garante `data_used` e `warnings` como listas
- normaliza `artifacts`:
  - remove invalid artifacts (quando aplicável)
  - normaliza aliases comuns do LLM:
    - `line_chart` -> `type=chart, chart_type=line`
    - `horizontal_bar_chart` -> `chart_type=horizontal_bar`
    - e assim por diante
- valida/“saneia” `scenario_action` com whitelist e clamp por faixas permitidas
### 9.3 Validação final por Pydantic
Arquivo:
- `api/schemas.py`
No orquestrador:
- `AgentQueryResponse.model_validate(...)`
Se falhar:
- remove artifacts inválidos (`validated_no_artifacts["artifacts"] = []`)
- preserva o texto da resposta
Esse é exatamente o mecanismo que evita quebrar a request quando o LLM devolve artifacts com schema incorreto.
---
## 10. Cenários dinâmicos (`scenario_action`) — execução em duas fases
Quando o LLM detecta que o usuário pediu mudanças em premissas (“rodar/simular/e se...”), ele pode retornar `scenario_action`.
Fluxo:
- Fase 1: LLM retorna JSON com `scenario_action`
- Orquestrador executa:
  - `execute_llm_scenario` em `api/services/agent_llm_scenario.py`
  - roda `run_simulation` com premissas alteradas
  - gera artifacts determinísticos do scenario executado (ex.: `scenario_comparison` e `EV por cenario`)
- Fase 2: novo contexto é montado por `build_phase2_context(...)`
  - injeta `scenario_execution` (action, scenario_comparison, ev_chart etc.)
- chama LLM novamente para produzir a explicação final
- garante que `scenario_action` não gere outro scenario_action na fase 2
---
## 11. Detalhamento: arquitetura de artifacts (tipos e mapeamento)
### 11.1 `ArtifactChart`
- `type="chart"`
- `chart_type`: `line | bar | waterfall | stacked_bar | grouped_bar | horizontal_bar`
- `x`: categorias (anos, labels etc.)
- `series`: lista de `{name, values}`
- `unit`: string opcional (ex.: `"BRL"`, `"%"`)
- `reference_line`: opcional
Renderer:
- `frontend/src/components/agent/AgentArtifactRenderer.tsx`
### 11.2 `ArtifactTable`
- `type="table"`
- `title`
- `columns`: lista de strings
- `rows`: matriz de linhas
Renderer:
- `frontend/src/components/ui/Table.tsx`
### 11.3 `ArtifactKPIPanel`
- `type="kpi_panel"`
- `items`: lista de `ArtifactKPI`
### 11.4 `ArtifactScenarioComparison`
- `type="scenario_comparison"`
- `scenarios`: lista de `ArtifactScenarioResult`
Renderer:
- `frontend/src/components/agent/ScenarioComparisonPanel.tsx`
### 11.5 `ArtifactSensitivityMatrix`
- `type="sensitivity_matrix"`
- `row_param` / `col_param`
- `row_values` / `col_values`
- `matrix`: número[][] (valores para EV/resultado na malha)
Renderer:
- `frontend/src/components/agent/SensitivityHeatmap.tsx`
---
## 12. Como o projeto lida com “visuais automáticos” vs “visuais explícitos”
Existe um mecanismo duplo:
- `visual_profile` baseado em `Intent` (`INTENT_VISUAL_PROFILE`) no orquestrador
- regras do system prompt que determinam quando artifacts devem ser gerados:
  - se `visual_profile.default` não for nulo, gerar automaticamente o tipo padrão
  - se `precomputed_artifacts` vier, usar os valores exatos
Além disso, existe ainda `wants_visual(question)` (heurística por tokens), como compatibilidade.
---
## 13. Testes (o que existe e por que importa)
Pontos do que cobre:
- `tests/test_agent_intent.py`
  - valida rotas por intent/entidades
- `tests/test_golden_agent.py`
  - valida “golden questions” com LLM mock e espera artifacts válidos
- `tests/test_agent_llm_scenario_action.py`
  - valida duas fases de `scenario_action`
Isso é importante porque o contrato de JSON do LLM + schema de artifacts é altamente sensível.
---
## 14. Observações e “pontos de atenção” (para o Claude tirar conclusões de melhoria)
Esta seção não altera código; serve como “lista de hipóteses” de melhoria para análise.
14.1 Complexidade do contexto
O `context` tem:
- `system_context_markdown` enorme (texto com tabelas e métricas derivadas)
- `meta_context` e `data_context` e ainda
- `visual_profile` + `precomputed_artifacts`
Isso pode aumentar custo/latência e tokens. Uma melhoria típica é estruturar melhor “dados tabulares” e reduzir redundância textual.
14.2 Potencial divergência entre intents
- O roteador principal usa `route_question`.
- O `detect_intent` para montar `data_context` em `agent_context.py` usa heurística própria.
- Isso pode gerar inconsistências em `data_context` (ex.: um intent roteado específico, mas `data_context` montado por outra heurística simples).
14.3 Robustez de artifacts
- O normalizador faz aliases de `chart_type` e `type`.
- Mas se o LLM inventa campos ou manda `artifacts` com type errado, o Pydantic remove artifacts.
A melhoria seria:
- impor ainda mais fortemente o schema no prompt
- e/ou aumentar validação prévia no normalizador
14.4 Merge por tipo de artifact
O merge evita duplicação por `type`, mas não por `chart_type`/conteúdo.
Pode haver casos em que dois charts diferentes de mesmo `type` deveriam co-existir.
14.5 Sensibilidade (g x wacc)
- O heatmap usa `row_param` e `col_param` diretamente para rotulagem.
- A melhor prática é documentar explicitamente no `agent_system_prompt.md` quais valores esperados (se são razão ou percentual), para o frontend não precisar “inferir escala”.
---
## 15. Resumo final (o que o agente faz, em 1 parágrafo)
Para cada pergunta, o backend sempre roda uma simulação atual, roteia a intenção (`route_question`) e computa artifacts determinísticos quando existe handler. Em seguida, constrói um objeto de contexto com três camadas (texto `system_context_markdown`, metadados `meta_context`/`conversation_context`, e dados estruturados `data_context`, além de `visual_profile` e `precomputed_artifacts`) e envia ao LLM com um system prompt rígido que exige JSON validado pelo schema. Depois normaliza e valida a resposta do LLM, remove artifacts inválidos e faz merge dos artifacts determinísticos ausentes. Se o LLM pedir mudanças via `scenario_action`, o backend executa um novo cenário em duas fases, monta contexto de execução e volta ao LLM para explicar com números reais.
---
## Anexos (caminhos de arquivos citados)
- `api/routes/agent.py`
- `api/services/agent_orchestrator.py`
- `api/services/agent_intent.py`
- `api/services/agent_deterministic.py`
- `api/services/agent_context.py`
- `api/services/openai_client.py`
- `api/services/agent_output_normalizer.py`
- `api/services/agent_llm_scenario.py`
- `api/prompts/agent_system_prompt.md`
- `api/schemas.py`
- `frontend/src/components/agent/AgentArtifactRenderer.tsx`
- `frontend/src/components/agent/SensitivityHeatmap.tsx`
- `frontend/src/components/agent/ScenarioComparisonPanel.tsx`
- `frontend/src/types/agent.ts`
- `docs/FUNCIONAMENTO_AGENTE.md`
- `PROJETO.md`
