# Plano de Implementação — Projeção DRE Renovação

## Contexto

Este documento especifica a lógica de projeção da BU Renovação de Suporte e Manutenção
de 2026 a 2030, replicando linha a linha a aba `DRE RENOVAÇÃO` da planilha
`S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`.

A Renovação é a BU estruturalmente mais simples do modelo: não depende de nenhuma
outra BU, tem headcount fixo, custos diretos zerados e nada abaixo do EBITDA.
A única peculiaridade que pode causar erro silencioso é o bug de label no custo/func
documentado na seção correspondente.

---

## Arquivos envolvidos

```
projecao_bus/
├── fopm.py                      ← adicionar projetar_renovacao() aqui
├── dre_renovacao_historico.csv  ← histórico 2018–2025 (a ser criado)
└── projecoes/
    └── projecao_renovacao.csv   ← gerado pela execução
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

### Spread real de reajuste contratual

**2% ao ano** — aplicado sobre a base de contratos retida, somado diretamente
à inflação (não multiplicado).

### Reajuste real de pessoal

**+1% ao ano** sobre a inflação — mesmo padrão da FOPM e da AMS.

### Alíquota ISV

**17,43%** sobre o Faturamento Bruto. Composição padrão:

| Tributo    | Alíquota |
|------------|----------|
| PIS/Cofins | 3,65%    |
| CSLL       | 2,88%    |
| IR         | 8,00%    |
| ISS        | 2,90%    |
| **Total**  | **17,43%** |

### IRPJ/CSLL

**0%** — mesma lógica da FOPM. EBITDA = EBIT = LAIR = Lucro Líquido.

---

## Premissas operacionais — inputs manuais por ano

### Headcount

**Fixo em 3 funcionários** para toda a projeção 2026–2030. Não varia, não é
derivado — é input manual congelado.

| Ano  | N.º Funcionários |
|------|-----------------|
| 2026 | 3               |
| 2027 | 3               |
| 2028 | 3               |
| 2029 | 3               |
| 2030 | 3               |

---

## Ratios históricos — como calcular

Todos calculados sobre o período-base **2023, 2024 e 2025**, salvo exceção indicada.

### Valores de referência

| Ratio                  | 2023      | 2024      | 2025      | **Média (driver)** |
|------------------------|-----------|-----------|-----------|-------------------|
| Rem. Sócios / MC I     | 6,500%    | 6,500%    | 6,500%    | **6,500%**        |
| Outras ADM / RL        | 1,178%    | 1,034%    | 0,581%    | **0,931%**        |
| Custo/Func (R$/ano)    | 81.478,71 | 87.791,97 | 101.829,94| **base cascata**  |

**Nota sobre Outras Despesas Diretas:** historicamente zero nos três anos-base.
Ratio = 0%. Não há cálculo a fazer — zerar diretamente.

**Nota sobre Incentivos:** zero nos três anos-base e zerado nas projeções.

---

## Lógica de projeção — linha a linha

### Pré-cálculo: base para as cascatas

**Custo/Func base:**

```
Custo_Func_2025 = Gastos_Pessoal_2025 / N_Func_2025
               = 305.489,82 / 3
               = 101.829,94
```

Este é o `custo_func_ant` que entra no primeiro ciclo do loop (2026).

**FB base:**

```
FB_base = FB_2025 = 3.385.238,39
```

Este é o `fb_ant` que entra no primeiro ciclo do loop.

**Honorários base — janela deslizante de 3 anos:**

A janela começa com os três últimos anos históricos conhecidos:
`janela = [hon_2023, hon_2024, hon_2025] = [64.500, 66.000, 66.000]`

A cada ano projetado, o valor calculado entra na janela e o mais antigo sai.

---

### Loop por ano (2026, 2027, 2028, 2029, 2030)

#### 1. Fator de Reajuste

```
Fator(t) = 1 + inflação(t) + spread_real
         = 1 + inflação(t) + 0,02
