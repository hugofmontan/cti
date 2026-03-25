# Projeto — Artefato Calculadora

Documento na **raiz do repositório** com visão geral do produto e do **Analista IA** (agente). Para detalhes técnicos do motor financeiro (DRE por BU, consolidado, DCF, colunas), use também [`docs/FUNCIONAMENTO_PROJETO.md`](docs/FUNCIONAMENTO_PROJETO.md).

---

## 1. O que é o projeto

Ferramenta de **projeção financeira** e **valuation**:

- Projeta a **DRE** de várias **unidades de negócio (BUs)** no horizonte **2026–2030**.
- **Consolida** as BUs numa visão de grupo.
- Calcula **FCFF** e **DCF** (valor da empresa, equity, sensibilidades e múltiplos).
- Oferece **API REST (FastAPI)** e **dashboard (React + Vite)** para ajustar premissas e visualizar resultados.
- Inclui o **Analista IA**: chat que responde com base no **cenário atual** (última simulação com as premissas enviadas ou padrão).

**Fluxo numérico principal:**

```text
premissas → projeções por BU → consolidado → DCF → JSON
```

Implementação central: `projecao_bus/orchestrator.py` (`run_simulation`).

---

## 2. Stack e pastas principais

| Pasta / arquivo | Função |
|-----------------|--------|
| `projecao_bus/` | Motor: uma BU por módulo (`fopm`, `renovacao`, `ams`, …), `consolidado`, `orchestrator`, `dcf/`, `shared.py` |
| `api/` | FastAPI: rotas, schemas Pydantic, serviços do agente, cliente OpenAI |
| `frontend/` | SPA React: dashboard, painel do agente (chat), gráficos (Recharts) |
| `data/historico/` | CSVs usados como drivers em algumas BUs (ex.: FOPM) |
| `data/original/` | DREs originais de referência; também base para **histórico** exposto ao agente (`historical_dre`) |
| `docs/` | Planos e documentação aprofundada |
| `tests/` | Testes (API, orquestrador, agente, normalizador, intents) |

---

## 3. API (resumo)

Aplicação: `api/app.py` (CORS para o Vite em `localhost:5173`).

Rotas típicas de simulação (ver `api/routes/simulation.py`):

- `GET /api/health` — saúde da API
- `GET /api/defaults` — premissas padrão
- `GET /api/historical-dre` — séries históricas para o dashboard
- `POST /api/simulate` — executa `run_simulation` e devolve resultado consolidado + DCF

**Agente:**

- `POST /api/agent/query` — corpo JSON com `question`, opcionalmente `premissas` e `history` (ver `api/schemas.py`)

Se `AGENT_ENABLED=false` no ambiente, o endpoint do agente responde **503**.

---

## 4. Frontend (resumo)

- Premissas e recálculo no **Dashboard**; o chat do agente usa as **mesmas premissas** quando o cliente as envia no payload da pergunta (senão usa defaults no backend).
- Respostas do assistente em **Markdown**; fórmulas matemáticas via **KaTeX** (`remark-math` / `rehype-katex` no componente de markdown do chat).
- **Artefatos** retornados pela API (`table`, `chart`, `kpi`) são renderizados por `AgentArtifactRenderer` (tabelas + gráficos linha/barra com Recharts).

Variável opcional no build do front: `VITE_AGENT_ENABLED` (ver `frontend/src/utils/constants.ts`).

---

## 5. Analista IA — funcionamento

O agente **não substitui o motor**: ele **lê o resultado** de `run_simulation` (e, quando aplicável, histórico) e produz texto estruturado + artefatos opcionais.

### 5.1 Pipeline (ordem)

Arquivo central: `api/services/agent_orchestrator.py` — função `run_agent_query`.

1. **Simulação sempre atual**  
   `run_simulation(premissas=payload.premissas)` → `resultado_para_json` → objeto JSON do cenário.

2. **Identificação do cenário**  
   `compute_scenario_id` gera um id (hash) para rastreio na resposta e na UI.

3. **Roteamento de intenção**  
   `route_question` em `api/services/agent_intent.py` classifica a pergunta em um `Intent` e preenche `entities` (anos, BU, direção de impacto positivo/negativo, etc.).

4. **Resposta determinística (prioritária)**  
   `execute_deterministic` em `api/services/agent_deterministic.py`: se a intenção tem implementação, devolve `AgentQueryResponse` com `response_source="deterministic"`, números tirados do `sim_json` (ou do bundle histórico).  
   Isso cobre perguntas-alvo comuns (margem consolidada, tabelas, múltiplo EV/EBITDA, etc.) com **menos alucinação** e **latência previsível**.

