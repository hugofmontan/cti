# Funcionamento do agente — `Analista IA` (`/api/agent/query`)

Este documento descreve **somente** como o agente funciona no repositoreo: como a requisicao chega ao backend, como ele decide entre resposta deterministica vs LLM, como monta o contexto e como garante um contrato estavel de saida.

---

## 1. Entrada do agente (endpoint e validacoes)

O agente e acessado via:

`POST /api/agent/query` (arquivo: `api/routes/agent.py`)

Antes de executar a consulta, o endpoint aplica:

- Habilitacao: se `AGENT_ENABLED=false`, retorna `503`.
- Rate limit por origem: usa `check_rate_limit(identity)` com janela de 60s e max 30 req/identidade. Se exceder: `429`.
- Validacao minima: a pergunta deve ter pelo menos 3 caracteres (`400` se falhar).
- Normalizacao do historico: converte `payload.history` para uma lista de dicionarios via `model_dump()`.

Depois, chama o orquestrador principal:

- `run_agent_query(payload.question, payload.premissas, history)` (arquivo: `api/services/agent_orchestrator.py`)

---

## 2. Orcestracao principal (pipeline em `run_agent_query`)

A rotina central do agente (pipeline) fica em:

- `api/services/agent_orchestrator.py` -> `run_agent_query(...)`

O fluxo executa, em ordem:

1. Roda uma simulacao numerica sempre atual
   - `sim = run_simulation(premissas=premissas)`
   - Converte o resultado para JSON: `sim_json = resultado_para_json(sim)`
2. Calcula um id de cenario
   - `scenario_id = compute_scenario_id(sim_json)`
   - Esse id serve para rastreio na resposta.
3. Roteia a intencao da pergunta
   - `routed = route_question(question)`
   - O retorno (`RoutedIntent`) inclui:
     - `intent` (um `Intent` enum)
     - `entities` (entidades extraidas: anos, BU mencionada, direcao de impacto, etc.)
4. Detecta desejo explicito de visual
   - `wants_visual = _wants_visual(question)`
   - A funcao procura tokens como `grafico`, `gráfico`, `plot`, `tabela`, `visual`.
5. Carrega bundle de historico (best effort)
   - Tenta `load_historical_dre_bundle()`
   - Se falhar: `historical_bundle = None`
   - Esse bundle entra apenas em intencoes de historico.
6. Tenta responder deterministacamente (prioridade)
   - `det = execute_deterministic(routed, question, sim_json, historical_bundle, scenario_id, wants_visual)`
   - Se retornar nao-nulo: a resposta vai com `response_source="deterministic"` e o agente termina.
7. Se nao deterministico: constroi contexto e tenta LLM (OpenAI)
   - Constroi contexto: `context = build_agent_context(sim_json, question, history, router_intent=routed.intent.value)`
   - Cria client: `client = OpenAIClient(settings)`
   - Se `client.is_enabled()`:
     - chama `llm_raw = client.generate_structured(prompt=question, context=context)`
     - normaliza e valida:
       - `normalized = normalize_agent_response_dict(llm_raw)`
       - `validated = AgentQueryResponse.model_validate(...)`
     - retorna com `response_source="openai"`
8. Fallback local (se LLM falhar ou estiver desligado)
   - `out = _local_generic_fallback(question, scenario_id, routed.intent.value)`
   - Retorna com:
     - `response_source="fallback"`
     - `confidence="medium"`
     - mensagem generica orientando a reformulacao da pergunta.

---

## 3. Roteamento de intencao (heuristicas em `route_question`)

O roteamento fica em:

- `api/services/agent_intent.py` -> `route_question(question)`

Ele transforma a pergunta em:

- um `Intent` (ex.: `IMPACT_MARGIN_CONSOLIDATED`, `VALUATION_EV_EBITDA`, `TABLE_METRIC_BU_YEARS`, `GENERIC`)
- `entities` extraidas (ex.: `year`, `bus_mentioned`, `impact_direction`, `metric`, etc.)

As heuristicas principais:

- aliases de BU (ex.: `renovacao`, `venda sw`, `data science`, etc.)
- deteccao de anos (regex para anos entre 2012 e 2030)
- deteccao de termos de metrica (ex.: `receita`, `faturamento`, `ebitda`, `margem`, `EV/EBITDA`, `equity`)
- regra especial para evitar assumir ranking automaticamente quando a pergunta menciona uma BU mas nao cita `consolidado`

Quando nao encontra um match forte, o roteamento cai em:

- `Intent.GENERIC` (menor score)

---

## 4. Resposta deterministica (`execute_deterministic`)

O caminho deterministico fica em:

- `api/services/agent_deterministic.py` -> `execute_deterministic(...)`

Esse componente:

- recebe o `RoutedIntent` (intencao + entidades)
- recebe os dados do cenario (`sim_result` como `sim_json`)
- decide se consegue produzir uma resposta pronta

Ele implementa handlers para varias intencoes, por exemplo:

