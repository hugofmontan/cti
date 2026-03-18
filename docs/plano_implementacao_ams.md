# Plano de Implementação — Projeção DRE AMS

## Contexto

Este documento especifica a lógica de projeção da BU AMS (Application Management Services) de 2026 a 2030, replicando linha a linha a aba `DRE AMS` da planilha `S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`.

A AMS tem três diferenças estruturais em relação à FOPM Brasil que tornam sua projeção mais complexa:

1. **Driver de receita diferente** — o FB não é bottom-up de NFs próprias. É a soma de dois componentes: uma base de contratos retida do ano anterior (reajustada) mais um componente incremental proporcional ao FB da FOPM Brasil.
2. **Alíquota de ISV diferente** — 12,3% (não 17,43%). Regime tributário próprio.
3. **Cadeia mais longa até o Lucro Líquido** — a AMS tem D&A real, Receita e Despesa Financeira, LAIR e IRPJ/CSLL de 34% (Lucro Real). Na FOPM, tudo abaixo do EBITDA era zero ou igual.

---

## Arquivos envolvidos

```
projecao_bus/
├── fopm.py                   ← adicionar projetar_ams() aqui
├── dre_ams_historico.csv     ← histórico 2018–2025 (a ser criado)
└── projecoes/
    └── projecao_ams.csv      ← gerado pela execução
```

---

## Premissas globais (constantes)

### Inflação Focus

Idêntica à FOPM:

| Ano | Taxa |
|-----|------|
| 2026 | 3,97% |
| 2027 | 3,80% |
| 2028 | 3,50% |
| 2029 | 3,50% |
| 2030 | 3,50% |

### Alíquota ISV — AMS

**12,30%** sobre o Faturamento Bruto. Composição diferente das demais BUs:

| Tributo | Alíquota |
|---------|----------|
| PIS | 1,70% |
| COFINS | 7,70% |
| ISS | 2,90% |
| **Total** | **12,30%** |

### Spread real de reajuste contratual

**2% ao ano** — pressão de custo de TI acima da inflação aplicada sobre a base retida de contratos.

### Reajuste real de pessoal

**+1% ao ano** sobre a inflação. Mesma regra da FOPM.

### IRPJ/CSLL

**34%** sobre o LAIR. Regime Lucro Real — única BU com IRPJ efetivo nas projeções.

---

## Ratios históricos — como calcular

### Período base

A AMS usa **períodos distintos por ratio**, conforme declarado explicitamente na planilha:

| Ratio | Período base | Valores históricos | Média (driver) |
|-------|-------------|-------------------|---------------|
| Horas/NF | 2023, 2024, 2025 | 98,290 h / 119,607 h / 98,193 h | **105,363 h/NF** |
| Ticket Médio/NF | 2023, 2024, 2025 | R$ 18.390 / R$ 18.343 / R$ 18.006 | **R$ 18.246,57** |
| Outras Desp. Dir. / RL | **2024, 2025** | 1,314% / 2,446% | **1,880%** |
| Rem. Sócios / MC I | 2023, 2024, 2025 | 12,118% / 11,810% / 9,210% | **11,046%** |
| Outras ADM / RL | **2024, 2025** | 0,963% / 1,298% | **1,219%** |
| Custo/Func | 2023, 2024, 2025 | R$ 143.922 / R$ 132.113 / R$ 160.074 | **R$ 145.370** |
| D&A / Horas Totais | **2025 apenas** | R$ 2,6509/h | **R$ 2,6509/h** |

**Atenção:** Outras Desp. Dir. e Outras ADM usam média de **2 anos** (2024–2025), não 3. O ratio de D&A usa **só 2025**.

### Horas por NF — origem do dado

A AMS não usa um modelo de horas alocadas ÷ NFs como a FOPM. Aqui as horas/NF são calculadas diretamente da aba `FAT. AMS`:

