# Plano de Implementação — Consolidado

## Contexto

Este documento especifica como construir a DRE Consolidada de 2026 a 2030 a partir
das DREs individuais de cada BU já projetadas.

O Consolidado não tem lógica de negócio própria — é quase inteiramente uma agregação.
As únicas exceções são três linhas calculadas fora das BUs:
**D&A consolidada**, **Receita Financeira** e **Despesa Financeira**,
que dependem de inputs externos (caixa projetado, SELIC Focus).

---

## Posição no orquestrador

O Consolidado deve ser calculado **depois de todas as BUs**, incluindo a Administrativa:

```
1. FOPM Brasil
2. Renovação
3. AMS              ← depende do FB FOPM
4. Venda Softwares
5. Data Science
6. Administrativa   ← depende de RL e headcount consolidados
7. Reprojetar BUs com rateio correto
8. CONSOLIDADO      ← soma tudo + calcula D&A, Rec/Desp Fin, LAIR, IRPJ, LL
```

---

## Estrutura do Consolidado

O Consolidado tem **duas partes distintas**:

### Parte 1 — DRE Consolidada (linhas de negócio)
Soma linha a linha das BUs operacionais, com tratamentos específicos por linha.

### Parte 2 — Linhas calculadas abaixo do EBITDA
D&A, Resultado Financeiro, LAIR, IRPJ e Lucro Líquido — calculados com inputs
externos que não existem dentro das BUs individuais.

---

## Parte 1 — Agregação linha a linha

### Regra geral

```
Consolidado(linha, t) = soma de todas as BUs operacionais para aquela linha no ano t
```

BUs incluídas: FOPM Brasil, Renovação, AMS, Venda Softwares, Data Science.

**A Administrativa NÃO entra na soma** das linhas operacionais — ela é um
centro de custo interno e seu resultado já está distribuído via Rateio ADM.

### Tratamento do Rateio ADM

O rateio é uma transferência interna: cada BU operacional recebe um débito
(rateio_adm positivo que reduz EBITDA), e a ADM registra o crédito equivalente
(rateio negativo que reduz suas despesas). Ao consolidar, os dois se cancelam.

```
Rateio_Consolidado = 0  (cancela internamente — não some na DRE consolidada)
```

### Linha a linha

| Linha consolidada          | Origem                                                       |
|----------------------------|--------------------------------------------------------------|
| Receita Bruta              | Soma dos FB de todas as BUs operacionais                     |
| (−) Deduções               | Soma dos ISV de todas as BUs operacionais                    |
| Receita Líquida            | Soma das RL de todas as BUs operacionais                     |
| Incentivos e Prospecção    | Soma dos Incentivos de todas as BUs                          |
| Gastos com Pessoal         | Soma dos Gastos Pessoal de todas as BUs                      |
| Outras Despesas Diretas    | Soma das Outras Dir. de todas as BUs                         |
| Lucro Bruto (MC I)         | RL − Custos Operacionais (= soma dos MC I das BUs)           |
| Remuneração Direta Sócios  | Soma das Rem. Sócios de todas as BUs                         |
| EBITDA antes das ADM (MC II)| Soma dos MC II das BUs                                      |
| Outras Despesas ADM        | Soma das Outras ADM de todas as BUs operacionais             |
| Rateio Administrativo      | **Zero** (cancela internamente)                              |
| Honorários ADM Sócios      | Soma dos Honorários de todas as BUs operacionais             |
| Honorários ADM (Rateio)    | **Zero nas projeções** (absorvido pela ADM)                  |
| **EBITDA**                 | Soma dos EBITDAs de todas as BUs operacionais                |

### Valores de referência (gabarito parcial)

| Linha           | 2026        | 2027        | 2028        | 2029        | 2030        |
|-----------------|-------------|-------------|-------------|-------------|-------------|
| Receita Bruta   | 55.705.600  | 60.689.070  | 66.021.045  | 71.512.336  | 79.942.892  |
| Receita Líquida | 46.939.343  | 51.109.974  | 55.569.432  | 60.162.741  | 67.191.035  |
| EBITDA          | 14.879.223  | 16.016.893  | 17.400.387  | 18.351.496  | 20.769.756  |

---

## Parte 2 — Linhas calculadas abaixo do EBITDA

### D&A Consolidada

A D&A consolidada é calculada como a diferença entre a D&A da AMS
(única BU com ativos depreciáveis) e a amortização de ágios registrada
no CONS. FORMATO PARCEIRO:

```
D&A_Consolidada(t) = D&A_AMS(t) − |Amortização_CFP(t)|
```

