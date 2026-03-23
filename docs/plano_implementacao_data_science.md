# Plano de Implementação — Projeção DRE Data Science

## Contexto

Este documento especifica a lógica de projeção da BU Data Science de 2026 a 2030,
replicando linha a linha a aba `DRE DATA SCIENCE` da planilha
`S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`.

A Data Science é a única **BU nova sem histórico operacional relevante**. Os anos
de 2023, 2024 e 2025 têm dados esparsos e negativos (fase pré-operacional) — por
isso todos os ratios de custo são **espelhados da FOPM Brasil**, não calculados
sobre o histórico próprio. O modelo de receita é bottom-up por projetos de IA,
com crescimento agressivo de headcount e volume de projetos.

---

## Arquivos envolvidos

```
projecao_bus/
├── fopm.py                       ← adicionar projetar_data_science() aqui
└── projecoes/
    └── projecao_data_science.csv ← gerado pela execução
```

A Data Science não tem CSV histórico utilizável para cálculo de ratios. Todos os
ratios vêm da FOPM Brasil (declarados explicitamente na planilha).

---

## Premissas globais (constantes)

### Inflação Focus

| Ano  | Taxa   |
|------|--------|
| 2026 | 3,97%  |
| 2027 | 3,80%  |
| 2028 | 3,50%  |
| 2029 | 3,50%  |
| 2030 | 3,50%  |

### Reajuste real de TI

**+1% ao ano** sobre a inflação — aplicado ao custo/func e ao ticket médio.
Mesmo padrão das outras BUs para pessoal, mas aqui também aplicado ao ticket.

### Alíquota ISV

**17,43%** — composição padrão (PIS/Cofins 3,65% + CSLL 2,88% + IR 8,00% + ISS 2,90%).

### IRPJ/CSLL

**0%** — regime Lucro Presumido. EBITDA = EBIT = LAIR = Lucro Líquido.

---

## Ratios de custo — todos espelhados da FOPM Brasil

Por não ter período-base operacional, a Data Science usa os ratios históricos
médios da FOPM (2023–2025) como proxy, declarados explicitamente na planilha:

| Ratio                  | Valor        | Fonte                        |
|------------------------|--------------|------------------------------|
| Incentivos / RL        | **2,85%**    | Média FOPM 2023–2025         |
| Outras Desp. Dir. / RL | **3,38%**    | Média FOPM 2023–2025         |
| Rem. Sócios / MC I     | **16,56%**   | Média FOPM 2023–2025         |
| Outras ADM / RL        | **12,77%**   | Média FOPM 2023–2025         |

Estes valores são **constantes** para toda a projeção 2026–2030.

---

## Premissas operacionais — inputs manuais por ano

### Headcount

Input manual — crescimento agressivo de equipe de IA:

| Ano  | N.º Funcionários |
|------|-----------------|
| 2026 | 5               |
| 2027 | 8               |
| 2028 | 10              |
| 2029 | 15              |
| 2030 | 17              |

### Total de Projetos

Input manual — cada projeto = um engajamento de Data Science / IA de grande porte:

| Ano  | Total Projetos |
|------|---------------|
| 2026 | 2             |
| 2027 | 3             |
| 2028 | 4             |
| 2029 | 5             |
| 2030 | 7             |

### Parâmetros fixos

- Horas por projeto: **3.840 h** (equipe dedicada por ~12 meses)
- Ociosidade: **15%** fixo em todos os anos
- Horas/mês: **160**
- Meses/ano: **12**

---

## Lógica de projeção — linha a linha

### Pré-cálculo: bases das cascatas

**Ticket Médio base:**
```
Ticket_2026 = 1.300.000  (input declarado na planilha — base fixa, sem inflação no 1.º ano)
```

**Ticket Médio cascata a partir de 2027:**
```
Ticket(t) = Ticket(t-1) × (1 + inflação(t-1))
```

**Atenção — cascata usa a inflação do ano ANTERIOR**, não do ano corrente.
Isso foi confirmado verificando que a inflação de 2026 (3,97%) é aplicada para
gerar o ticket de 2027, a inflação de 2027 (3,80%) para o de 2028, etc.