```

**Atenção — soma simples, não produto composto.** A planilha usa adição direta
dos dois componentes, não `(1 + inflação) × (1 + spread)`.

| Ano  | Inflação | Spread | Fator      |
|------|---------|--------|------------|
| 2026 | 3,97%   | 2%     | **1,0597** |
| 2027 | 3,80%   | 2%     | **1,0580** |
| 2028 | 3,50%   | 2%     | **1,0550** |
| 2029 | 3,50%   | 2%     | **1,0550** |
| 2030 | 3,50%   | 2%     | **1,0550** |

#### 2. Faturamento Bruto (cascata)

```
FB(t) = FB(t-1) × Fator(t)
```

Exemplo 2026: `3.385.238,39 × 1,0597 = 3.587.337,12`

Ao final de cada ano: `fb_ant = FB(t)`

| Ano  | FB           |
|------|-------------|
| 2026 | 3.587.337   |
| 2027 | 3.795.403   |
| 2028 | 4.004.150   |
| 2029 | 4.224.378   |
| 2030 | 4.456.719   |

#### 3. Impostos sobre Venda

```
ISV(t) = FB(t) × 17,43%
```

#### 4. Receita Líquida

```
RL(t) = FB(t) − ISV(t)
      = FB(t) × 82,57%
```

| Ano  | RL          |
|------|------------|
| 2026 | 2.962.064  |
| 2027 | 3.133.864  |
| 2028 | 3.306.227  |
| 2029 | 3.488.069  |
| 2030 | 3.679.913  |

#### 5. Reclassificação de Receitas e Despesas

```
Reclassificação = 0  (zerada em todas as projeções)
```

#### 6. Incentivos de Prospecção e Vendas

```
Incentivos = 0  (zerados nas projeções)
```

Havia R$ 42.687 em 2025, mas não é projetado.

#### 7. Gastos com Pessoal (cascata)

```
Custo_Func(t) = Custo_Func(t-1) × (1 + inflação(t) + 1%)
Gastos_Pessoal(t) = N_Func × Custo_Func(t)
                  = 3 × Custo_Func(t)
```

**Armadilha crítica:** a linha `Custo / Funcionário (R$)` exibida na seção de
premissas da planilha (linha 83) mostra o valor crescendo **só pela inflação**
(sem o +1% real). Esse valor está errado — é um bug de label na planilha.

O cálculo de Gastos com Pessoal usa **inflação + 1% real**, confirmado ao
dividir `Gastos_Pessoal / N_Func` em cada ano projetado:
`320.672,66 / 3 = 106.890,89 = 101.829,94 × 1,0497` ✓

Ao final de cada ano: `custo_func_ant = Custo_Func(t)`

| Ano  | Custo/Func (correto) | Gastos Pessoal |
|------|---------------------|---------------|
| 2026 | 106.890,89          | 320.672,66    |
| 2027 | 111.988,16          | 335.964,48 (aprox) |
| 2028 | 117.024,63          | 351.073,89 (aprox) |

Valores exatos da planilha para referência:

| Ano  | Gastos Pessoal |
|------|---------------|
| 2026 | 320.672,66    |
| 2027 | 336.064,95    |
| 2028 | 351.187,87    |
| 2029 | 366.991,33    |
| 2030 | 383.505,94    |

#### 8. Outras Despesas Diretas

```
Outras_Dir = 0  (historicamente zero, zerado nas projeções)
```

#### 9. Margem Contribuição I

```
MC I(t) = RL(t) − Incentivos − Gastos_Pessoal(t) − Outras_Dir
        = RL(t) − Gastos_Pessoal(t)
```

| Ano  | MC I        |
|------|------------|
| 2026 | 2.641.392  |
| 2027 | 2.797.799  |
| 2028 | 2.955.039  |
| 2029 | 3.121.078  |
| 2030 | 3.296.407  |

#### 10. Remuneração Direta dos Sócios

```
Rem_Socios(t) = MC I(t) × 6,5%
```

O ratio de 6,5% é absolutamente estável — idêntico nos três anos-base. Não é
uma média calculada; é um valor fixo declarado explicitamente na planilha.

| Ano  | Rem. Sócios |
|------|------------|
| 2026 | 171.690    |
| 2027 | 181.857    |
| 2028 | 192.078    |
| 2029 | 202.870    |
| 2030 | 214.266    |

#### 11. Margem Contribuição II

```
MC II(t) = MC I(t) − Rem_Socios(t)
         = MC I(t) × 93,5%
