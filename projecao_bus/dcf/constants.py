"""Premissas e gabaritos do plano_implementacao_dcf.md."""

from __future__ import annotations

from ..year_config import get_projected_years

# --- Balanço / NCG ---
PMCR_DIAS = 40
PMIP_DIAS = 30
DIAS_ANO = 360

RATIO_FORNECEDORES = 0.00439476386325896
# Rácio usado exclusivamente na série `default_custos_excl_pessoal_gabarito` (premissas.defaults).
RATIO_FORNECEDORES_CUSTOS_EXCL_GABARITO = 0.004961
RATIO_OBRIG_TRABALHISTAS = 0.0354456683379581
RATIO_PROVISOES = 0.0801166034199223

ADIANTAMENTOS = 95_336.2
IMPOSTOS_RECUPERAR = 214_910.0
OUTROS_AC = 14_921.8
PARTES_RELACIONADAS = 0.0
OUTRAS_OBRIGACOES = -94_208.8
RECEITAS_DIFERIDAS = 155_506.8

# CAPEX de expansão: R$ 15.000 / funcionário novo (base nominal).
# O reajuste ano a ano é ∏(1 + inflação Focus[j], j=2026..ano) — ver `dcf/bp.py`.
CAPEX_BASE_POR_FUNC_NOVO = 15_000.0
TAXA_DEPRECIACAO_CAPEX = 0.20
ANOS_DEPRECIACAO_CAPEX = 5

IMOBILIZADO_BASE_2025 = 2_445_435.0
DEPR_ACUM_BASE_2025 = -1_561_883.0

NCG_BASE_2025 = 4_514_000.0

# Gabarito AC_op / PC_op / NCG 2025 (histórico)
AC_OP_2025 = 7_477_000.0
PC_OP_2025 = 2_963_000.0

# Séries gabarito → use `SimulationContext` / `premissas.defaults` (evita estado global).

# --- Fluxo / DCF ---
CAIXA_BASE_2025 = 2_291_962.0
MESES_RESERVA_CAIXA = 4

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

def get_anos_projecao() -> tuple[int, ...]:
    """Anos projetados ativos (dinamico)."""
    return get_projected_years()