Onde `Amortização_CFP` é o valor da linha D&A do CONS. FORMATO PARCEIRO,
que tem **sinal negativo** (é amortização de ágios que reduz custo, não
depreciação normal). Ao subtrair o valor absoluto da amortização da D&A
da AMS, obtém-se a D&A líquida que entra no Consolidado.

Confirmação:

| Ano  | D&A AMS    | Amort. CFP  | D&A Consolidada |
|------|-----------|------------|----------------|
| 2026 | 270.677   | −189.520   | **81.157**      |
| 2027 | 276.189   | −178.575   | **97.614**      |
| 2028 | 282.034   | −170.519   | **111.516**     |
| 2029 | 287.762   | −151.534   | **136.228**     |
| 2030 | 294.784   | −139.244   | **155.539**     |

A amortização do CFP decresce em cascata — não há regra simples para
derivá-la. Para a implementação, usar os valores fixos da planilha acima.

```
EBIT(t) = EBITDA(t) − D&A_Consolidada(t)
```

| Ano  | EBIT        |
|------|------------|
| 2026 | 14.798.066 |
| 2027 | 15.919.279 |
| 2028 | 17.288.871 |
| 2029 | 18.215.267 |
| 2030 | 20.614.217 |

---

### Receita Financeira

```
Rec_Financeira(t) = Caixa(t-1) × Rendimento_SELIC(t)
Rendimento_SELIC(t) = SELIC_Focus(t) × 0,95
```

O caixa do ano anterior rende a SELIC com desconto de 5% (spread de
gestão de tesouraria). A fórmula foi confirmada centavo a centavo:
`8.018.000 × (12,13% × 0,95) = 923.954` ✓

**Inputs necessários:**

| Ano  | SELIC Focus | Rendimento | Caixa base | Rec. Financeira |
|------|------------|-----------|-----------|----------------|
| 2026 | 12,13%     | 11,524%   | 8.018.000 (2025) | 923.954    |
| 2027 | 10,50%     | 9,975%    | 14.760.212 (2026)| 1.472.331  |
| 2028 | 10,00%     | 9,500%    | 20.976.552 (2027)| 1.992.772  |
| 2029 | 9,50%      | 9,025%    | 27.549.804 (2028)| 2.486.370  |
| 2030 | 10,00%     | 9,500%    | 34.306.757 (2029)| 3.259.142  |

O caixa projetado de cada ano é calculado na mesma etapa (ver seção Caixa).

---

### Despesa Financeira

```
Desp_Financeira = 95.333,33  (fixo — média de 2022, 2023 e 2024)
```

Composição: Consultores R$ 38.667 + Serviços (AMS) R$ 56.667.
Mantida constante para toda a projeção.

---

### LAIR

```
LAIR(t) = EBIT(t) + Rec_Financeira(t) − Desp_Financeira(t)
```

| Ano  | LAIR        |
|------|------------|
| 2026 | 15.897.364 |
| 2027 | 17.572.466 |
| 2028 | 19.468.344 |
| 2029 | 20.894.066 |
| 2030 | 24.072.809 |

---

### IRPJ / CSLL

```
IRPJ_CSLL(t) = LAIR_AMS(t) × 34%
```

A única BU com tributação efetiva é a AMS (Lucro Real, 34%). As demais BUs
operam em Lucro Presumido com alíquota zero na DRE de BU. O IRPJ do
consolidado é **idêntico ao IRPJ da AMS**.

| Ano  | IRPJ/CSLL  |
|------|-----------|
| 2026 | 1.215.656 |
| 2027 | 1.307.853 |
| 2028 | 1.398.948 |
| 2029 | 1.511.030 |
| 2030 | 1.619.312 |

---

### Lucro Líquido

```
Lucro_Liquido(t) = LAIR(t) − IRPJ_CSLL(t)
```

| Ano  | Lucro Líquido |
|------|--------------|
| 2026 | 14.681.707   |
| 2027 | 16.264.612   |
| 2028 | 18.069.396   |
| 2029 | 19.383.036   |
| 2030 | 22.453.497   |

---

## Caixa Projetado

O caixa é necessário para calcular a Receita Financeira do ano seguinte.
A planilha projeta o caixa na linha 54 do CONSOLIDADO.

```
Caixa(t) = Caixa(t-1) + Lucro_Liquido(t) − Participações(t)
```

Onde `Participações` é a distribuição aos sócios/acionistas.

**Participações projetadas:**

```
Participações(t) = Lucro_Liquido(t) × ratio_participações
ratio = média 2022–2025 ≈ 4,78%
```

O ratio de participações (linha 47 do CONSOLIDADO) é a média histórica
de 2022 a 2025, congelado nas projeções em **4,7806%**.

