# Arquitetura e fontes de verdade

Este documento apoia a refatoração incremental do repositório: mapa de pastas, contratos públicos e onde cada premissa vive.

## Mapa de pastas — atual (resumo)

| Pacote / pasta | Papel |
|---------------|--------|
| `projecao_bus/` | Motor: BUs na raiz (`ams.py`, `fopm.py`, …), `orchestrator.py`, `context.py`, `year_config.py` |
| `projecao_bus/dcf/` | BP, NCG, fluxo, valuation, constantes de balanço e DCF |
| `projecao_bus/premissas/` | Defaults de macro, FOPM, DS e gabaritos operacionais |
| `projecao_bus/io/`, `projecao_bus/drivers/` | CSV, drivers FOPM |
| `api/` | FastAPI: `routes/`, `services/`, `schemas.py`, `config.py` |
| `frontend/src/` | React: `components/`, `hooks/`, `utils/`, `types/` |
| `tests/` | Regressão (`test_motor_regression.py`), BUs, API, agente |
| `data/` | `original/` e `historico/` **versionados no Git**; `uploads/active/` apenas runtime (gitignored); fixtures em `test_uploads/` quando existirem |
| `scripts/` | Automação (ex.: geração de CSVs fictícios) |

## Mapa alvo (evolutivo)

| Camada | Destino típico |
|--------|----------------|
| Domínio (cálculo) | `projecao_bus/domain/bu/*`, DCF permanece em `dcf/` ou espelho em `domain/dcf/` |
| Aplicação (orquestração) | `projecao_bus/application/` (`context`, `orchestrator`) |
| Infra (I/O, paths) | `projecao_bus/infrastructure/` (`paths`, carregamento de histórico) |
| Config | `projecao_bus/config/` (`year_config`) |

Módulos na raiz de `projecao_bus/` podem permanecer como **facades** que reexportam símbolos, preservando imports existentes (`from projecao_bus.orchestrator import run_simulation`).

## Fontes de verdade (um conceito → um lugar)

| Conceito | Fonte principal |
|----------|-----------------|
| Anos histórico vs projetado | `projecao_bus/config/year_config.py` (exposta como `projecao_bus.year_config`) |
| Inflação/Selic Focus, HC FOPM/DS, RL consolidada ref., honorários CFP | `projecao_bus/premissas/defaults.py` |
| Parâmetros de projeção AMS | `projecao_bus/premissas/ams_params.py` |
| Parâmetros Renovação / Venda SW / Data Science | `projecao_bus/premissas/renovacao_params.py`, `venda_sw_params.py`, `data_science_params.py` |
| NCG, WACC, g, rácios de balanço DCF | `projecao_bus/dcf/constants.py` |
| Rácio fornecedores (balanço) vs série gabarito custos excl. | `dcf.constants`: `RATIO_FORNECEDORES` e `RATIO_FORNECEDORES_CUSTOS_EXCL_GABARITO` |
| Drivers FOPM (ratios, ticket) | `projecao_bus/drivers/fopm.py` + CSV |
| Mapeamento CSV DRE/BP → chaves JSON | `infrastructure/historical_dre.py` (facade: `historical_dre`) |
| Paths repo / dados / uploads | `projecao_bus/infrastructure/paths.py` |
| Env API (OpenAI, CORS, agente) | `api/config.py` (`Settings`) |
| Schemas HTTP e artefatos (contrato front) | `api/schemas.py` |

## Duplicatas conhecidas (drift evitado)

- Anos 2026–2030 e labels de BU: alinhar frontend (`YearConfigContext`, resposta da API) com `year_config`; evitar listas literais só em `constants.ts` ou `agent_context_builder`.
- Anos projetados na API do agente: `api/services/projection_config.get_projection_years()` (espelha `year_config`). No frontend, preferir `YearConfigContext` / payload de simulação; `utils/constants.YEARS` permanece fallback de UI.

## Superfície pública estável (motor)

Consumidores externos devem preferir:

- `projecao_bus.orchestrator.run_simulation`, `resultado_para_json`, `premissas_padrao`, `resolve_base_values`
- `projecao_bus.year_config`: `YearConfig`, `get_active_year_config`, `set_active_year_config`, `reset_year_config`
- `projecao_bus.context`: `SimulationContext`, `build_simulation_context`, `default_simulation_context`
- `projecao_bus.historical_dre`: `load_historical_dre_bundle` e séries

Constantes de BU expostas para orchestrator/premissas (ex.: `RATIO_INCREMENTAL_FOPM`, `SPREAD_REAJUSTE_RENOVACAO`) permanecem reexportadas pelos módulos de BU na raiz.

## Superfície pública API

- Rotas sob `/api/*` conforme README.
- Modelos Pydantic em `api/schemas.py` — o frontend depende dos tipos de artefatos; mudanças exigem plano de migração.

## Validação

- `make test` — inclui golden DCF em `tests/test_motor_regression.py`.
- `make lint` — Ruff (Python) e lint do frontend.