```
Horas/NF(ano) = Horas Totais(ano) / N.º NFs(ano)
             = (N.Func × 160 × 12) / COUNT(NFs emitidas)
```

Valores históricos: 2023 = 98,290 h | 2024 = 119,607 h | 2025 = 98,193 h → média = **105,363 h/NF**

---

## Dependência do FB FOPM

A projeção da AMS **depende do FB FOPM projetado de cada ano**. O componente incremental é:

```
Incremental(t) = FB_FOPM(t) × 9,58%
```

A taxa de 9,58% é a média histórica de `ΔFB_AMS / FB_FOPM` nos anos 2023–2025, declarada explicitamente na planilha. Isso significa que `projetar_ams()` deve receber o DataFrame da FOPM já projetado como parâmetro, ou os valores de FB FOPM por ano como dict.

---

## Lógica de projeção — linha a linha

### Pré-cálculo: cascatas iniciais

**Ticket Médio base:**
```
ticket_base = média(ticket_2023, ticket_2024, ticket_2025)
            = (18.390,33 + 18.343,21 + 18.006,16) / 3
            = 18.246,57
```
A partir de 2026 cresce pela inflação em cascata:
```
ticket(t) = ticket(t-1) × (1 + inflação(t))
ticket_2026 = 18.246,57 × 1,0397 = 18.970,95
```
**Diferença em relação à FOPM:** na AMS o ticket 2026 aplica inflação normalmente sobre a média — não há o "atalho" da média direta sem inflação.

**Custo/Func base:**
```
custo_func_base = média(custo_2023, custo_2024, custo_2025)
                = (143.922 + 132.113 + 160.074) / 3
                = 145.370
```
Cresce em cascata: `Custo(t) = Custo(t-1) × (1 + inflação(t) + 1%)`

**D&A ratio:**
```
ratio_da = D&A_2025 / Horas_Totais_2025
         = 167.097 / (32,83 × 160 × 12)
         = 167.097 / 63.033,6
         = 2,6509 R$/hora
```
Constante para toda a projeção.

---

### Loop por ano (2026, 2027, 2028, 2029, 2030)

#### 1. Componente Base Retida

```
Base_Retida(t) = FB_AMS(t-1) × (1 - Churn) × Fator_Reajuste(t)
Fator_Reajuste(t) = (1 + inflação(t)) × (1 + 2%)
Churn = 0% em todas as projeções
```

Exemplo 2026:
```
Base_Retida_2026 = 15.293.573,83 × 1,0597 = 16.206.600,19
```

| Ano | Fator Reajuste |
|-----|---------------|
| 2026 | 1,0597 |
| 2027 | 1,0596 |
| 2028 | 1,0557 |
| 2029 | 1,0557 |
| 2030 | 1,0557 |

#### 2. Componente Incremental

```
Incremental(t) = FB_FOPM(t) × 9,58%
```

| Ano | FB FOPM | Incremental |
|-----|---------|------------|
| 2026 | 22.755.017 | 2.179.931 |
| 2027 | 24.293.002 | 2.327.270 |
| 2028 | 26.016.091 | 2.492.342 |
| 2029 | 27.666.117 | 2.650.414 |
| 2030 | 30.380.019 | 2.910.406 |

#### 3. Faturamento Bruto

```
FB(t) = Base_Retida(t) + Incremental(t)
```

Valores de referência:

| Ano | FB |
|-----|----|
| 2026 | 18.386.531 |
| 2027 | 19.473.853 |
| 2028 | 20.581.987 |
| 2029 | 21.734.990 |
| 2030 | 23.044.633 |

#### 4. N.º NFs Projetadas

```
NFs(t) = FB(t) / Ticket_Médio(t)
```

O ticket cresce em cascata a partir de 18.246,57:

| Ano | Ticket Médio | NFs |
|-----|-------------|-----|
| 2026 | 18.970,95 | 969,19 |
| 2027 | 19.691,85 | 988,93 |
| 2028 | 20.381,06 | 1.009,86 |
| 2029 | 21.094,40 | 1.030,37 |
| 2030 | 21.832,70 | 1.055,51 |

#### 5. Horas Totais Necessárias

```
Horas_Totais(t) = NFs(t) × Horas_por_NF
               = NFs(t) × 105,363
```

| Ano | Horas Totais |
|-----|-------------|
| 2026 | 102.117,3 |
| 2027 | 104.196,7 |
| 2028 | 106.401,8 |
| 2029 | 108.562,8 |
| 2030 | 111.211,8 |

#### 6. N.º Funcionários (derivado)

```
N_Func(t) = Horas_Totais(t) / (160 × 12)
```

O headcount da AMS **não é input manual** — é derivado da demanda operacional. Isso é a diferença fundamental em relação à FOPM.

| Ano | N.º Func |
|-----|---------|
| 2026 | 53,186 |
| 2027 | 54,269 |
| 2028 | 55,418 |
| 2029 | 56,543 |
| 2030 | 57,923 |

#### 7. Impostos sobre Venda

```
ISV(t) = FB(t) × 12,30%
```

Alíquota fixa e específica da AMS. Não usar 17,43%.

#### 8. Receita Líquida

```
RL(t) = FB(t) - ISV(t)
```

| Ano | RL |
|-----|----|
| 2026 | 16.124.988 |
| 2027 | 17.078.569 |
| 2028 | 18.050.402 |
| 2029 | 19.061.586 |
| 2030 | 20.210.143 |

#### 9. Reclassificação de Receitas e Despesas

```
Reclassificação = 0  (zerada em todas as projeções)
```

#### 10. Incentivos de Prospecção e Vendas

```
Incentivos = 0  (zerados nas projeções — planilha declara explicitamente)
```

Diferença em relação à FOPM: na AMS os incentivos históricos existem (R$ 74.459 em 2023) mas são zerados na projeção.

#### 11. Gastos com Pessoal (cascata)

```
Custo_Func(t) = Custo_Func(t-1) × (1 + inflação(t) + 1%)
Gastos_Pessoal(t) = N_Func(t) × Custo_Func(t)
```

| Ano | Custo/Func | Gastos Pessoal |
|-----|-----------|---------------|
| 2026 | 152.595 | 8.115.906 |
| 2027 | 159.919 | 8.678.667 |
| 2028 | 167.115 | 9.261.139 |
| 2029 | 174.636 | 9.874.440 |
| 2030 | 182.494 | 10.570.579 |

#### 12. Outras Despesas Diretas

```
Outras_Dir(t) = RL(t) × 1,880%
```

Ratio calculado como média de **2024 e 2025** (não 3 anos):
- 2024: 142.797 / 10.870.637 = 1,314%
- 2025: 326.078 / 13.331.723 = 2,446%
- Média: **1,880%**

Sub-linhas (13a Profissionais, 13c Projetos) não projetadas separadamente.

| Ano | Outras Dir. |
|-----|------------|
| 2026 | 303.108 |

#### 13. Margem Contribuição I

```
MC I(t) = RL(t) - Gastos_Pessoal(t) - Outras_Dir(t)
```

**Atenção:** Incentivos = 0, portanto não entram no cálculo. Diferente da FOPM onde Incentivos subtrai da RL.

| Ano | MC I |
|-----|------|
| 2026 | 7.705.973 |
| 2027 | 8.078.868 |
| 2028 | 8.449.963 |
| 2029 | 8.828.837 |
| 2030 | 9.259.666 |

#### 14. Remuneração Direta dos Sócios

```
Rem_Socios(t) = MC_I(t) × 11,046%
```

Ratio = média de 2023, 2024 e 2025:
- 2023: 566.808 / 5.244.255 = 12,118%
- 2024: 566.808 / 5.366.340 = 11,810%
- 2025: 566.808 / 6.720.889 = 9,210%
- Média: **11,046%**

