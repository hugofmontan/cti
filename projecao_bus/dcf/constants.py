"""Premissas e gabaritos do plano_implementacao_dcf.md."""

from __future__ import annotations

# --- Balanço / NCG ---
PMCR_DIAS = 40
PMIP_DIAS = 30
DIAS_ANO = 360

RATIO_FORNECEDORES = 0.004961
RATIO_OBRIG_TRABALHISTAS = 0.038584
RATIO_PROVISOES = 0.080117

ADIANTAMENTOS = 116_400.0
IMPOSTOS_RECUPERAR = 286_600.0
OUTROS_AC = 13_600.0
PARTES_RELACIONADAS = 0.0
OUTRAS_OBRIGACOES = -114_600.0
RECEITAS_DIFERIDAS = 217_600.0

# CAPEX de expansão: R$ 15.000 / funcionário novo (base nominal).
# O reajuste ano a ano é ∏(1 + inflação Focus[j], j=2026..ano) — ver `dcf/bp.py`.
CAPEX_BASE_POR_FUNC_NOVO = 15_000.0
TAXA_DEPRECIACAO_CAPEX = 0.20
ANOS_DEPRECIACAO_CAPEX = 5

IMOBILIZADO_BASE_2025 = 2_491_000.0
DEPR_ACUM_BASE_2025 = -1_663_000.0

NCG_BASE_2025 = 4_514_000.0

# Gabarito AC_op / PC_op / NCG 2025 (histórico)
AC_OP_2025 = 7_477_000.0
PC_OP_2025 = 2_963_000.0

# Custos excl. pessoal alinhados ao gabarito Fornecedores (Fornecedores / ratio)
# Fonte: planilha (L12+L23+outras do CONS.FORMATO PARCEIRO); aqui usa valores reversos do gabarito BP.
CUSTOS_EXCL_PESSOAL_GABARITO: dict[int, float] = {
    2026: 38_456 / RATIO_FORNECEDORES,
    2027: 46_180 / RATIO_FORNECEDORES,
    2028: 58_476 / RATIO_FORNECEDORES,
    2029: 63_351 / RATIO_FORNECEDORES,
    2030: 68_767 / RATIO_FORNECEDORES,
}

# Gastos com pessoal não alocado (consolidado_original.csv, linha 23, colunas 2026–2030)
PESSOAL_NAO_ALOCADO_ADM: dict[int, float] = {
    2026: 1_715_347.35,
    2027: 1_799_279.13,
    2028: 1_840_241.44,
    2029: 1_920_439.47,
    2030: 1_949_520.41,
}

# --- Fluxo / DCF ---
CAIXA_BASE_2025 = 8_018_000.0
PAYOUT_DIVIDENDOS = 0.50

WACC_FIXO = 0.1712411693119031
G_PERPETUIDADE = 0.035
DIVIDA_LIQUIDA = 0.0

# --- WACC (premissas de mercado) ---
RF_NTN_B = 0.06
ERP_EUA = 0.0446
CRP_BR = 0.0324
PRM = ERP_EUA + CRP_BR  # 0.077
PREM_TAMANHO = 0.03
PREM_LIQUIDEZ = 0.01
INF_BR = 0.035
INF_EUA = 0.02
ALIQUOTA_IR_CSLL_REF = 0.34

BETAS_DESALAVANCADOS: dict[str, float] = {
    "fopm": 1.031405,
    "renovacao": 0.995214,
    "ams": 0.814027,
    "venda_sw": 1.102833,
    "data_science": 1.106113,
}

# Beta ponderado por faturamento (gabarito plano, 2025–2030)
BETA_PONDERADO_GABARITO: dict[int, float] = {
    2025: 0.9725,
    2026: 0.9716,
    2027: 0.9751,
    2028: 0.9784,
    2029: 0.9814,
    2030: 0.9869,
}

ANOS_PROJECAO = (2026, 2027, 2028, 2029, 2030)

# Funcionários novos 2026 (gabarito BP) — base 2025 = Total_2026 − este valor
FUNC_NOVOS_2026_GABARITO = 26.019