| Ano  | Caixa        |
|------|-------------|
| 2025 | 8.018.000   |
| 2026 | 14.760.212  |
| 2027 | 20.976.552  |
| 2028 | 27.549.804  |
| 2029 | 34.306.757  |
| 2030 | 41.555.091  |

---

## Output esperado

Colunas do DataFrame resultado:

```
ano,
receita_bruta, deducoes, receita_liquida,
incentivos, gastos_pessoal, outras_desp_diretas,
mc1, mc1_pct_rl,
remuneracao_socios,
mc2, mc2_pct_rl,
outras_desp_adm, honorarios_adm,
ebitda, ebitda_pct_rl,
da_consolidada,
ebit,
receita_financeira, despesa_financeira,
lair,
irpj_csll,
lucro_liquido, lucro_liquido_pct_rl,
participacoes,
caixa
```

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

| Linha            | 2026       | 2027       | 2028       | 2029       | 2030       |
|------------------|------------|------------|------------|------------|------------|
| Receita Bruta    | 55.705.600 | 60.689.070 | 66.021.045 | 71.512.336 | 79.942.892 |
| Receita Líquida  | 46.939.343 | 51.109.974 | 55.569.432 | 60.162.741 | 67.191.035 |
| EBITDA           | 14.879.223 | 16.016.893 | 17.400.387 | 18.351.496 | 20.769.756 |
| D&A              | 81.157     | 97.614     | 111.516    | 136.228    | 155.539    |
| EBIT             | 14.798.066 | 15.919.279 | 17.288.871 | 18.215.267 | 20.614.217 |
| Rec. Financeira  | 923.954    | 1.472.331  | 1.992.772  | 2.486.370  | 3.259.142  |
| Desp. Financeira | 95.333     | 95.333     | 95.333     | 95.333     | 95.333     |
| LAIR             | 15.897.364 | 17.572.466 | 19.468.344 | 20.894.066 | 24.072.809 |
| IRPJ/CSLL        | 1.215.656  | 1.307.853  | 1.398.948  | 1.511.030  | 1.619.312  |
| Lucro Líquido    | 14.681.707 | 16.264.612 | 18.069.396 | 19.383.036 | 22.453.497 |
| Caixa            | 14.760.212 | 20.976.552 | 27.549.804 | 34.306.757 | 41.555.091 |

---

## Diagnóstico de desvios

Se o EBITDA divergir → alguma BU individual está com valor errado. Comparar
o EBITDA de cada BU com o gabarito individual antes de consolidar.

Se o EBIT divergir → checar D&A consolidada. Ela não é a soma das D&As das BUs:
é `D&A_AMS − |Amortização_CFP|`. Usar os valores fixos da tabela acima.

Se a Receita Financeira divergir → confirmar que o rendimento usa
`SELIC_Focus × 0,95` aplicado sobre o **caixa do ano anterior**
(não do ano corrente).

Se o IRPJ divergir → confirmar que é o IRPJ da AMS (34% × LAIR_AMS).
Nenhuma outra BU contribui para o IRPJ consolidado.

Se o Lucro Líquido bater mas o Caixa divergir → verificar o ratio de
participações (4,7806% do LL).

---

## Armadilhas conhecidas

**O Rateio ADM some na consolidação.** Cada BU operacional tem um débito de
rateio que reduz seu EBITDA. Na soma consolidada, esse débito e o crédito
correspondente da ADM se cancelam. Incluir o rateio na soma daria EBITDA
consolidado menor do que deveria.

**A D&A consolidada não é a soma das D&As das BUs.** A AMS tem D&A própria
de R$ 270.677, mas o consolidado usa apenas R$ 81.157. A diferença é
absorvida pela amortização de ágios do CONS. FORMATO PARCEIRO, que tem sinal
negativo. A fórmula correta é `D&A_AMS − |Amortização_CFP|`.

**A Receita Financeira usa o caixa do ano anterior.** Para calcular a Rec.
Fin. de 2026, usa-se o caixa de 2025 (R$ 8.018.000), não o caixa de 2026.
Isso cria uma dependência sequencial: o caixa precisa ser calculado antes
da Rec. Fin. do ano seguinte.

**A Despesa Financeira é fixa.** R$ 95.333 em todos os anos — não cresce
com inflação nem com o caixa. É a média histórica de 2022–2024 congelada.

**A Administrativa não entra na soma.** Apesar de existir como BU no modelo,
seu resultado já está distribuído às BUs operacionais via rateio. Somar
a ADM ao consolidado duplicaria o custo administrativo.
