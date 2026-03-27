# Agente analista (LLM + motor financeiro)

Este documento descreve, de forma direta, **o que o agente faz**, **como se integra ao projeto** e **onde estão os limites reais** — útil para quem vai apresentar o trabalho ou dar manutenção.

## O que é

O “agente” é uma camada em **FastAPI** que:

1. Recebe uma pergunta em linguagem natural (e opcionalmente premissas já editadas no frontend).
2. Executa o **mesmo motor** de projeção (`projecao_bus`: DRE por BU → consolidado → DCF) quando necessário.
3. Usa a **API da OpenAI** com *function calling*: o modelo decide chamar *tools* que rodam simulações, consultam dados ou montam artefatos (tabelas, gráficos).

Não é um modelo treinado em cima dos seus CSVs: é um **GPT (ou compatível)** orientado por prompts e por esquemas de ferramentas definidos em código.

## Fluxo técnico (resumido)

```text
Frontend (aba Agente)  →  POST /api/agent/query
                              ↓
                     agent_orchestrator.run_agent_query
                              ↓
              Contexto compacto (métricas + premissas + domain_reference)
                              ↓
                     OpenAIClient (chat + tools em loop)
                              ↓
              execute_tool → run_simulation, query_data, build_artifact, ...
                              ↓
                     Resposta: texto + artifacts (JSON para a UI)
```

Arquivos principais:

| Papel | Caminho |
|--------|---------|
| Rota HTTP | `api/routes/agent.py` |
| Orquestração | `api/services/agent_orchestrator.py` |
| Definição das tools | `api/services/agent_tools.py` |
| Contexto para o LLM | `api/services/agent_context_builder.py` |
| Domínio (BU, ranges, prompts) | `api/agent_domain.py` |
| Prompts em texto | `api/prompts/*.md` |
| Anos projetados no agente | `api/services/projection_config.py` (alinhado ao `year_config` do motor) |

## Configuração

Na **raiz do repositório**, arquivo `.env` (veja [`.env.example`](.env.example)):

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | **Sim**, para usar o agente | Chave da OpenAI |
| `OPENAI_MODEL` | Não | Padrão: `gpt-4.1-mini` |
| `AGENT_ENABLED` | Não | `true`/`false` (padrão `true`). Se `false`, `/api/agent/query` responde **503** |
| `AGENT_MAX_CONTEXT_TOKENS` | Não | Limite de contexto enviado ao modelo |
| `AGENT_MAX_OUTPUT_TOKENS` | Não | Limite da resposta |
| `AGENT_TIMEOUT_SECONDS` | Não | Timeout da chamada ao modelo |
| `CORS_ALLOW_ORIGINS` | Não | Lista separada por vírgulas |

Na **UI**, a aba do agente pode ser escondida com variável Vite (arquivo `frontend/.env` ou `frontend/.env.local`):

```env
VITE_AGENT_ENABLED=false
```

Isso só afeta o frontend; a API ainda expõe o endpoint se `AGENT_ENABLED` estiver `true`.

## Ferramentas expostas ao modelo (visão geral)

Definidas em `AGENT_TOOLS` em `api/services/agent_tools.py`:

1. **run_simulation** — roda cenário alternativo alterando premissas (dot-notation: `renovacao.churn`, `dcf.wacc`, etc.).
2. **compare_scenarios** — compara dois cenários (IDs derivados do hash das premissas efetivas).
3. **get_sensitivity_matrix** — matriz tipo WACC × g (ou outros parâmetros suportados).
4. **query_data** — leitura de dados da simulação atual ou do histórico carregado.
5. **build_artifact** — gera estruturas para tabelas/gráficos/KPIs consumidos pelo renderer do frontend.
6. **get_sankey_data** — dados agregados para Sankey da DRE.

O modelo **não** executa código arbitrário: só essas funções, com parâmetros validados pelo esquema da tool.

## Exemplos de prompts (português)

Funcionam melhor quando já existe uma simulação base carregada no painel (premissas + “Simular”).

- **Cenário único:**  
  *“Simule um cenário com churn da Renovação em 20% e mostre o enterprise value.”*

- **Dois parâmetros:**  
  *“E se o WACC subir para 18% e o g da perpetuidade for 2%?”*

- **Comparação:**  
  *“Compara o cenário atual com o cenário em que a taxa de conversão AMS é 15%.”*  
  (O modelo precisa ter rodado o segundo cenário antes, ou pedir que rode.)

- **Dado pontual:**  
  *“Qual foi o EBITDA consolidado em 2028 no cenário atual?”*

- **Sensibilidade:**  
  *“Monta uma sensibilidade de enterprise value variando WACC de 12% a 20% e g de 2% a 4%.”*

Formule pedidos **específicos** (BU, ano, métrica). Perguntas muito vagas tendem a respostas genéricas ou a mais chamadas de tool.

## O que funciona bem

- Perguntas ligadas às **premissas e métricas** que o motor já calcula (RL, EBITDA, FCFF, EV, etc.).
- **Cenários “e se”** com alterações claras em churn, WACC, g, headcount, etc.
- Uso conjunto com o **dashboard**: o agente reutiliza o JSON da simulação quando enviado no payload.

## Limitações (importante ser transparente)

1. **Dependência externa** — sem `OPENAI_API_KEY` válida, o agente não operacionaliza (erro ou resposta vazia conforme tratamento).
2. **Custo e latência** — cada conversa pode implicar várias chamadas ao modelo + execuções do motor; há **rate limit** simples por IP em `api/services/rate_limit.py`.
3. **Timeouts** — `AGENT_TIMEOUT_SECONDS` pode cortar respostas longas ou loops com muitas tools.
4. **Alucinação / interpretação** — o texto explicativo pode ser impreciso mesmo com números corretos vindos das tools; **valide números críticos** na UI ou via `POST /api/simulate`.
5. **Escopo** — o agente não “aprende” com novos PDFs ou planilhas não carregadas pelo fluxo oficial (`data/` + upload); conhecimento extra é só o que estiver no prompt + contexto JSON limitado.
6. **Dissertative mode** — modo mais narrativo (flag no payload) pode gerar respostas mais longas e menos estruturadas.

## Endpoints

- `POST /api/agent/query` — corpo: `question`, `premissas` (opcional), `history`, etc. (ver `api/schemas.py` → `AgentQueryPayload`).

Com agente desligado: **503** com mensagem de configuração.

## Leitura adicional

- [docs/FUNCIONAMENTO_AGENTE.md](docs/FUNCIONAMENTO_AGENTE.md) — ponte para código e prompts.
- [docs/ARCHITECTURE_AND_SOURCES.md](docs/ARCHITECTURE_AND_SOURCES.md) — fontes de verdade do motor e da API.
