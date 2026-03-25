"""Roteamento de intenção e entidades para o agente financeiro."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Intent(str, Enum):
    IMPACT_MARGIN_CONSOLIDATED = "impact_margin_consolidated"
    IMPACT_MARGIN_YEAR_BY_YEAR = "impact_margin_year_by_year"
    TIMESERIES_AMS_FATURAMENTO = "timeseries_ams_faturamento"
    MARGIN_BU_BY_YEAR = "margin_bu_by_year"
    COMPARE_GROWTH = "compare_growth"
    VALUATION_EV_EBITDA = "valuation_ev_ebitda"
    TABLE_METRIC_BU_YEARS = "table_metric_bu_years"
    EV_VS_EQUITY = "ev_vs_equity"
    BU_REVENUE_SHARE_CHANGE = "bu_revenue_share_change"
    HISTORICAL_BU_METRIC = "historical_bu_metric"
    PROJECTION_BU_METRIC_YEAR = "projection_bu_metric_year"
    GENERIC = "generic"


@dataclass(frozen=True)
class RoutedIntent:
    intent: Intent
    score: float
    entities: dict[str, Any]


def _has_any(q: str, *phrases: str) -> bool:
    return any(p in q for p in phrases)


def route_question(question: str) -> RoutedIntent:
    q = question.lower().strip()
    entities: dict[str, Any] = {}
    bu_aliases = {
        "fopm": "fopm",
        "renovacao": "renovacao",
        "renovação": "renovacao",
        "ams": "ams",
        "venda sw": "venda_sw",
        "venda software": "venda_sw",
        "data science": "data_science",
        "datascience": "data_science",
    }
    mentioned_bus = [norm for alias, norm in bu_aliases.items() if alias in q]
    if mentioned_bus:
        entities["bus_mentioned"] = sorted(set(mentioned_bus))

    year_match = re.findall(r"\b(20[12][0-9]|2030)\b", q)
    for y in year_match:
        iy = int(y)
        if 2018 <= iy <= 2030:
            entities.setdefault("years_mentioned", []).append(iy)
    if entities.get("years_mentioned"):
        entities["years_mentioned"] = sorted(set(entities["years_mentioned"]))

    # Projeção: métrica por BU e ano (2026-2030)
    if "fopm" in q and _has_any(q, "receita", "faturamento"):
        for y in (2026, 2027, 2028, 2029, 2030):
            if str(y) in q:
                entities["year"] = y
                entities["bu"] = "fopm"
                entities["metric"] = "receita_liquida" if "receita" in q else "receita_bruta"
                return RoutedIntent(Intent.PROJECTION_BU_METRIC_YEAR, 0.9, entities)

    # Historical (2018-2025): receita/faturamento por BU
    if "fopm" in q and ("receita" in q or "faturamento" in q):
        for cand in (2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018):
            if str(cand) in q and cand <= 2025:
                entities["historical_year"] = cand
                entities["historical_bu"] = "fopm"
                entities["historical_metric"] = "receita_liquida" if "receita" in q else "receita_bruta"
                return RoutedIntent(Intent.HISTORICAL_BU_METRIC, 0.92, entities)

    # EV vs Equity
    if _has_any(q, "equity", "enterprise") and _has_any(q, "diferen", "por que", "porque", "why"):
        return RoutedIntent(Intent.EV_VS_EQUITY, 0.9, entities)

    # Valuation multiple
    if _has_any(q, "ev/ebitda", "ev ebitda", "múltiplo", "multiplo", "implicito", "implícito") and _has_any(
        q, "valuation", "dcf", "valor"
    ):
        return RoutedIntent(Intent.VALUATION_EV_EBITDA, 0.88, entities)

    # Table EBITDA por BU todos os anos
    if "tabela" in q and ("bu" in q or "bus" in q) and ("ebitda" in q or "margem" in q):
        return RoutedIntent(Intent.TABLE_METRIC_BU_YEARS, 0.9, {**entities, "metric": "ebitda"})

    # Compare growth FOPM vs Data Science
    if _has_any(q, "compar", "crescimento") and _has_any(q, "fopm", "data science", "datascience"):
        entities["bu_a"] = "fopm"
        entities["bu_b"] = "data_science"
        entities["metric"] = "receita_liquida" if "receita" in q else "ebitda"
        return RoutedIntent(Intent.COMPARE_GROWTH, 0.88, entities)

    # AMS faturamento evolution
    if "ams" in q and _has_any(q, "faturamento", "evolu", "2026", "2030"):
        return RoutedIntent(Intent.TIMESERIES_AMS_FATURAMENTO, 0.85, entities)

    # Margin by BU in year (e.g. 2028)
    if _has_any(q, "margem", "ebitda") and _has_any(q, "cada bu", "por bu", "cada bu") and any(
        str(y) in q for y in (2026, 2027, 2028, 2029, 2030)
    ):
        for y in (2026, 2027, 2028, 2029, 2030):
            if str(y) in q:
                entities["year"] = y
                break
        return RoutedIntent(Intent.MARGIN_BU_BY_YEAR, 0.87, entities)

    # BU that lost most revenue share
    if _has_any(q, "particip", "share", "perdeu", "perda", "mix") and _has_any(q, "receita", "rl"):
        return RoutedIntent(Intent.BU_REVENUE_SHARE_CHANGE, 0.86, entities)

    # Impact on consolidated margin — year by year
    if _has_any(q, "margem", "ebitda") and _has_any(
        q, "maior impacto", "impacto", "quem puxou", "bus", "bus ", "bus que"
    ):
        if _has_any(q, "negativ", "pior", "reduziu", "queda", "deterior"):
            entities["impact_direction"] = "negative"
        elif _has_any(q, "positiv", "melhor", "aumentou", "ganho"):
            entities["impact_direction"] = "positive"
        else:
            entities["impact_direction"] = "any"

        # Se a pergunta é focada em uma BU específica (ex.: FOPM) e não cita consolidado,
        # evita resposta determinística de ranking entre BUs.
        if entities.get("bus_mentioned") and "consolid" not in q:
            return RoutedIntent(Intent.GENERIC, 0.45, entities)

        if _has_any(q, "ano a ano", "ano-a-ano", "cada ano", "por ano", "informações ano"):
            return RoutedIntent(Intent.IMPACT_MARGIN_YEAR_BY_YEAR, 0.9, entities)
        return RoutedIntent(Intent.IMPACT_MARGIN_CONSOLIDATED, 0.88, entities)

    return RoutedIntent(Intent.GENERIC, 0.3, entities)