| Ano  | Ticket Médio     | Fator aplicado          |
|------|-----------------|------------------------|
| 2026 | 1.300.000,00    | base (sem inflação)     |
| 2027 | 1.351.610,00    | × 1,0397 (inf. 2026)   |
| 2028 | 1.405.268,92    | × 1,0397 (inf. 2026)   |
| 2029 | 1.461.058,09    | × 1,0397 (inf. 2026)   |
| 2030 | 1.519.062,10    | × 1,0397 (inf. 2026)   |

**Atenção — a inflação de 2026 (3,97%) é usada como fator fixo de cascata para
todos os anos**, não a inflação do ano vigente. Todos os anos crescem pelo mesmo
fator 1,0397.

**Custo/Func base:**
```
Custo_Func_2026 = 153.654,72  (input declarado na planilha)
```

Cascata a partir de 2027:
```
Custo_Func(t) = Custo_Func(t-1) × (1 + inflação(t-1) + 1% reajuste TI)
```

Usa a inflação do **ano anterior** (mesma lógica do ticket):

| Ano  | Custo/Func       |
|------|-----------------|
| 2026 | 153.654,72      |
| 2027 | 161.030,14      |  ← × (1 + 3,80% + 1%)
| 2028 | 168.276,50      |  ← × (1 + 3,50% + 1%)
| 2029 | 175.848,94      |  ← × (1 + 3,50% + 1%)
| 2030 | 183.762,15      |  ← × (1 + 3,50% + 1%)

---

### Loop por ano (2026, 2027, 2028, 2029, 2030)

#### 1. Total de Projetos

```
Total_Projetos(t) = input manual (tabela acima)
```

#### 2. Verificação de capacidade (informativo)

```
Horas_Alocadas(t) = N_Func(t) × 160 × 12 × (1 − 0,15)
Capacidade_Projetos = Horas_Alocadas(t) / 3.840
```

Este cálculo confirma que o headcount dimensionado suporta os projetos planejados.
Não entra diretamente no FB — é verificação de consistência.

| Ano  | Horas Alocadas | Capacidade |
|------|---------------|-----------|
| 2026 | 8.160         | 2,125     |
| 2027 | 13.056        | 3,400     |
| 2028 | 16.320        | 4,250     |
| 2029 | 24.480        | 6,375     |
| 2030 | 27.744        | 7,225     |

#### 3. Faturamento Bruto

```
FB(t) = Total_Projetos(t) × Ticket_Médio(t)
```

| Ano  | Projetos | Ticket       | FB           |
|------|---------|-------------|-------------|
| 2026 | 2       | 1.300.000   | 2.600.000   |
| 2027 | 3       | 1.351.610   | 4.054.830   |
| 2028 | 4       | 1.405.269   | 5.621.076   |
| 2029 | 5       | 1.461.058   | 7.305.290   |
| 2030 | 7       | 1.519.062   | 10.633.435  |

#### 4. Impostos sobre Venda

```
ISV(t) = FB(t) × 17,43%
```

#### 5. Receita Líquida

```
RL(t) = FB(t) − ISV(t) = FB(t) × 82,57%
```

| Ano  | RL          |
|------|------------|
| 2026 | 2.146.820  |
| 2027 | 3.348.073  |
| 2028 | 4.641.322  |
| 2029 | 6.031.978  |
| 2030 | 8.780.027  |

#### 6. Reclassificação

```
Reclassificação = 0
```

#### 7. Incentivos de Prospecção e Vendas

```
Incentivos(t) = RL(t) × 2,85%
```

| Ano  | Incentivos |
|------|-----------|
| 2026 | 61.184    |
| 2027 | 95.420    |

#### 8. Gastos com Pessoal

```
Gastos_Pessoal(t) = N_Func(t) × Custo_Func(t)
```