| Ano | Rem. Sócios |
|-----|------------|
| 2026 | 851.197 |

#### 15. Margem Contribuição II

```
MC II(t) = MC I(t) - Rem_Socios(t)
```

| Ano | MC II |
|-----|-------|
| 2026 | 6.854.776 |
| 2027 | 7.186.482 |
| 2028 | 7.516.585 |
| 2029 | 7.853.610 |
| 2030 | 8.236.849 |

#### 16. Outras Despesas Administrativas

```
Outras_ADM(t) = RL(t) × 1,219%
```

Ratio = média de **2024 e 2025**:
- 2024: 104.660 / 10.870.637 = 0,963%
- 2025: 173.048 / 13.331.723 = 1,298%
- Média: **1,219%**

Sub-linhas (14 a 24) não projetadas separadamente.

| Ano | Outras ADM |
|-----|-----------|
| 2026 | 196.505 |

#### 17. Rateio Administrativo

```
Rateio_ADM = input externo por ano
```

Mesma lógica da FOPM: vem da aba `DRE ADMINISTRATIVA`, proporcional ao headcount. Na fase atual, usar os valores já calculados na planilha:

| Ano | Rateio ADM |
|-----|-----------|
| 2026 | 2.579.968 |
| 2027 | 2.609.915 |
| 2028 | 2.660.970 |
| 2029 | 2.649.267 |
| 2030 | 2.692.591 |

#### 18. Honorários ADM Sócios Diretores (média móvel)

```
Honorários(t) = média(Honorários(t-4), Honorários(t-3), Honorários(t-2), Honorários(t-1))
```

**Diferença em relação à FOPM:** a AMS usa **média móvel de 4 anos anteriores**, não cascata de inflação.

Verificação:
- 2026 = média(2022, 2023, 2024, 2025) = (240.000 + 258.000 + 264.000 + 264.000) / 4 = **256.500** ✓
- 2027 = média(2023, 2024, 2025, 2026) = (258.000 + 264.000 + 264.000 + 256.500) / 4 = **260.625** ✓
- 2028 = média(2024, 2025, 2026, 2027) = (264.000 + 264.000 + 256.500 + 260.625) / 4 = **261.281,25** ✓

| Ano | Honorários |
|-----|-----------|
| 2026 | 256.500 |
| 2027 | 260.625 |
| 2028 | 261.281 |
| 2029 | 260.602 |
| 2030 | 259.752 |

#### 19. EBITDA

```
EBITDA(t) = MC II(t) - Outras_ADM(t) - Rateio_ADM(t) - Honorários(t)
```

| Ano | EBITDA |
|-----|--------|
| 2026 | 3.821.803 |
| 2027 | 4.107.817 |
| 2028 | 4.374.365 |
| 2029 | 4.711.450 |
| 2030 | 5.038.218 |

#### 20. Depreciação / Amortização

```
D&A(t) = ratio_da × Horas_Totais(t)
ratio_da = D&A_2025 / Horas_Totais_2025
         = 167.097 / (32,83 × 160 × 12)
         = 2,6509 R$/hora
```

**Única BU com D&A real nas projeções.** Calculada sobre as horas totais derivadas do modelo de NFs.

| Ano | D&A |
|-----|-----|
| 2026 | 270.677 |
| 2027 | 276.189 |
| 2028 | 282.034 |
| 2029 | 287.762 |
| 2030 | 294.784 |

#### 21. EBIT

```
EBIT(t) = EBITDA(t) - D&A(t)
```

| Ano | EBIT |
|-----|------|
| 2026 | 3.551.126 |
| 2027 | 3.831.628 |
| 2028 | 4.092.331 |
| 2029 | 4.423.688 |
| 2030 | 4.743.435 |

#### 22. Receita Financeira

```
Receita_Fin(t) = média(Rec_Fin_2023, Rec_Fin_2024, Rec_Fin_2025)
```

