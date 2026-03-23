# Plano de Implementação — Projeção DRE Administrativa

## Contexto

Este documento especifica a lógica de projeção da BU Administrativa de 2026 a 2030,
replicando linha a linha a aba `DRE ADMINISTRATIVA` da planilha
`S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`.

A Administrativa é fundamentalmente diferente de todas as demais BUs:
não gera receita, não tem faturamento, e seu resultado é **sempre negativo** nas
projeções — é um centro de custo puro. Sua função no modelo é dupla:

1. **Calcular as Outras Despesas ADM totais**, que crescem com a receita consolidada.
2. **Distribuir o Rateio ADM entre as BUs operacionais**, que cresce apenas pela inflação.

Esses dois valores são **distintos e calculados por mecanismos separados**,
gerando um déficit residual que aparece como EBITDA negativo da ADM.

---

## Posição no orquestrador

A ADM **depende das demais BUs** e deve ser calculada depois delas:

```
Ordem de execução:
  1. FOPM Brasil      ← sem dependências externas
  2. Renovação        ← sem dependências externas
  3. AMS              ← depende do FB FOPM
  4. Venda Softwares  ← sem dependências externas
  5. Data Science     ← sem dependências externas
  6. ADMINISTRATIVA   ← depende da RL e headcount consolidados de 1-5
  7. Distribuir rateio às BUs operacionais
  8. Reprojetar BUs com rateio correto
```

---

## Arquivos envolvidos

```
projecao_bus/
├── fopm.py                      ← adicionar projetar_administrativa() aqui
└── projecoes/
    └── projecao_administrativa.csv ← gerado pela execução
```

A ADM não tem CSV histórico próprio como input — seus dois drivers
(RL Consolidada e Rateio base) são derivados das outras BUs ou da planilha.

---

## Dois mecanismos distintos

### Mecanismo 1 — Outras Despesas ADM (custo real da ADM)

```
Outras_ADM(t) = RL_Consolidada(t) × 12,4158%
```

Onde `RL_Consolidada(t)` é a **soma das Receitas Líquidas de todas as BUs
operacionais** no ano `t`: FOPM + Renovação + AMS + Venda Softwares + Data Science.

O ratio **12,4158%** é declarado diretamente na planilha (linha 76) como valor fixo
para toda a projeção. Não é possível derivá-lo de forma limpa a partir dos três anos
históricos — a planilha apresenta um bug interno de referência na seção de premissas
(a coluna de 2024 exibe o mesmo valor que 2025). O valor correto para implementação
é `0.12415802928103117`, confirmado por reproduzir os cinco anos projetados com
diferença zero centavo a centavo.

| Ano  | RL Consolidada (ref.) | Outras ADM       |
|------|----------------------|-----------------|
| 2026 | 46.939.343           | 5.827.896        |
| 2027 | 51.109.974           | 6.345.714        |
| 2028 | 55.569.432           | 6.899.391        |
| 2029 | 60.162.741           | 7.469.687        |
| 2030 | 67.191.035           | 8.342.307        |

### Mecanismo 2 — Rateio ADM (valor repassado às BUs)

```
Rateio_Total(t) = Rateio_Total(t-1) × (1 + inflação(t))
```

O Rateio **não cresce com a receita consolidada** — cresce apenas pela inflação,
em cascata sobre o valor de 2025.

Base: `Rateio_2025 = 5.047.539,09`

| Ano  | Inflação | Rateio Total |
|------|---------|-------------|
| 2026 | 3,97%   | 5.247.926   |
| 2027 | 3,80%   | 5.447.348   |
| 2028 | 3,50%   | 5.638.005   |
| 2029 | 3,50%   | 5.835.335   |
| 2030 | 3,50%   | 6.039.572   |

**Por que Outras ADM ≠ Rateio?** Porque as Outras ADM crescem com a receita
consolidada (que cresce mais rápido que a inflação), enquanto o Rateio cresce
apenas pela inflação. A diferença entre os dois é o déficit residual da ADM —
o custo que não é repassado às BUs e aparece como EBITDA negativo.

---

## Distribuição do Rateio por BU

```
Rateio_BU(t) = Rateio_Total(t) × (N.Func_BU(t) / Total_Func(t))
```

Onde `Total_Func(t)` é a **soma do headcount de todas as BUs operacionais**
(sem contar os funcionários da ADM).

| Ano  | Total Func |
|------|-----------|
| 2026 | 108,186   |
| 2027 | 113,269   |
| 2028 | 117,418   |
| 2029 | 124,543   |
| 2030 | 129,923   |

### Headcount por BU usado no rateio