```

| Ano  | MC II       |
|------|------------|
| 2026 | 2.469.701  |
| 2027 | 2.615.942  |
| 2028 | 2.762.961  |
| 2029 | 2.918.208  |
| 2030 | 3.082.140  |

#### 12. Outras Despesas Administrativas

```
Outras_ADM(t) = RL(t) × 0,9312%
```

Média aritmética simples de 2023, 2024 e 2025:

- 2023: 20.175,45 / 1.712.222,97 = 1,178%
- 2024: 20.606,90 / 1.991.988,59 = 1,034%
- 2025: 16.131,42 / 2.777.019,53 = 0,581%
- Média: **0,9312%**

Sub-linhas (14 Gastos Pessoal, 15 Tecnologia, 16 Eventos, 17 Marketing, etc.)
não são projetadas separadamente.

| Ano  | Outras ADM |
|------|-----------|
| 2026 | 27.584    |
| 2027 | 29.184    |
| 2028 | 30.789    |
| 2029 | 32.482    |
| 2030 | 34.269    |

#### 13. Rateio Administrativo

```
Rateio_ADM = input externo por ano
```

Vem da aba `DRE ADMINISTRATIVA`, proporcional ao headcount.
Na fase atual, usar os valores fixos da planilha:

| Ano  | Rateio ADM |
|------|-----------|
| 2026 | 145.525   |
| 2027 | 144.276   |
| 2028 | 144.050   |
| 2029 | 140.562   |
| 2030 | 139.458   |

#### 14. Honorários ADM Sócios Diretores (média móvel de 3 anos)

```
Honorários(t) = média(janela_3_anos)
```

A janela desliza a cada ano incorporando o valor calculado no ano anterior.

Inicialização: `janela = [hon_2023, hon_2024, hon_2025] = [64.500, 66.000, 66.000]`

Ao final de cada ano: `janela = janela[1:] + [honorarios_calculado]`

Verificação:
- 2026 = (64.500 + 66.000 + 66.000) / 3 = **65.500** ✓
- 2027 = (66.000 + 66.000 + 65.500) / 3 = **65.833,33** ✓
- 2028 = (66.000 + 65.500 + 65.833,33) / 3 = **65.777,78** ✓
- 2029 = (65.500 + 65.833,33 + 65.777,78) / 3 = **65.703,70** ✓
- 2030 = (65.833,33 + 65.777,78 + 65.703,70) / 3 = **65.771,60** ✓

| Ano  | Honorários |
|------|-----------|
| 2026 | 65.500,00 |
| 2027 | 65.833,33 |
| 2028 | 65.777,78 |
| 2029 | 65.703,70 |
| 2030 | 65.771,60 |

#### 15. EBITDA

```
EBITDA(t) = MC II(t) − Outras_ADM(t) − Rateio_ADM(t) − Honorários(t)
```

| Ano  | EBITDA      |
|------|------------|
| 2026 | 2.231.092  |
| 2027 | 2.376.649  |
| 2028 | 2.522.345  |
| 2029 | 2.679.460  |
| 2030 | 2.842.643  |

#### 16. Depreciação / Amortização

```
D&A = 0
```

#### 17. EBIT

```
EBIT(t) = EBITDA(t)
```

#### 18. Receita Financeira

```
Receita_Financeira = 0
```

#### 19. Despesa Financeira

```
Despesa_Financeira = 0
```

#### 20. LAIR

```
LAIR(t) = EBIT(t)
```

#### 21. IRPJ / CSLL

```
IRPJ_CSLL = 0  (alíquota = 0%)
```

#### 22. Lucro Líquido

```
Lucro_Liquido(t) = LAIR(t)
```

Igual ao EBITDA para todos os anos.

---

## Output esperado

Colunas do DataFrame resultado, nesta ordem:

```
bu, ano, n_funcionarios, inflacao_focus, fator_reajuste,
custo_por_func, fb_ant,
faturamento_bruto, impostos_sv, receita_liquida,
incentivos, gastos_pessoal, outras_desp_diretas,
mc1, mc1_pct_rl,
remuneracao_socios,
mc2, mc2_pct_rl,
outras_desp_adm, rateio_adm, honorarios_adm,
ebitda, ebitda_pct_rl,
ebit, lair, irpj_csll, lucro_liquido
```

O CSV de saída é gravado em `projecoes/projecao_renovacao.csv`.

---

## Validação — gabarito completo

Tolerância: diferença absoluta < R$ 1,00 por célula.

| Linha          | 2026      | 2027      | 2028      | 2029      | 2030      |
|----------------|-----------|-----------|-----------|-----------|-----------|
| Faturamento Bruto | 3.587.337 | 3.795.403 | 4.004.150 | 4.224.378 | 4.456.719 |
| Receita Líquida   | 2.962.064 | 3.133.864 | 3.306.227 | 3.488.069 | 3.679.913 |
| Gastos com Pessoal| 320.673   | 336.065   | 351.188   | 366.991   | 383.506   |
| MC I              | 2.641.392 | 2.797.799 | 2.955.039 | 3.121.078 | 3.296.407 |
| Rem. Sócios       | 171.690   | 181.857   | 192.078   | 202.870   | 214.266   |
| MC II             | 2.469.701 | 2.615.942 | 2.762.961 | 2.918.208 | 3.082.140 |
| Outras ADM        | 27.584    | 29.184    | 30.789    | 32.482    | 34.269    |
| Rateio ADM        | 145.525   | 144.276   | 144.050   | 140.562   | 139.458   |
| Honorários        | 65.500    | 65.833    | 65.778    | 65.704    | 65.772    |
| EBITDA = LL       | 2.231.092 | 2.376.649 | 2.522.345 | 2.679.460 | 2.842.643 |

### Diagnóstico de desvios

Se o FB divergir → verificar se o fator está sendo calculado como **soma simples**
`1 + inflação + 0,02` e não como produto `(1 + inflação) × (1 + 0,02)`.

Se a RL bater mas o MC I divergir → quase certamente o Custo/Func está usando
**apenas inflação** sem o +1% real. Dividir `Gastos_Pessoal_projetado / 3` e
comparar com `Custo_2025 × (1 + inf + 0,01)` para confirmar.

Se o MC I bater mas o MC II divergir → ratio de Rem. Sócios deve ser exatamente
**6,5%**, não uma média calculada que pode ter imprecisão de arredondamento.

Se o MC II bater mas o EBITDA divergir → verificar Honorários. Confirmar que a
janela deslizante usa 3 anos (não 4 como na AMS) e que a inicialização parte de
`[64.500, 66.000, 66.000]` (2023, 2024, 2025).

---

## Diferenças estruturais em relação à FOPM e AMS

| Aspecto                  | FOPM                    | AMS                        | Renovação              |
|--------------------------|-------------------------|----------------------------|------------------------|
| Driver de receita        | Bottom-up NFs × Ticket  | Base retida + Incremental  | Só base retida × fator |
| Dependência externa      | Nenhuma                 | FB FOPM obrigatório        | **Nenhuma**            |
| Headcount                | Input manual variável   | Derivado das NFs           | **Fixo em 3**          |
| Alíquota ISV             | 17,43%                  | 12,30%                     | **17,43%**             |
| Fórmula do fator reajuste| N/A                     | Produto composto           | **Soma simples**       |
| Custo/Func               | Inflação + 1% real      | Inflação + 1% real         | Inflação + 1% real (*label errado na planilha*) |
| Outras Desp. Diretas     | Ratio × RL              | Ratio × RL                 | **Zero**               |
| Incentivos               | Ratio × RL              | Zero                       | **Zero**               |
| Honorários ADM           | Cascata de inflação     | Média móvel 4 anos         | **Média móvel 3 anos** |
| D&A                      | Zero                    | Sim (ratio × horas)        | **Zero**               |
| Financeiras              | Zero                    | Sim (valores históricos)   | **Zero**               |
| IRPJ/CSLL                | 0%                      | 34% sobre LAIR             | **0%**                 |

---

## Armadilhas conhecidas

**Fator de reajuste é soma, não produto.** `1 + 0,0397 + 0,02 = 1,0597` — não
`(1 + 0,0397) × (1 + 0,02) = 1,060494`. A diferença parece pequena mas gera
divergência de ~R$ 2.688 no FB 2026 e acumula nos anos seguintes.

**O label `Custo / Funcionário (R$)` na planilha está errado.** A linha 83 da
aba exibe o custo crescendo só pela inflação (sem +1% real), mas o cálculo de
Gastos com Pessoal usa inflação + 1%. Implementar sempre com `× (1 + inf + 0,01)`.

**Honorários usam janela de 3 anos, não 4.** A AMS usa 4 anos; a Renovação usa 3.
Misturar os dois dá honorários errados a partir de 2028.

**A Renovação não depende de nenhuma outra BU.** Ao contrário da AMS (que precisa
do FB FOPM), a Renovação pode ser projetada de forma completamente independente.
No orquestrador, pode rodar em qualquer ordem.