Média dos 3 anos históricos, congelada nas projeções:
- 2023: R$ 109.000 | 2024: R$ 50.000 | 2025: R$ 84.000 → média = **R$ 81.000**

**Atenção:** a planilha mostra R$ 81.000 em 2026 e valores ligeiramente diferentes nos anos seguintes (71.667, 78.889...). Isso ocorre porque a média móvel inclui os anos projetados anteriores. Para simplicidade na implementação, usar o valor de R$ 81.000 fixo em 2026 e calcular os seguintes como média dos 4 anos mais recentes — idêntica à lógica dos honorários.

| Ano | Rec. Financeira |
|-----|----------------|
| 2026 | 81.000 |
| 2027 | 71.667 |
| 2028 | 78.889 |
| 2029 | 77.185 |
| 2030 | 75.914 |

#### 23. Despesa Financeira

```
Desp_Fin = 56.667  (constante — média 2023-2025)
```

- 2023: R$ 72.000 | 2024: R$ 55.000 | 2025: R$ 56.667 → média ≈ **R$ 56.667**

Valor fixo em todos os anos de projeção.

#### 24. LAIR

```
LAIR(t) = EBIT(t) + Receita_Fin(t) - Desp_Fin(t)
```

| Ano | LAIR |
|-----|------|
| 2026 | 3.575.459 |
| 2027 | 3.846.628 |
| 2028 | 4.114.553 |
| 2029 | 4.444.207 |
| 2030 | 4.762.682 |

#### 25. IRPJ / CSLL

```
IRPJ_CSLL(t) = LAIR(t) × 34%
```

| Ano | IRPJ/CSLL |
|-----|----------|
| 2026 | 1.215.656 |
| 2027 | 1.307.853 |
| 2028 | 1.398.948 |
| 2029 | 1.511.030 |
| 2030 | 1.619.312 |

#### 26. Lucro Líquido

```
Lucro_Liquido(t) = LAIR(t) - IRPJ_CSLL(t)
```

| Ano | Lucro Líquido |
|-----|--------------|
| 2026 | 2.359.803 |
| 2027 | 2.538.774 |
| 2028 | 2.715.605 |
| 2029 | 2.933.176 |
| 2030 | 3.143.370 |

---

## Output esperado

Colunas do DataFrame resultado, nesta ordem:

```
bu, ano, n_funcionarios, inflacao_focus,
nfs_projetadas, horas_por_nf, horas_totais,
ticket_medio, custo_por_func,
base_retida, incremental_fopm,
faturamento_bruto, impostos_sv, receita_liquida,
incentivos, gastos_pessoal, outras_desp_diretas,
mc1, mc1_pct_rl,
remuneracao_socios,
mc2, mc2_pct_rl,
outras_desp_adm, rateio_adm, honorarios_adm,
ebitda, ebitda_pct_rl,
depreciacao_amort, ebit,
receita_financeira, despesa_financeira,
lair, irpj_csll, lucro_liquido
```

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

| Linha | 2026 | 2027 | 2028 | 2029 | 2030 |
|-------|------|------|------|------|------|
| Faturamento Bruto | 18.386.531 | 19.473.853 | 20.581.987 | 21.734.990 | 23.044.633 |
| Receita Líquida | 16.124.988 | 17.078.569 | 18.050.402 | 19.061.586 | 20.210.143 |
| Gastos com Pessoal | 8.115.906 | 8.678.667 | 9.261.139 | 9.874.440 | 10.570.579 |
| MC I | 7.705.973 | 8.078.868 | 8.449.963 | 8.828.837 | 9.259.666 |
| MC II | 6.854.776 | 7.186.482 | 7.516.585 | 7.853.610 | 8.236.849 |
| EBITDA | 3.821.803 | 4.107.817 | 4.374.365 | 4.711.450 | 5.038.218 |
| D&A | 270.677 | 276.189 | 282.034 | 287.762 | 294.784 |
| EBIT | 3.551.126 | 3.831.628 | 4.092.331 | 4.423.688 | 4.743.435 |
| LAIR | 3.575.459 | 3.846.628 | 4.114.553 | 4.444.207 | 4.762.682 |
| IRPJ/CSLL | 1.215.656 | 1.307.853 | 1.398.948 | 1.511.030 | 1.619.312 |
| Lucro Líquido | 2.359.803 | 2.538.774 | 2.715.605 | 2.933.176 | 3.143.370 |