- `HISTORICAL_BU_METRIC`: consulta historico (usa `historical_bundle`)
- `PROJECTION_BU_METRIC_YEAR`: consulta projecao da BU em um ano
- `IMPACT_MARGIN_CONSOLIDATED`: ranking de impacto na margem EBITDA consolidada (2026->2030)
- `IMPACT_MARGIN_YEAR_BY_YEAR`: impactos ano a ano (top 3 por ano, com filtro por direcao quando especificado)
- `TIMESERIES_AMS_FATURAMENTO`: serie de faturamento da AMS (e opcionalmente `ArtifactChart` quando `wants_visual`)
- `MARGIN_BU_BY_YEAR`: margem por BU em um ano
- `COMPARE_GROWTH`: compara crescimento entre duas BUs (e opcionalmente `ArtifactChart`)
- `VALUATION_EV_EBITDA`: EV/EBITDA implicito e KPIs (e opcionalmente `ArtifactKPI`)
- `TABLE_METRIC_BU_YEARS`: cria `ArtifactTable` por pivot de metrica x BU x anos
- `EV_VS_EQUITY`: explica diferenca entre Enterprise Value e Equity Value

Quando um handler consegue produzir:

- ele retorna um `AgentQueryResponse`
- com `response_source="deterministic"`
- e, quando aplicavel, retorna `artifacts` (tabelas/graficos/KPIs)

Se a intencao nao tiver handler implementado (ou faltar dado), ele retorna `None` e o orquestrador segue para LLM/fallback.

---

## 5. Caminho OpenAI (contexto + resposta estruturada)

Quando a resposta deterministica nao acontece, o agente tenta LLM.

### 5.1 Habilitacao do LLM

- Arquivo: `api/services/openai_client.py` -> `OpenAIClient`
- `client.is_enabled()` exige:
  - `settings.agent_enabled`
  - SDK `openai` disponivel
  - existencia de `OPENAI_API_KEY`

Se habilitado, o agente chama:

- `generate_structured(prompt=question, context=context)`

### 5.2 Geracao com formato estruturado

O client:

- carrega o prompt de sistema em `api/prompts/agent_system_prompt.md`
- envia mensagens:
  - `system`: instrucoes do agente
  - `user`: pergunta + `system_context_markdown` + metadados JSON do contexto
- solicita `response_format={"type": "json_object"}`
- faz `json.loads(text)` para obter um dicionario JSON

---

## 6. Construcao de contexto (`build_agent_context`)

O contexto para o LLM fica em:

- `api/services/agent_context.py` -> `build_agent_context(...)`

O contexto contem principalmente:

1. `meta_context`
   - `scenario_id`, anos (2026-2030) e lista de BUs (`BU_KEYS`)
   - hint do intent detectado (`intent_hint`) e `router_intent`
   - definicoes de termos financeiros (ex.: margem EBITDA = ebitda/receita_liquida)
2. `conversation_context`
   - resumo do historico: usa apenas as ultimas 6 entradas e trunca `content` para 120 caracteres
3. `system_context_markdown`
   - texto consolidado com:
     - resumo da DRE consolidada (por ano)
     - metricas por BU (2026 vs 2030)
     - dados de valuation do DCF (EV/Equity, EV/EBITDA implicito, WACC, g)
     - metricas derivadas (participacao de share e delta EBITDA aproximado)
   - instrucoes de resposta (usar dados concretos e gerar tabela/grafico apenas quando pedido)

Tambem existe um ajuste do `data_context` dependendo do intent detectado:

- para `valuation`: inclui `dcf` e `consolidado`
- para `comparison`, `timeseries`, `table`: inclui `dre` e `consolidado`
- para os demais: inclui `dcf`, `dre`, `consolidado` e `fluxo`

---

## 7. Normalizacao e validacao do JSON (contrato estavel)

Depois que o LLM retorna JSON bruto, o agente tenta consertar tipos e formatos comuns antes de validar.

Esse passo fica em:

- `api/services/agent_output_normalizer.py` -> `normalize_agent_response_dict(...)`

A normalizacao garante, principalmente:

- `answer_markdown`
  - deve ser string
  - se faltar, tenta `answer`
  - se continuar vazio, usa "(resposta vazia)"
- `confidence`
  - converte `high/medium/low` ou mapeia numeros para faixas
  - se nao existir, assume `"medium"`
- `data_used` e `warnings`
  - converte para lista de strings
- `artifacts`
  - se vier ausente ou com tipo invalido, normaliza para `[]`

Depois disso, o orquestrador valida com:

- `AgentQueryResponse.model_validate(...)`

E garante metadados:

- `response_source="openai"`
- `intent=routed.intent.value`
- `scenario_id=scenario_id`

---

## 8. Artefatos e visualizacoes (`artifacts`)

O contrato do `AgentQueryResponse` permite retornar `artifacts` (opcionais), como:

- `ArtifactChart` (com `ArtifactChartSeries`)
- `ArtifactTable`
- `ArtifactKPI`

Regra geral:

- no deterministico: os artefatos dependem de `wants_visual` detectado na pergunta
- no caminho OpenAI: o prompt do system pede para usar `artifacts` apenas quando o usuario pedir explicitamente `grafico`, `tabela` ou `visualizacao`
- no fallback local: `artifacts` sai como lista vazia

---

## 9. Fallback de resposta (quando algo falha)

Se o caminho OpenAI falhar (erro de chamada, JSON invalido, ou validacao Pydantic) o orquestrador nao interrompe:

- ele cai para `_local_generic_fallback(...)`

Esse fallback retorna um `AgentQueryResponse` valido e com:

- `response_source="fallback"`
- `confidence="medium"`
- mensagem generica orientando a reformular com metrica, BU/consolidado e periodo correto.

---

## 10. Resumo operacional (em uma frase)

Para cada pergunta, o agente:

1. roda um cenario atual (simulacao),
2. roteia a intencao,
3. tenta uma resposta deterministica (menor custo/risco),
4. e, se necessario, usa LLM com contexto estruturado; sempre termina com um contrato validado ou fallback.

