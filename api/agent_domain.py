"""
Referência de domínio única para o agente (prompt + contexto LLM).

Evita duplicar tabelas em Markdown; o JSON enviado na mensagem do usuário é a fonte da verdade.
"""

from __future__ import annotations

from typing import Any

# Códigos de BU usados na DRE / query_data (fatia `dre[bu]`).
BU_DRE_CODES = ["fopm", "renovacao", "ams", "venda_sw", "data_science"]

BU_LABELS: dict[str, str] = {
    "fopm": "FOPM",
    "renovacao": "Renovação",
    "ams": "AMS",
    "venda_sw": "Venda SW",
    "data_science": "Data Science",
}

# Raiz de premissas no payload (run_simulation / API). venda_sw é só rótulo da DRE; premissas usam venda_softwares.
BU_PREMISSA_SCHEMA: dict[str, list[str]] = {
    "fopm": ["headcount_por_ano", "ociosidade_por_ano"],
    "renovacao": ["churn", "spread_real"],
    "ams": ["taxa_conversao_fopm", "churn"],
    "venda_softwares": ["fator_crescimento_real"],
    "data_science": ["headcount_por_ano", "ociosidade_por_ano"],
    "dcf": ["wacc", "g"],
}

METRIC_DEFINITIONS: dict[str, str] = {
    "headcount": "métrica canônica de funcionários (alias: n_funcionarios)",
    "margem_ebitda": "ebitda / receita_liquida",
    "derivadas_sufixo": (
        "<metrica>_delta_pct, <metrica>_cagr, <metrica>_yoy_pct; "
        "para variação anual % use preferencialmente <metrica>_yoy_pct"
    ),
    "fcff": "nopat + da_total - capex - delta_ncg",
    "nopat": "ebit × (1 - aliquota_ir)",
    "enterprise_value": "soma dos FCFFs descontados + valor terminal",
    "equity_value": "enterprise_value - divida_liquida",
    "ev_ebitda_implicito": "enterprise_value / ebitda_ultimo_ano",
}

# Chaves em dot-notation alinhadas ao merge de premissas (run_simulation).
PREMISSA_RANGES: dict[str, dict[str, Any]] = {
    "renovacao.churn": {"pessimista": 0.25, "base": 0.15, "otimista": 0.08, "unit": "ratio"},
    "renovacao.spread_real": {"pessimista": 0.01, "base": 0.03, "otimista": 0.05, "unit": "ratio"},
    "ams.churn": {"pessimista": 0.20, "base": 0.12, "otimista": 0.05, "unit": "ratio"},
    "ams.taxa_conversao_fopm": {"pessimista": 0.10, "base": 0.20, "otimista": 0.35, "unit": "ratio"},
    "venda_softwares.fator_crescimento_real": {"pessimista": 0.02, "base": 0.05, "otimista": 0.10, "unit": "ratio"},
    "dcf.wacc": {"pessimista": 0.16, "base": 0.12, "otimista": 0.09, "unit": "ratio"},
    "dcf.g": {"pessimista": 0.02, "base": 0.035, "otimista": 0.05, "unit": "ratio"},
}

MOTOR_SUMMARY_BULLETS: list[str] = [
    "FOPM / Data Science: receita = f(headcount, ociosidade, ticket)",
    "Renovação: receita = base_renovável × (1 - churn) × (1 + spread_real)",
    "AMS: receita = base_ams × (1 - churn) + conversão_fopm × taxa_conversao",
    "Venda SW: receita = base × (1 + fator_crescimento_real)",
    "Consolidado = soma das BUs; DCF desconta FCFF a WACC com perpetuidade a g",
]

# Nota para o LLM: tools ainda aceitam venda_sw.*; executor normaliza para venda_softwares.*.
PREMISSA_ALIASES_NOTE = (
    "Em premissa_changes, venda_sw.fator_crescimento_real é aceito e mapeado para venda_softwares.fator_crescimento_real."
)


def build_domain_reference() -> dict[str, Any]:
    return {
        "bu_dre_codes": BU_DRE_CODES,
        "bu_labels": BU_LABELS,
        "bu_premissa_schema": BU_PREMISSA_SCHEMA,
        "metric_definitions": METRIC_DEFINITIONS,
        "premissa_ranges": PREMISSA_RANGES,
        "motor_projection_summary": MOTOR_SUMMARY_BULLETS,
        "premissa_aliases": PREMISSA_ALIASES_NOTE,
    }
