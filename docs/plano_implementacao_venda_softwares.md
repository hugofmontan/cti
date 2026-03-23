# Plano de Implementação — Projeção DRE Venda de Softwares

## Contexto

Este documento especifica a lógica de projeção da BU Venda de Licenças de Software
de 2026 a 2030, replicando linha a linha a aba `DRE VENDA SOFTWARES` da planilha
`S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`.

A Venda de Softwares é a BU com a estrutura de custos mais enxuta do modelo:
1 funcionário fixo, sem Remuneração de Sócios, sem Outras Despesas ADM, e nada
abaixo do EBITDA. O único cuidado é o fator de crescimento real — a planilha
exibe 5% na célula de premissa mas o cálculo efetivo usa **4,5%**, conforme
confirmado linha a linha para todos os anos 2026–2030.

---

## Arquivos envolvidos

```
projecao_bus/
├── fopm.py                          ← adicionar projetar_venda_softwares() aqui
├── dre_venda_softwares_historico.csv ← histórico 2018–2025 (a ser criado)
└── projecoes/
    └── projecao_venda_softwares.csv  ← gerado pela execução
```

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

### Alíquota ISV

**17,43%** sobre o Faturamento Bruto. Composição padrão:

| Tributo    | Alíquota |
|------------|----------|
| PIS/Cofins | 3,65%    |
| CSLL       | 2,88%    |
| IR         | 8,00%    |
| ISS        | 2,90%    |
| **Total**  | **17,43%** |

### Reajuste real de pessoal

**+1% ao ano** sobre a inflação — mesmo padrão das demais BUs.

### IRPJ/CSLL

**0%** — alíquota zerada. EBITDA = EBIT = LAIR = Lucro Líquido.

---

## Premissas operacionais — inputs manuais por ano

### Headcount

**Fixo em 1 funcionário** para toda a projeção 2026–2030 e para todo o histórico
disponível. A BU opera com uma única pessoa em todos os anos.

### Fator de crescimento real

**4,5% ao ano** — constante para todos os anos projetados.

**Armadilha crítica:** a linha de premissa `Fator de Crescimento (%)` na planilha
(linha 75) exibe o valor `0,05` (5%), mas o cálculo efetivo do FB usa **4,5%**.
Isso foi descoberto ao verificar que `FB_2025 × (1 + 5% + 3,97%) = 8.415.328`
e `FB_2025 × (1 + 4,5% + 3,97%) = 8.376.715` — somente o segundo bate com a
planilha. O valor real de 4,5% está registrado na linha `Fator Cresc (base)`
(linha 91), que é a célula de referência efetiva do cálculo.

---

## Ratios históricos — como calcular

### Período base e regras

A Venda de Softwares usa **períodos distintos por ratio**:

| Ratio                       | Período base       | Valores históricos                        | Driver              |
|-----------------------------|--------------------|-------------------------------------------|---------------------|
| Incentivos / RL             | 2023, 2024, 2025   | 1,541% / 3,145% / 2,644%                 | **média = 2,443%**  |
| Outras Desp. Dir. / RL      | **2025 apenas**    | 28,431% / 22,145% / **18,461%**           | **18,461%**         |
| Rem. Sócios / MC I          | N/A                | 0% em todos os anos                       | **0%**              |
| Outras ADM / RL             | N/A                | 0% nos anos-base (2023, 2024, 2025)       | **0%**              |
| Custo/Func (R$/ano)         | 2023, 2024, 2025   | 187.604 / 157.969 / 169.393              | **base cascata**    |

**Nota sobre Outras Desp. Dir.:** o histórico é muito volátil (28,4% → 22,1% → 18,5%).
A planilha congela o **valor mais recente** (2025 = 18,461%), não a média.
Usar a média resultaria em 23,0%, que diverge do gabarito.

**Nota sobre Outras ADM:** zerada em 2023, 2024 e 2025. Ratio = 0% nas projeções.

---

## Lógica de projeção — linha a linha

### Pré-cálculo: base para as cascatas

**Custo/Func base:**
```
Custo_Func_2025 = Gastos_Pessoal_2025 / N_Func_2025
               = 169.393,04 / 1
               = 169.393,04
```