5. **Caminho OpenAI (se não houve resposta determinística)**  
   Monta **contexto** com `build_agent_context` (`api/services/agent_context.py`): resumo do cenário, métricas derivadas, texto para o modelo.  
   O cliente em `api/services/openai_client.py` pede saída em **JSON** alinhado ao schema.  
   Antes do Pydantic, `normalize_agent_response_dict` (`api/services/agent_output_normalizer.py`) corrige formatos comuns (ex.: `confidence` numérico, listas vindas como string).

6. **Fallback local**  
   Se o LLM falhar ou estiver desligado, resposta genérica orientando reformulação (`response_source="fallback"`).

### 5.2 Intenções (visão geral)

Definidas em `Intent` em `api/services/agent_intent.py`, incluindo por exemplo:

- Impacto na margem EBITDA (consolidado ou ano a ano)
- Série temporal (ex.: AMS faturamento)
- Margem por BU em ano específico
- Comparação de crescimento entre BUs
- Múltiplo EV/EBITDA e explicação EV vs equity
- Tabela métrica × BU × anos
- Participação de receita / mudança de share
- Métrica histórica por BU (2018–2025) vs projeção (2026–2030)
- `generic` — sem match forte; tende a ir para o LLM

Regras especiais: perguntas muito focadas em **uma BU** (ex.: “impacto na margem da FOPM”) podem ser roteadas para `generic` para não devolver automaticamente o **ranking entre todas as BUs**. Palavras como “negativamente” / “positivamente” ajustam filtros quando o intent consolidado ainda se aplica.

### 5.3 Ferramentas numéricas

`api/services/agent_tools.py` concentra funções puras sobre `sim_json`: séries por BU/ano, margens, impacto aproximado na margem consolidada, pivot para tabelas, valuation, etc.  
O caminho determinístico chama essas funções e formata `answer_markdown` e `artifacts`.

### 5.4 Contrato da resposta (`AgentQueryResponse`)

Em `api/schemas.py`:

- `answer_markdown` — texto principal
- `artifacts` — lista de `table` | `chart` | `kpi`
- `confidence` — `high` | `medium` | `low`
- `data_used`, `warnings`
- **Transparência:** `response_source` (`openai` | `deterministic` | `fallback`), `intent`, `scenario_id`, `validation_repaired`

O frontend pode exibir uma linha de rastreio (origem · intent · cenário).

### 5.5 Gráficos e tabelas

- **Determinístico:** alguns fluxos adicionam `ArtifactChart` / `ArtifactTable` quando a pergunta sugere visual (`_wants_visual` no orquestrador: palavras como “gráfico”, “tabela”, “plot”, “visual”).
- **OpenAI:** o prompt orienta a preencher `artifacts` quando o usuário pedir visualização explícita; o JSON precisa respeitar o schema.

### 5.6 Configuração (.env)

Carregado a partir da raiz do projeto em `api/config.py` (via `python-dotenv`):

| Variável | Efeito |
|----------|--------|
| `OPENAI_API_KEY` | Habilita o caminho LLM se presente |
| `OPENAI_MODEL` | Modelo (default `gpt-4.1-mini`) |
| `AGENT_ENABLED` | `false` desliga o endpoint do agente (503) |
| `AGENT_MAX_CONTEXT_TOKENS`, `AGENT_MAX_OUTPUT_TOKENS`, `AGENT_TIMEOUT_SECONDS` | Limites da chamada ao modelo |

### 5.7 Rate limit

`api/services/rate_limit.py` limita frequência de chamadas por IP ao endpoint do agente (evita abuso).

---

## 6. Testes e execução local

- Instalação / dev: ver `Makefile` e [`README.md`](README.md).
- Testes Python: `pytest` ou `make test`.
- Há testes de roteamento de intent, normalizador de saída e smoke do endpoint do agente (`tests/`).

---

## 7. Leitura recomendada

| Documento | Conteúdo |
|-----------|----------|
| [`README.md`](README.md) | Quick start, estrutura resumida, endpoints |
| [`docs/FUNCIONAMENTO_PROJETO.md`](docs/FUNCIONAMENTO_PROJETO.md) | Motor DRE/DCF em profundidade |
| `api/prompts/agent_system_prompt.md` | Instruções de sistema do LLM (se presente) |

---

*Documento alinhado ao desenho atual do repositório (API + agente determinístico + OpenAI opcional).*
