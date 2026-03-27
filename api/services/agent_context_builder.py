"""
Agent v2 — Context Builder.

Monta contexto compacto em JSON para o LLM.
Substitui o antigo agent_context.py (markdown narrativo pesado).
~800-1200 tokens em vez de ~3000-5000.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from api.agent_domain import BU_DRE_CODES, BU_LABELS, build_domain_reference
from api.services.projection_config import get_projection_years

BU_KEYS = BU_DRE_CODES


def compute_scenario_id(sim_json: dict[str, Any]) -> str:
    return hashlib.sha256(
        str(sim_json.get("premissas_efetivas", {})).encode("utf-8")
    ).hexdigest()[:12]


def build_agent_context(
    sim_json: dict[str, Any],
    historical_bundle: dict[str, Any] | None,
    premissas: dict[str, Any],
    history: list[dict[str, str]],
    scenario_id: str,
) -> dict[str, Any]:
    """
    Monta o contexto completo para o LLM.
    Retorna dict com blocos de estado + dados auxiliares para tools.
    """
    return {
        "current_state": _build_current_state(sim_json, premissas, scenario_id),
        "session": _build_session_context(history),

        # Dados completos (disponíveis para tools, não enviados inteiros ao LLM)
        "sim_json": sim_json,
        "historical_bundle": historical_bundle or {},
        "premissas": premissas,
        "scenario_id": scenario_id,

        "domain_reference": build_domain_reference(),
    }


def _get_row_for_year(rows: list[dict[str, Any]], year: int) -> dict[str, Any]:
    """Busca um registro por ano numa lista de dicts [{ano: ..., ...}]."""
    for row in rows:
        if int(row.get("ano", -1)) == year:
            return row
    return {}


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _build_current_state(
    sim_json: dict[str, Any],
    premissas: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    consolidado_rows = sim_json.get("consolidado", [])
    dre = sim_json.get("dre", {})
    dcf = sim_json.get("dcf", {})

    proj_years = get_projection_years()
    resumo_consolidado = {}
    for year in proj_years:
        row = _get_row_for_year(consolidado_rows, year)
        if not row:
            continue
        resumo_consolidado[str(year)] = {
            "faturamento_bruto": _safe_float(row.get("faturamento_bruto")),
            "receita_liquida": _safe_float(row.get("receita_liquida")),
            "ebitda": _safe_float(row.get("ebitda")),
            "margem_ebitda": _safe_float(row.get("ebitda_pct_rl")),
            "lucro_liquido": _safe_float(row.get("lucro_liquido")),
        }

    y_first, y_last = proj_years[0], proj_years[-1]
    resumo_bus = {}
    for bu in BU_KEYS:
        bu_rows = dre.get(bu, [])
        resumo_bus[bu] = {
            str(y_first): _extract_bu_snapshot(bu_rows, y_first),
            str(y_last): _extract_bu_snapshot(bu_rows, y_last),
        }

    resumo_dcf = {
        "enterprise_value": _safe_float(dcf.get("enterprise_value")),
        "equity_value": _safe_float(dcf.get("equity_value")),
        "wacc": _safe_float(dcf.get("wacc")),
        "g": _safe_float(dcf.get("g")),
    }
    multiplos = dcf.get("multiplos", {})
    ev_ebitda = next((v for k, v in multiplos.items() if "EV_EBITDA" in k), None)
    if ev_ebitda is not None:
        resumo_dcf["ev_ebitda_implicito"] = _safe_float(ev_ebitda)

    premissas_resumo = _flatten_premissas(premissas)

    return {
        "scenario_id": scenario_id,
        "currency": "BRL",
        "projection_years": proj_years,
        "bus": BU_KEYS,
        "bu_labels": BU_LABELS,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "consolidado": resumo_consolidado,
        "por_bu": resumo_bus,
        "dcf": resumo_dcf,
        "premissas_atuais": premissas_resumo,
    }


def _build_session_context(history: list[dict[str, str]]) -> dict[str, Any]:
    recent = history[-5:] if len(history) > 5 else history
    resumo = []
    for entry in recent:
        resumo.append({
            "role": entry.get("role", "user"),
            "content_preview": str(entry.get("content", ""))[:150],
        })
    return {
        "history_summary": resumo,
        "turn_count": len(history),
    }


def _extract_bu_snapshot(bu_rows: list[dict[str, Any]], year: int) -> dict[str, Any]:
    row = _get_row_for_year(bu_rows, year)
    return {
        "faturamento_bruto": _safe_float(row.get("faturamento_bruto")),
        "receita_liquida": _safe_float(row.get("receita_liquida")),
        "ebitda": _safe_float(row.get("ebitda")),
        "margem_ebitda": _safe_float(row.get("ebitda_pct_rl")),
    }


def _flatten_premissas(premissas: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for bu_key, bu_val in premissas.items():
        if isinstance(bu_val, dict):
            for param, value in bu_val.items():
                flat[f"{bu_key}.{param}"] = value
        else:
            flat[bu_key] = bu_val
    return flat