**FB base:**
```
FB_base = FB_2025 = 7.722.610,43
```

**Honorários base:**
```
Honorários = média(hon_2023, hon_2024, hon_2025)
           = (322.500 + 330.000 + 330.000) / 3
           = 327.500
```
Este valor é calculado uma vez e **congelado** para toda a projeção — não é
uma janela deslizante como na Renovação ou AMS. Comprovado: se fosse móvel,
2027 seria `(330.000 + 330.000 + 327.500) / 3 = 329.167`, mas a planilha
mostra 327.500 em todos os anos.

---

### Loop por ano (2026, 2027, 2028, 2029, 2030)

#### 1. Faturamento Bruto (cascata, soma simples)

```
FB(t) = FB(t-1) × (1 + fator_crescimento + inflação(t))
      = FB(t-1) × (1 + 0,045 + inflação(t))
```

O fator é soma simples dos dois componentes — mesmo comportamento da Renovação,
diferente do produto composto que seria matematicamente mais correto.

| Ano  | Inflação | Fator total | FB           |
|------|---------|-------------|-------------|
| 2026 | 3,97%   | 1,0847      | 8.376.716   |
| 2027 | 3,80%   | 1,0830      | 9.071.983   |
| 2028 | 3,50%   | 1,0800      | 9.797.742   |
| 2029 | 3,50%   | 1,0800      | 10.581.561  |
| 2030 | 3,50%   | 1,0800      | 11.428.086  |

Ao final de cada ano: `fb_ant = FB(t)`

#### 2. Impostos sobre Venda

```
ISV(t) = FB(t) × 17,43%
```

#### 3. Receita Líquida

```
RL(t) = FB(t) − ISV(t) = FB(t) × 82,57%
```

| Ano  | RL          |
|------|------------|
| 2026 | 6.916.654  |
| 2027 | 7.490.736  |
| 2028 | 8.089.995  |
| 2029 | 8.737.195  |
| 2030 | 9.436.170  |

#### 4. Reclassificação de Receitas e Despesas

```
Reclassificação = 0  (zerada nas projeções)
```

#### 5. Incentivos de Prospecção e Vendas

```
Incentivos(t) = RL(t) × 2,443%
```

Ratio = média aritmética de 2023, 2024 e 2025:
- 2023: 40.771,81 / 2.645.872,52 = 1,541%
- 2024: 157.306,64 / 5.002.292,92 = 3,145%
- 2025: 168.010,36 / 6.353.758,49 = 2,644%
- Média: **2,443%**

| Ano  | Incentivos |
|------|-----------|
| 2026 | 168.995   |
| 2027 | 183.022   |

#### 6. Gastos com Pessoal (cascata)

```
Custo_Func(t) = Custo_Func(t-1) × (1 + inflação(t) + 1%)
Gastos_Pessoal(t) = 1 × Custo_Func(t) = Custo_Func(t)
```

| Ano  | Custo/Func   | Gastos Pessoal |
|------|-------------|---------------|
| 2026 | 177.811,88  | 177.811,88    |
| 2027 | 186.346,85  | 186.346,85    |
| 2028 | 194.732,45  | 194.732,45    |
| 2029 | 203.495,41  | 203.495,41    |
| 2030 | 212.652,71  | 212.652,71    |

Ao final de cada ano: `custo_func_ant = Custo_Func(t)`

#### 7. Outras Despesas Diretas

```
Outras_Dir(t) = RL(t) × 18,461%
```

Ratio = valor de **2025 apenas** (não média):
`1.172.937,78 / 6.353.758,49 = 18,461%`

O histórico desta linha é dominado por custos de licenças de software
repassadas ao cliente, que oscilam muito entre anos — por isso a planilha
congela o valor mais recente em vez de usar a média.

Sub-linha `13b. Custos de Licenças` representa praticamente 100% deste valor
no histórico, mas não é projetada separadamente.

| Ano  | Outras Dir.  |
|------|-------------|
| 2026 | 1.276.851   |
| 2027 | 1.382.830   |
| 2028 | 1.493.456   |
| 2029 | 1.612.933   |
| 2030 | 1.741.967   |