| Ano  | N.Func | Custo/Func | Gastos Pessoal |
|------|--------|-----------|---------------|
| 2026 | 5      | 153.655   | 768.274       |
| 2027 | 8      | 161.030   | 1.288.241     |
| 2028 | 10     | 168.277   | 1.682.765     |
| 2029 | 15     | 175.849   | 2.637.734     |
| 2030 | 17     | 183.762   | 3.123.956     |

#### 9. Outras Despesas Diretas

```
Outras_Dir(t) = RL(t) × 3,38%
```

#### 10. Margem Contribuição I

```
MC I(t) = RL(t) − Incentivos(t) − Gastos_Pessoal(t) − Outras_Dir(t)
```

| Ano  | MC I        |
|------|------------|
| 2026 | 1.244.800  |
| 2027 | 1.851.247  |
| 2028 | 2.669.403  |
| 2029 | 3.018.452  |
| 2030 | 5.109.075  |

#### 11. Remuneração Direta dos Sócios

```
Rem_Socios(t) = MC I(t) × 16,56%
```

| Ano  | Rem. Sócios |
|------|------------|
| 2026 | 206.139    |
| 2027 | 306.567    |

#### 12. Margem Contribuição II

```
MC II(t) = MC I(t) − Rem_Socios(t)
```

| Ano  | MC II       |
|------|------------|
| 2026 | 1.038.661  |
| 2027 | 1.544.681  |
| 2028 | 2.227.350  |
| 2029 | 2.518.596  |
| 2030 | 4.263.012  |

#### 13. Outras Despesas Administrativas

```
Outras_ADM(t) = RL(t) × 12,77%
```

| Ano  | Outras ADM |
|------|-----------|
| 2026 | 274.149   |
| 2027 | 427.549   |
| 2028 | 592.697   |
| 2029 | 770.284   |
| 2030 | 1.121.209 |

#### 14. Rateio Administrativo

```
Rateio_ADM = input externo por ano
```

Vem da aba `DRE ADMINISTRATIVA`, proporcional ao headcount.
Na fase atual, usar os valores fixos da planilha:

| Ano  | Rateio ADM |
|------|-----------|
| 2026 | 242.542   |
| 2027 | 384.737   |
| 2028 | 480.167   |
| 2029 | 702.809   |
| 2030 | 790.259   |

#### 15. Honorários ADM

```
Honorários = 0  (zerado em toda a projeção)
```

Diferente de todas as outras BUs, a Data Science não tem honorários ADM
nas projeções. Valor historicamente também zero.

#### 16. EBITDA

```
EBITDA(t) = MC II(t) − Outras_ADM(t) − Rateio_ADM(t) − Honorários
          = MC II(t) − Outras_ADM(t) − Rateio_ADM(t)
```

| Ano  | EBITDA      |
|------|------------|
| 2026 | 521.970    |
| 2027 | 732.395    |
| 2028 | 1.154.486  |
| 2029 | 1.045.504  |
| 2030 | 2.351.543  |

#### 17. Depreciação / Amortização

```
D&A = 0
```

#### 18. EBIT = LAIR = Lucro Líquido

```
EBIT(t) = EBITDA(t)
LAIR(t) = EBIT(t)
LL(t)   = LAIR(t)
```

---

## Output esperado

Colunas do DataFrame resultado, nesta ordem:

```
bu, ano, n_funcionarios, total_projetos, horas_alocadas, capacidade_projetos,
inflacao_fator_cascata, ticket_medio, custo_por_func,
faturamento_bruto, impostos_sv, receita_liquida,
incentivos, gastos_pessoal, outras_desp_diretas,
mc1, mc1_pct_rl,
remuneracao_socios,
mc2, mc2_pct_rl,
outras_desp_adm, rateio_adm, honorarios_adm,
ebitda, ebitda_pct_rl,
ebit, lair, irpj_csll, lucro_liquido
```

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

