# Plano de Reestruturação do Repositório `artefato_calculadora`

## Contexto

O repositório é uma ferramenta de projeção financeira (DRE) e valuation (DCF) para múltiplas unidades de negócio, com backend Python/FastAPI e frontend React/TypeScript.

Embora funcional, a organização atual apresenta problemas de coesão:
- Arquivos gerados estão versionados no git
- Todos os módulos BU dependem de `fopm.py` para utilitários compartilhados via hack de `sys.path`
- Não há tooling de desenvolvimento (Makefile, pyproject.toml)
- Não há infraestrutura de testes

**Objetivo:** Organização, coesão e boas práticas sem alterar a lógica de negócio.

---

## Fase 0 — Higiene do Git

**Objetivo:** Parar de rastrear artefatos gerados.

### Tarefas

1. **Atualizar `.gitignore`** — adicionar:
   ```
   projecao_bus/projecoes/
   projecao_bus/dcf_output/
   frontend/dist/
   node_modules/
   __pycache__/
   ```

2. **Remover do índice git** (sem apagar localmente):
   ```bash
   git rm -r --cached projecao_bus/projecoes/
   git rm -r --cached projecao_bus/dcf_output/
   git rm -r --cached frontend/dist/  # se rastreado
   ```

**Arquivos:** `.gitignore`

---

## Fase 1 — Extrair Utilitários Compartilhados de `fopm.py`

**Objetivo:** Eliminar o acoplamento onde 6 módulos dependem de `fopm.py` para constantes/helpers.

### Tarefas

1. **Criar `projecao_bus/shared.py`** — mover de `fopm.py`:
   - `INFLACAO_FOCUS` (dict)
   - `ALIQUOTA_ISV` (float)
   - `_validar_anos()` (função)
   - `salvar_projecao_csv()` (função)

2. **Atualizar imports em 6 módulos** — trocar `from fopm import ...` por `from .shared import ...`:
   - `ams.py`
   - `renovacao.py`
   - `consolidado.py`
   - `administrativa.py`
   - `venda_softwares.py`
   - `data_science.py`
   
   > Para `ams.py`: manter `from .fopm import projetar_dre_fopm_brasil` separado

3. **Limpar `projecao_bus/__init__.py`** — remover hack `sys.path.insert`

**Arquivos:** `projecao_bus/shared.py` (novo), `projecao_bus/__init__.py`, `projecao_bus/fopm.py`, + 6 módulos BU

---

## Fase 2 — Consolidação do Diretório de Dados

**Objetivo:** Unificar `data/` e `data_original/` numa estrutura clara.

### Nova Estrutura

```
data/
├── historico/    ← conteúdo atual de data/
└── original/     ← conteúdo atual de data_original/
```

### Tarefas

- Atualizar referências de path nos módulos Python (`fopm.py` etc.)
- Remover diretório `data_original/` vazio

**Arquivos:** Mover arquivos CSV, atualizar paths em `fopm.py` (e quaisquer outros módulos que leiam CSVs)

---

## Fase 3 — Estrutura de Pacote Python

**Objetivo:** Tornar o projeto instalável e eliminar hacks de path.

### Tarefas

1. **Criar `pyproject.toml`** na raiz com:
   - Dependências core: `pandas`, `numpy`
   - Extras `[api]`: `fastapi`, `uvicorn`
   - Extras `[dev]`: `pytest`, `ruff`, `httpx`
   - Config do ruff e pytest

2. **Remover `requirements-api.txt`** (substituído pelo pyproject.toml)

3. **Remover hack `sys.path` de `api/main.py`** — após `pip install -e .`, imports funcionam nativamente

**Arquivos:** `pyproject.toml` (novo), `requirements-api.txt` (deletar), `api/main.py`

---

## Fase 4 — Organização do Módulo API

**Objetivo:** Preparar a API para crescimento separando responsabilidades.

### Nova Estrutura

```
api/
├── __init__.py
├── app.py          ← factory do FastAPI + CORS
├── schemas.py      ← modelos Pydantic (SimulatePayload, etc.)
└── routes/
    ├── __init__.py
    └── simulation.py   ← endpoints /health, /defaults, /simulate
```

### Tarefas

- Criar `.env.example` na raiz documentando variáveis esperadas