#### 8. Margem Contribuição I

```
MC I(t) = RL(t) − Incentivos(t) − Gastos_Pessoal(t) − Outras_Dir(t)
```

| Ano  | MC I        |
|------|------------|
| 2026 | 5.292.996  |
| 2027 | 5.738.538  |
| 2028 | 6.204.143  |
| 2029 | 6.707.290  |
| 2030 | 7.250.996  |

#### 9. Remuneração Direta dos Sócios

```
Rem_Socios = 0  (zero em todo o histórico e nas projeções)
```

Esta BU não remunera sócios diretamente — característica estrutural,
não um dado faltante.

#### 10. Margem Contribuição II

```
MC II(t) = MC I(t)  (pois Rem. Sócios = 0)
```

#### 11. Outras Despesas Administrativas

```
Outras_ADM = 0  (zero nos anos-base 2023, 2024, 2025 → zerado nas projeções)
```

#### 12. Rateio Administrativo

```
Rateio_ADM = input externo por ano
```

Vem da aba `DRE ADMINISTRATIVA`, proporcional ao headcount (N.Func = 1).
Na fase atual, usar os valores fixos da planilha:

| Ano  | Rateio ADM |
|------|-----------|
| 2026 | 48.508    |
| 2027 | 48.092    |
| 2028 | 48.017    |
| 2029 | 46.854    |
| 2030 | 46.486    |

#### 13. Honorários ADM Sócios Diretores (valor fixo)

```
Honorários = 327.500  (constante em todos os anos)
```

Calculado como média(2023, 2024, 2025) = (322.500 + 330.000 + 330.000) / 3
= **327.500**, congelado para toda a projeção.

Diferente da Renovação (média móvel 3 anos) e da AMS (média móvel 4 anos).

#### 14. EBITDA

```
EBITDA(t) = MC II(t) − Outras_ADM(t) − Rateio_ADM(t) − Honorários(t)
          = MC II(t) − 0 − Rateio_ADM(t) − 327.500
```

| Ano  | EBITDA      |
|------|------------|
| 2026 | 4.916.988  |
| 2027 | 5.362.946  |
| 2028 | 5.828.626  |
| 2029 | 6.332.936  |
| 2030 | 6.877.010  |

#### 15. Depreciação / Amortização

```
D&A = 0
```

#### 16. EBIT

```
EBIT(t) = EBITDA(t)
```

#### 17. Receita Financeira

```
Receita_Financeira = 0
```

#### 18. Despesa Financeira

```
Despesa_Financeira = 0
```

#### 19. LAIR

```
LAIR(t) = EBIT(t)
```

#### 20. IRPJ / CSLL

```
IRPJ_CSLL = 0  (alíquota = 0%)
```

#### 21. Lucro Líquido

```
Lucro_Liquido(t) = LAIR(t) = EBITDA(t)
```

---

## Output esperado

Colunas do DataFrame resultado, nesta ordem:

```
bu, ano, n_funcionarios, inflacao_focus, fator_nominal,
custo_por_func,
faturamento_bruto, impostos_sv, receita_liquida,
incentivos, gastos_pessoal, outras_desp_diretas,
mc1, mc1_pct_rl,
remuneracao_socios,
mc2, mc2_pct_rl,
outras_desp_adm, rateio_adm, honorarios_adm,
ebitda, ebitda_pct_rl,
ebit, lair, irpj_csll, lucro_liquido
```

O CSV de saída é gravado em `projecoes/projecao_venda_softwares.csv`.

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

| Linha             | 2026      | 2027      | 2028      | 2029       | 2030       |
|-------------------|-----------|-----------|-----------|------------|------------|
| Faturamento Bruto | 8.376.716 | 9.071.983 | 9.797.742 | 10.581.561 | 11.428.086 |
| Receita Líquida   | 6.916.654 | 7.490.736 | 8.089.995 | 8.737.195  | 9.436.170  |
| Incentivos        | 168.995   | 183.022   | 197.663   | 213.476    | 230.554    |
| Gastos Pessoal    | 177.812   | 186.347   | 194.732   | 203.495    | 212.653    |
| Outras Dir.       | 1.276.851 | 1.382.830 | 1.493.456 | 1.612.933  | 1.741.967  |
| MC I = MC II      | 5.292.996 | 5.738.538 | 6.204.143 | 6.707.290  | 7.250.996  |
| Rateio ADM        | 48.508    | 48.092    | 48.017    | 46.854     | 46.486     |
| Honorários        | 327.500   | 327.500   | 327.500   | 327.500    | 327.500    |
| EBITDA = LL       | 4.916.988 | 5.362.946 | 5.828.626 | 6.332.936  | 6.877.010  |