| BU               | 2026   | 2027   | 2028   | 2029   | 2030   |
|------------------|--------|--------|--------|--------|--------|
| FOPM Brasil      | 46     | 47     | 48     | 49     | 51     |
| Renovação        | 3      | 3      | 3      | 3      | 3      |
| AMS              | 53,186 | 54,269 | 55,418 | 56,543 | 57,923 |
| Venda Softwares  | 1      | 1      | 1      | 1      | 1      |
| Data Science     | 5      | 8      | 10     | 15     | 17     |

### Valores do Rateio por BU

| BU               | 2026        | 2027        | 2028        | 2029        | 2030        |
|------------------|-------------|-------------|-------------|-------------|-------------|
| FOPM Brasil      | 2.231.383   | 2.260.328   | 2.304.801   | 2.295.843   | 2.370.778   |
| Renovação        | 145.525     | 144.276     | 144.050     | 140.562     | 139.458     |
| AMS              | 2.579.968   | 2.609.915   | 2.660.970   | 2.649.267   | 2.692.591   |
| Venda Softwares  | 48.508      | 48.092      | 48.017      | 46.854      | 46.486      |
| Data Science     | 242.542     | 384.737     | 480.167     | 702.809     | 790.259     |

---

## Lógica de projeção — linha a linha

### Linhas zeradas nas projeções

As seguintes linhas existem no histórico mas são **zero** em todas as projeções:

- Faturamento Bruto → 0 (ADM não gera receita)
- Impostos sobre Venda → 0
- Receita Líquida → 0
- Reclassificação → 0
- Incentivos → 0
- Gastos com Pessoal → 0 (pessoal ADM está dentro de Outras ADM via ratio)
- Outras Despesas Diretas → 0
- Rem. Direta Sócios → 0
- Outras ADM sub-linhas (14 a 24) → não projetadas separadamente
- D&A → 0
- Receita/Despesa Financeira → 0
- IRPJ/CSLL → 0

### MC I e MC II — congelados

```
MC I(t)  = MC II(t) = 376.375,08  (valor de 2025, fixo para toda a projeção)
```

MC I e MC II da ADM representam as entradas operacionais líquidas (reembolsos
recebidos de terceiros). A planilha congela o valor de 2025 sem atualizar por
inflação — é um valor residual tratado como constante.

### Outras Despesas ADM

```
Outras_ADM(t) = RL_Consolidada(t) × 0.12415802928103117
```

Calculada com a RL Consolidada projetada das BUs operacionais do mesmo ano.
Exige que as DREs de todas as BUs operacionais já estejam calculadas antes da ADM.

### Rateio Administrativo (linha 39 — sinal negativo)

```
Rateio_Total(t) = Rateio_Total(t-1) × (1 + inflação(t))
```

Na planilha este valor aparece com **sinal negativo** (é saída da ADM para as BUs).
O valor de base é `Rateio_2025 = −5.047.539,09`.

### Honorários ADM Sócios Diretores

```
Honorários_ADM = 1.310.000  (fixo — média de 2023, 2024 e 2025)
```

`(1.290.000 + 1.320.000 + 1.320.000) / 3 = 1.310.000`

Congelado para toda a projeção. Sem cascata de inflação, sem média móvel.

### Honorários ADM (Rateio) — linha 42

```
Honorarios_Rateio = −1.222.000  (fixo — média de 2023, 2024 e 2025)
```

`(−1.290.000 + −1.188.000 + −1.188.000) / 3 = −1.222.000`

Representa a parcela dos honorários que a ADM **absorve sem repassar** às BUs.
Aparece com sinal negativo na planilha e entra na fórmula do EBITDA com seu
sinal original (negativo), reduzindo o déficit.

### EBITDA

```
EBITDA(t) = MC_II(t) − Outras_ADM(t) − Rateio_Total(t) − Honorários_ADM − Honorários_Rateio
```

Como `Rateio_Total` e `Honorários_Rateio` têm **sinal negativo** na planilha,
subtraí-los na fórmula os converte em positivos — eles reduzem o custo líquido da ADM.

Exemplo 2026:
```
EBITDA = 376.375 − 5.827.896 − (−5.247.926) − 1.310.000 − (−1.222.000)
       = 376.375 − 5.827.896 + 5.247.926 − 1.310.000 + 1.222.000
       = −291.595
```

| Ano  | EBITDA       |
|------|-------------|
| 2026 | −291.595    |
| 2027 | −609.991    |
| 2028 | −973.011    |
| 2029 | −1.345.977  |
| 2030 | −2.014.360  |

O EBITDA fica progressivamente mais negativo porque as Outras ADM crescem
proporcionalmente à receita consolidada, enquanto o Rateio cresce apenas
pela inflação — a diferença entre eles aumenta a cada ano.

### EBIT = LAIR = Lucro Líquido

```
EBIT(t) = EBITDA(t)   (D&A = 0)
LAIR(t) = EBIT(t)     (sem financeiras)
LL(t)   = LAIR(t)     (IRPJ = 0%)
```