**Arquivos:** `api/main.py` → split em `api/app.py`, `api/schemas.py`, `api/routes/simulation.py`

---

## Fase 5 — Developer Experience

**Objetivo:** Um comando para rodar tudo.

### Tarefas

1. **Criar `Makefile`** na raiz:

   | Comando | Ação |
   |---------|------|
   | `make install` | `pip install -e ".[api,dev]"` + `cd frontend && npm install` |
   | `make dev` | Inicia API + frontend em paralelo |
   | `make test` | `pytest tests/ -v` |
   | `make lint` | `ruff check` + `npm run lint` |
   | `make clean` | Limpa outputs gerados |

2. **Criar `.env.example`** com:
   - `API_HOST`
   - `API_PORT`
   - `VITE_API_URL`

**Arquivos:** `Makefile` (novo), `.env.example` (novo)

---

## Fase 6 — Infraestrutura de Testes (esqueleto)

**Objetivo:** Estabelecer padrão de testes sem exigir cobertura completa imediata.

### Nova Estrutura

```
tests/
├── __init__.py
├── conftest.py           ← fixtures: DataFrames de exemplo, TestClient
├── test_fopm.py          ← teste básico: retorna DataFrame com colunas esperadas
├── test_orchestrator.py  ← teste básico: run_simulation retorna chaves esperadas
└── test_api.py           ← teste básico: /health retorna 200, /simulate retorna JSON válido
```

**Arquivos:** 5 novos arquivos em `tests/`

---

## Fase 7 — README

**Objetivo:** Documentação completa para onboarding.

### Conteúdo

1. Visão geral do projeto
2. Diagrama de arquitetura (texto)
3. Quick start (`make install && make dev`)
4. Estrutura de diretórios atualizada
5. Endpoints da API
6. Módulos de BU
7. Como contribuir (testes, lint)

**Arquivos:** `README.md`

---

## Estrutura Final Proposta

```
artefato_calculadora/
├── .gitignore               (atualizado)
├── .env.example             (novo)
├── pyproject.toml           (novo)
├── Makefile                 (novo)
├── README.md                (reescrito)
│
├── api/
│   ├── __init__.py
│   ├── app.py               (novo — factory + CORS)
│   ├── schemas.py           (novo — Pydantic models)
│   └── routes/
│       ├── __init__.py
│       └── simulation.py    (novo — endpoints)
│
├── data/
│   ├── historico/           (movido de data/)
│   └── original/            (movido de data_original/)
│
├── docs/                    (sem mudança)
│
├── frontend/                (sem mudança interna — já bem organizado)
│   └── src/...
│
├── projecao_bus/
│   ├── __init__.py          (limpo)
│   ├── shared.py            (novo — constantes e helpers compartilhados)
│   ├── orchestrator.py
│   ├── fopm.py, ams.py, renovacao.py, etc.
│   ├── dcf/
│   ├── projecoes/           (gitignored)
│   └── dcf_output/          (gitignored)
│
└── tests/                   (novo)
    ├── conftest.py
    ├── test_fopm.py
    ├── test_orchestrator.py
    └── test_api.py
```

---

## Verificação

Após cada fase, rodar:

1. `pip install -e ".[api,dev]"` (a partir da Fase 3)
2. `python -m projecao_bus.orchestrator` — verificar que projeções rodam sem erro
3. `uvicorn api.app:app` — verificar que API inicia
4. `cd frontend && npm run build` — verificar que frontend compila
5. `pytest tests/ -v` (a partir da Fase 6)

---

## Ordem de Execução Recomendada

| Fase | Risco | Esforço | Impacto |
|:----:|:-----:|:-------:|:--------|
| 0 | Muito baixo | 15 min | **Alto** — limpa git |
| 1 | Médio | 1h | **Alto** — elimina acoplamento central |
| 3 | Médio | 30 min | **Alto** — projeto instalável |
| 2 | Baixo | 30 min | Médio — organização de dados |
| 4 | Baixo | 45 min | Médio — API preparada para crescer |
| 5 | Muito baixo | 30 min | **Alto** — DX |
| 6 | Muito baixo | 45 min | Médio — base para testes |
| 7 | Muito baixo | 30 min | **Alto** — onboarding |