### Diagnóstico de desvios

Se o FB divergir → confirmar que o fator de crescimento é **4,5%** (não 5%) e
que a fórmula é **soma simples** `1 + 0,045 + inflação` (não produto composto).
Usar 5% gera ~R$ 38.000 de excesso já no primeiro ano.

Se a RL bater mas o MC I divergir → verificar se o ratio de Outras Desp. Dir.
é o valor de **2025 isolado** (18,461%), não a média dos 3 anos (23,0%).

Se o MC I bater mas o EBITDA divergir → honorários devem ser **R$ 327.500 fixo**
(não crescem, não têm média móvel). Confirmar que `hon = 327.500` é constante
para todos os anos.

---

## Diferenças estruturais em relação às demais BUs

| Aspecto                  | FOPM              | AMS                    | Renovação          | **Venda Softwares**         |
|--------------------------|-------------------|------------------------|--------------------|-----------------------------|
| Driver de receita        | NFs × Ticket      | Base retida + Incr.    | Base retida        | **Base retida, fator fixo** |
| Dependência externa      | Nenhuma           | FB FOPM obrigatório    | Nenhuma            | **Nenhuma**                 |
| Headcount                | Input variável    | Derivado das NFs       | Fixo em 3          | **Fixo em 1**               |
| Alíquota ISV             | 17,43%            | 12,30%                 | 17,43%             | **17,43%**                  |
| Fórmula fator reajuste   | N/A               | Soma simples           | Soma simples       | **Soma simples**            |
| Fator crescimento real   | N/A               | 2%                     | 2%                 | **4,5% (label diz 5%)**     |
| Outras Desp. Dir.        | Ratio × RL (3a)   | Ratio × RL (2a)        | Zero               | **Ratio × RL (só 2025)**    |
| Rem. Sócios              | 16,558% × MC I    | 11,046% × MC I         | 6,5% × MC I        | **Zero**                    |
| Outras ADM               | 12,772% × RL      | 1,219% × RL            | 0,931% × RL        | **Zero**                    |
| Honorários ADM           | Cascata inflação  | Média móvel 4 anos     | Média móvel 3 anos | **Fixo R$ 327.500**         |
| D&A / Financeiras / IRPJ | Tudo zero         | D&A + Fin. + 34%       | Tudo zero          | **Tudo zero**               |

---

## Armadilhas conhecidas

**Fator de crescimento real é 4,5%, não 5%.** A célula de premissa exibe 5%,
mas a célula de referência efetiva (`Fator Cresc (base)`, linha 91) contém 0,045.
O cálculo confirmado centavo a centavo para todos os anos usa 4,5%. Usar 5%
gera divergência crescente de ~R$ 38k em 2026 a ~R$ 200k em 2030.

**Fórmula é soma simples.** `1 + 0,045 + inflação`, não `(1 + 0,045) × (1 + inflação)`.
A diferença em 2026 seria de ~R$ 14k — pequena mas acumulável.

**Ratio de Outras Desp. Dir. usa só 2025.** A linha é dominada por custos de
licenças de software muito variáveis entre anos. A planilha descarta 2023 e 2024
e usa apenas o valor mais recente como proxy estável.

**Honorários são fixos, não média móvel.** Ao contrário da Renovação (3 anos)
e da AMS (4 anos), aqui a média é calculada uma única vez e congelada.
Implementar uma janela deslizante daria valores errados a partir de 2027.

**Rem. Sócios e Outras ADM são estruturalmente zero.** Não é ausência de dado —
é característica desta BU. Não tentar imputar ratios de outras BUs.
