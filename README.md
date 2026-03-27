# Calculadora financeira — DRE, consolidado e DCF

Aplicação **full-stack** para **projetar Demonstrações de Resultado (DRE)** por unidade de negócio (FOPM, Renovação, AMS, Venda de Softwares, Data Science, Administrativa), **consolidar** e rodar um **valuation por fluxo de caixa descontado (DCF)**. Inclui **API REST** em Python, **interface web** em React e, opcionalmente, um **agente conversacional** (OpenAI) que consulta o mesmo motor.

**Execução rápida** (após clonar): configure `.env` → instale Python (`requirements.txt`) e Node → `uvicorn` + `npm run dev`. Detalhes abaixo.

---

## O que a aplicação faz (visão de conjunto)

| Camada | Papel |
|--------|--------|
| **`projecao_bus/`** | Motor numérico: premissas (macro, headcount, DCF…), projeção ano a ano por BU, consolidado, balanço/fluxo e valuation. Os dados históricos vêm de CSVs em `data/`. |
| **`api/`** | Expõe o motor via HTTP: premissas padrão, histórico, simulação, upload de novos CSVs, reset. O agente chama internamente `run_simulation` e outras operações. |
| **`frontend/`** | Painel para editar premissas, rodar a simulação, ver gráficos, DRE, BP, exportar relatório/PDF e (se habilitado) conversar com o agente. |
| **`data/`** | CSVs de histórico e cenário base (**devem ser versionados no Git**). Ver secção abaixo. |

### Dados históricos no repositório

O projeto **não funciona sem** os arquivos em `data/`. Eles **precisam ser commitados** junto com o código para qualquer pessoa clonar e executar na hora:

| Pasta | Conteúdo (exemplos) |
|-------|----------------------|
| **`data/original/`** | DRE por BU e consolidado no formato pivot (`dre_*_original.csv`, `consolidado_original.csv`) — base padrão da simulação. |
| **`data/historico/`** | Balanço patrimonial, headcount por BU, DREs históricos auxiliares usados pelo motor e pelos gráficos. |
| **`data/test_uploads/`** | Cenários de teste (ex.: `2026_ficticio/`) usados por scripts e validações. |

Somente **`data/uploads/active/`** fica no `.gitignore`: é ali que a API grava CSVs quando alguém usa **“upload de histórico”** no painel; isso é estado local/ephemeral. O comando **`POST /api/reset-historical`** remove essa pasta e volta a ler de `data/original/`.

**Checklist para entrega / fork:** conferir no Git que `data/original/` e `data/historico/` (e fixtures necessárias) estão rastreados (`git status` não pode omitir esses arquivos).

Fluxo típico no navegador: carregar histórico → ajustar premissas → **Simular** → inspecionar consolidado, FCFF e múltiplos → exportar. Tudo isso repete o mesmo pipeline que a API usa em `POST /api/simulate`.

Referências: [PROJETO.md](PROJETO.md) (detalhe funcional), [docs/ARCHITECTURE_AND_SOURCES.md](docs/ARCHITECTURE_AND_SOURCES.md) (código), [AGENT.md](AGENT.md) (agente e limitações).

---

## Pré-requisitos

- **Python 3.10+**
- **Node.js 18+** (npm)
- **Git**

---

## 1. Clonar e ambiente virtual (recomendado)

```bash
git clone <url-do-repositório>
cd artefato_calculadora
python -m venv .venv
```

Ative o venv:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Linux/macOS:** `source .venv/bin/activate`

---

## 2. Dependências Python — `requirements.txt`

Na **raiz** do repositório:

```bash
pip install -r requirements.txt
pip install -e . --no-deps
```

- O primeiro comando instala **pandas, numpy, FastAPI, Uvicorn, OpenAI SDK, python-dotenv** (equivalente ao que está em [pyproject.toml](pyproject.toml) para rodar API + motor).
- O segundo registra o pacote **`artefato-calculadora`** em modo editável para os imports `projecao_bus` e `api` funcionarem a partir da raiz.

**Alternativa** (equivalente, usando só o pyproject):

```bash
pip install -e ".[api]"
```

**Desenvolvimento / testes** — inclui pytest, ruff e httpx:

```bash
pip install -r requirements-dev.txt
pip install -e . --no-deps
```

Ou: `pip install -e ".[api,dev]"`.

---

## 3. Dependências do frontend

```bash
cd frontend
npm install
cd ..
```

---

## 4. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`. Para o **dashboard e a API de simulação**, nada é obrigatório. Para o **agente**, use `OPENAI_API_KEY`. Ver [`.env.example`](.env.example) e [AGENT.md](AGENT.md).

---

## 5. Subir a aplicação

Dois terminais na **raiz** do repo (com venv ativo, se usar):

**API**

```bash
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```bash
cd frontend && npm run dev
```

- **Interface:** http://localhost:5173  
- **API:** http://127.0.0.1:8000 — documentação: http://127.0.0.1:8000/docs  
- O Vite encaminha `/api` para a porta 8000.

---

## Arquivos de requisitos (resumo)

| Arquivo | Uso |
|---------|-----|
| [requirements.txt](requirements.txt) | Execução: motor + API |
| [requirements-dev.txt](requirements-dev.txt) | Testes e lint Python (`pytest`, `ruff`, `httpx`) |
| [frontend/package.json](frontend/package.json) | Dependências do React / Vite |

---

## Comandos úteis

| Objetivo | Comando (na raiz) |
|----------|-------------------|
| Testes Python | `pytest tests/ -v` |
| Lint Python | `ruff check .` |
| Atalhos Make | `make install`, `make test`, `make lint` (se tiver Make) |

---

## Endpoints principais

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/defaults` | Premissas padrão |
| GET | `/api/historical-dre` | Histórico (CSVs) |
| POST | `/api/simulate` | Simulação completa + DCF |
| POST | `/api/upload-historical` | Novos CSVs |
| POST | `/api/reset-historical` | Volta ao `data/original` |
| POST | `/api/agent/query` | Agente (requer chave OpenAI) |

---

## Estrutura do repositório

`projecao_bus/` · `api/` · `frontend/` · **`data/` (histórico versionado)** · `tests/` · `scripts/` · `docs/` · **AGENT.md**

---

## Problemas comuns

- **ImportError em `projecao_bus`:** rode `pip install -e . --no-deps` após `pip install -r requirements.txt`.
- **Frontend sem dados / histórico vazio:** confira se a API está na porta **8000** e se **`data/original/`** e **`data/historico/`** existem no clone (foram commitados). Rode `POST /api/reset-historical` se tiver sobrado só pasta de upload ativo quebrada.
- **Agente 503 / erros:** [AGENT.md](AGENT.md).

---

## Licença / uso acadêmico

Entregável acadêmico: cite a fonte se reutilizar o trabalho e cumpra as políticas da instituição e da OpenAI ao usar o agente.