---

## Output esperado

Colunas do DataFrame resultado:

```
bu, ano,
mc2,
outras_desp_adm, rl_consolidada_ref,
rateio_adm_total, honorarios_adm, honorarios_rateio,
ebitda, ebit, lair, lucro_liquido,
n_funcionarios_adm,
rateio_fopm, rateio_renovacao, rateio_ams,
rateio_venda_sw, rateio_data_science,
total_func_operacional
```

O CSV de saída é gravado em `projecoes/projecao_administrativa.csv`.

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

### DRE ADM

| Linha            | 2026        | 2027        | 2028        | 2029         | 2030         |
|------------------|-------------|-------------|-------------|--------------|--------------|
| MC II (fixo)     | 376.375     | 376.375     | 376.375     | 376.375      | 376.375      |
| Outras ADM       | 5.827.896   | 6.345.714   | 6.899.391   | 7.469.687    | 8.342.307    |
| Rateio Total     | −5.247.926  | −5.447.348  | −5.638.005  | −5.835.335   | −6.039.572   |
| Honorários ADM   | 1.310.000   | 1.310.000   | 1.310.000   | 1.310.000    | 1.310.000    |
| Honorários Rat.  | −1.222.000  | −1.222.000  | −1.222.000  | −1.222.000   | −1.222.000   |
| EBITDA = LL      | −291.595    | −609.991    | −973.011    | −1.345.977   | −2.014.360   |

### Rateio por BU

| BU              | 2026      | 2027      | 2028      | 2029      | 2030      |
|-----------------|-----------|-----------|-----------|-----------|-----------|
| FOPM Brasil     | 2.231.383 | 2.260.328 | 2.304.801 | 2.295.843 | 2.370.778 |
| Renovação       | 145.525   | 144.276   | 144.050   | 140.562   | 139.458   |
| AMS             | 2.579.968 | 2.609.915 | 2.660.970 | 2.649.267 | 2.692.591 |
| Venda Softwares | 48.508    | 48.092    | 48.017    | 46.854    | 46.486    |
| Data Science    | 242.542   | 384.737   | 480.167   | 702.809   | 790.259   |

### Diagnóstico de desvios

Se Outras ADM divergir → confirmar que o ratio é **12,4158%** aplicado sobre a
**RL Consolidada** (soma das RLs das 5 BUs operacionais). Não usar a média simples
dos ratios históricos — o valor é hardcoded na planilha.

Se o Rateio Total divergir → confirmar que a cascata parte de `5.047.539,09`
(valor absoluto de 2025) e multiplica pela inflação de cada ano.

Se o Rateio por BU divergir → verificar o headcount total (denominador). O headcount
da AMS é derivado (não manual) e muda a cada ano — é a maior fonte de erro aqui.

Se o EBITDA divergir → verificar os sinais. Rateio e Honorários_Rateio têm sinal
negativo na planilha. Na fórmula do EBITDA, ao subtraí-los, eles se tornam positivos.
Simplificando: `EBITDA = MC II − Outras_ADM + |Rateio| − Honorários + |Hon_Rateio|`

---

## Armadilhas conhecidas

**Outras ADM e Rateio são calculados por mecanismos diferentes.** Outros ADM
cresce com a receita consolidada (ratio × RL). O Rateio cresce com a inflação
(cascata). Confundir os dois e usar o mesmo driver para ambos é o erro mais
provável de implementação.

**O ratio 12,4158% não se deriva de forma limpa dos dados históricos.** A planilha
tem um bug interno na seção de premissas onde a coluna de 2024 exibe o valor de 2025.
Usar os dados históricos brutos para calcular a média dará um ratio diferente (~12,2%
ou ~12,5% dependendo da abordagem). O valor correto é **0.12415802928103117** e
deve ser tratado como constante hardcoded.

**MC II é congelado no valor de 2025.** Não é zero, não cresce — é R$ 376.375,08
fixo para todos os anos. Representa entradas operacionais históricas que a planilha
decidiu manter constantes.

**Honorários ADM e Honorários Rateio são ambos fixos.** Nenhum dos dois tem cascata
de inflação ou média móvel — são as médias de 2023-2025 calculadas uma vez e
congeladas. Honorários ADM = +1.310.000 (custo); Honorários Rateio = −1.222.000
(redução líquida do custo).

**A ADM não pode ser projetada antes das BUs operacionais.** Ela precisa da RL
Consolidada (para calcular Outras ADM) e do headcount de cada BU (para distribuir
o Rateio). No orquestrador, deve ser a última BU a ser calculada.

**O EBITDA negativo não é erro.** A ADM é centro de custo — seu resultado sempre
negativo e crescentemente deficitário é o comportamento esperado e correto.
