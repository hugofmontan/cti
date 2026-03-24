# Artefato Calculadora

Ferramenta de projeção financeira (DRE) e valuation (DCF) para múltiplas unidades
de negócio, com backend Python/FastAPI e frontend React/TypeScript.

## Arquitetura (visão textual)

- `frontend`: interface de simulação e visualização de resultados.
- `api`: endpoints HTTP para defaults e simulação consolidada.
- `projecao_bus`: motor de projeções por BU, consolidação e pipeline de DCF.
- `data/historico`: bases históricas usadas como entrada dos cálculos.
- `data/original`: arquivos originais de referência.

Fluxo principal:
`premissas` -> `projeções por BU` -> `consolidado` -> `DCF` -> `resposta JSON`.

## Documentação detalhada

- **[Funcionamento do projeto (aprofundado)](docs/FUNCIONAMENTO_PROJETO.md)** — arquitetura, BUs, consolidado, DCF, API, frontend e dados.

## Quick Start

```bash
make install
make dev
```

No modo desenvolvimento:
- API: `uvicorn api.app:app --reload --host 127.0.0.1 --port 8000`
- Frontend: `cd frontend && npm run dev`

## Estrutura de diretórios

```text
artefato_calculadora/
├── api/
│   ├── app.py
│   ├── schemas.py
│   └── routes/
│       └── simulation.py
├── data/
│   ├── historico/
│   └── original/
├── frontend/
├── projecao_bus/
│   ├── shared.py
│   ├── orchestrator.py
│   ├── fopm.py
│   ├── ams.py
│   ├── renovacao.py
│   ├── venda_softwares.py
│   ├── data_science.py
│   ├── administrativa.py
│   └── consolidado.py
└── tests/
```

## Endpoints da API

- `GET /api/health`: status da API.
- `GET /api/defaults`: premissas padrão da simulação.
- `GET /api/historical-dre`: séries 2018–2025 a partir de `data/original/*.csv` (uso no dashboard).
- `POST /api/simulate`: executa projeções + consolidado + DCF.

Exemplo de payload:

```json
{
  "premissas": {
    "renovacao": { "churn": 0.05 },
    "ams": { "taxa_conversao_fopm": 0.1 }
  }
}
```

## Módulos de BU

- `fopm`: base operacional principal.
- `renovacao`: receita recorrente com reajuste e churn opcional.
- `ams`: dependente de FOPM para incremental.
- `venda_softwares`: crescimento nominal por inflação + fator real.
- `data_science`: projeção por número de projetos/capacidade.
- `administrativa`: centro de custo para rateio interno.
- `consolidado`: soma operacional e linhas financeiras do grupo.

## Como contribuir

- Rodar testes: `make test`
- Rodar lint: `make lint`
- Validar projeções: `python -m projecao_bus.orchestrator`