### Diagnóstico de desvios

Se o FB bater mas a RL divergir → alíquota ISV errada. Checar se está usando 12,30% e não 17,43%.

Se a RL bater mas o MC I divergir → checar se incentivos estão zerados (AMS não projeta incentivos) e se o ratio de Outras Dir. está em 1,880% (média 2024-2025, não 3 anos).

Se o MC I bater mas o EBITDA divergir → verificar ratio de Outras ADM (1,219%), rateio (valores fixos) e honorários (média móvel de 4 anos, não cascata de inflação).

Se o EBITDA bater mas o EBIT divergir → D&A errada. Checar se está usando `ratio_da × Horas_Totais` com ratio = 2,6509 R$/hora (D&A_2025 / Horas_Totais_2025).

Se o EBIT bater mas o LAIR divergir → Receita ou Despesa Financeira erradas.

Se o LAIR bater mas o Lucro Líquido divergir → IRPJ está com alíquota errada. Deve ser 34%.

---

## Diferenças estruturais em relação à FOPM

| Aspecto | FOPM Brasil | AMS |
|---------|-------------|-----|
| Driver de receita | Bottom-up: NFs × Ticket | Base retida + Incremental FOPM |
| Headcount | Input manual | Derivado das NFs projetadas |
| Alíquota ISV | 17,43% | 12,30% |
| Incentivos projetados | Sim (2,852% × RL) | Não (zerados) |
| Honorários ADM | Cascata de inflação | Média móvel 4 anos |
| D&A | Zero | Sim (ratio × Horas Totais) |
| Receita/Despesa Financeira | Zero | Sim (valores históricos) |
| IRPJ/CSLL | 0% | 34% sobre LAIR |
| Período base ratios | 3 anos (2023–2025) para todos | Varia: 2 ou 3 anos dependendo do ratio |

---

## Armadilhas conhecidas

**O FB da AMS depende do FB da FOPM projetado.** A função `projetar_ams()` não pode rodar de forma independente — precisa receber os valores de FB FOPM como parâmetro. No orquestrador, FOPM deve ser projetada antes da AMS.

**Headcount não é input — é output.** Ao contrário da FOPM onde N.Func é premissa, na AMS N.Func é derivado da cadeia: FB → NFs → Horas Totais → N.Func. Qualquer erro no FB propaga para os Gastos com Pessoal.

**Outras Desp. Dir. e Outras ADM usam média de 2 anos, não 3.** Usar média de 3 anos daria ratios incorretos para essas duas linhas.

**D&A usa só o ano de 2025 como base**, não uma média. Usar média dos 3 anos resultaria em ~265.132 vs 270.677 da planilha — diferença de R$ 5.545 por ano.

**Honorários usam média móvel de 4 anos**, não cascata de inflação como na FOPM. A lógica é: a cada ano, a média desliza incorporando o valor calculado do ano anterior. Isso cria uma série que converge suavemente.

**Alíquota ISV é 12,30%, não 17,43%.** Usar a alíquota padrão das outras BUs sub-estima os impostos e super-estima a RL em ~R$ 880.000 só em 2026.

**Período base distinto por ratio.** Não existe um único "período 2023-2025" para todos os ratios da AMS. Outras Desp. Dir. e Outras ADM usam 2024-2025 (a planilha declara isso explicitamente na metodologia de cada linha).