| Linha          | 2026      | 2027      | 2028      | 2029      | 2030       |
|----------------|-----------|-----------|-----------|-----------|------------|
| FB             | 2.600.000 | 4.054.830 | 5.621.076 | 7.305.290 | 10.633.435 |
| RL             | 2.146.820 | 3.348.073 | 4.641.322 | 6.031.978 | 8.780.027  |
| Gastos Pessoal | 768.274   | 1.288.241 | 1.682.765 | 2.637.734 | 3.123.956  |
| MC I           | 1.244.800 | 1.851.247 | 2.669.403 | 3.018.452 | 5.109.075  |
| MC II          | 1.038.661 | 1.544.681 | 2.227.350 | 2.518.596 | 4.263.012  |
| Outras ADM     | 274.149   | 427.549   | 592.697   | 770.284   | 1.121.209  |
| Rateio ADM     | 242.542   | 384.737   | 480.167   | 702.809   | 790.259    |
| EBITDA = LL    | 521.970   | 732.395   | 1.154.486 | 1.045.504 | 2.351.543  |

### Diagnóstico de desvios

Se o FB divergir → verificar se o número de projetos e o ticket estão corretos.
Ticket 2026 = 1.300.000 fixo (sem inflação). A partir de 2027, a cascata usa
sempre o fator **1,0397** (inflação de 2026), não a inflação do ano vigente.

Se a RL bater mas o MC I divergir → ratios espelhados da FOPM: incentivos 2,85%,
outras dir. 3,38%. Confirmar que não foram calculados sobre o histórico próprio
da DS (que tem valores erráticos).

Se o MC I bater mas o EBITDA divergir → Outras ADM usa 12,77% × RL. Confirmar
que Honorários = 0 (DS não tem honorários ADM em nenhum ano projetado).

Se o custo/func 2027 divergir → a cascata usa a inflação do ano **anterior**
(3,80% para 2027, não 3,97%). É a mesma regra do ticket.

---

## Diferenças estruturais em relação às demais BUs

| Aspecto               | FOPM / outras BUs          | **Data Science**                    |
|-----------------------|---------------------------|-------------------------------------|
| Driver de receita     | Horas/NFs ou base retida  | **Projetos × Ticket**               |
| Unidade de trabalho   | NF (nota fiscal)          | **Projeto (~3.840 h)**              |
| Headcount             | Input ou derivado         | **Input manual, crescimento rápido**|
| Ratios de custo       | Histórico próprio         | **Espelho da FOPM (sem histórico)** |
| Ticket base 2026      | Média ou cascata normal   | **Fixo R$ 1,3M — sem inflação**     |
| Cascata ticket 2027+  | Inflação do ano vigente   | **Inflação de 2026 (3,97%) fixa**   |
| Cascata custo/func    | Inf. ano vigente + 1%     | **Inf. ano anterior + 1%**          |
| Honorários ADM        | Valor fixo ou móvel       | **Zero**                            |
| D&A / Financeiras     | Zero ou sim               | **Zero**                            |
| IRPJ/CSLL             | 0% ou 34%                 | **0%**                              |

---

## Armadilhas conhecidas

**Ticket e custo/func usam a inflação do ano ANTERIOR na cascata.** A partir de
2027, o fator aplicado é a inflação do ano anterior — não a inflação do ano que
está sendo projetado. Concretamente: para calcular os valores de 2027, usa-se
3,97% (inflação de 2026); para 2028, usa-se 3,80% (inflação de 2027); e assim
por diante. Usar a inflação do ano vigente gera divergência crescente.

**Ticket 2026 é base fixa sem inflação.** R$ 1.300.000 é o ponto de partida
declarado — não é ticket anterior multiplicado por nenhum fator. A inflação
só entra a partir do cálculo de 2027.

**Todos os ratios de custo são da FOPM, não da DS.** Tentar calcular ratios
sobre o histórico da DS (anos 2023–2025) dará resultados sem sentido porque
a BU estava pré-operacional com receita zero ou mínima.

**Honorários ADM = zero.** Enquanto FOPM, AMS, Renovação e Venda Softwares têm
honorários, a DS não tem em nenhum ano projetado. Não é dado faltante.

**O headcount não precisa ser derivado.** Diferente da AMS (onde N.Func é
calculado a partir das NFs e horas), na DS o headcount é input manual direto.
O cálculo de capacidade (horas / horas-por-projeto) é apenas uma verificação
de consistência, não um driver do modelo.
