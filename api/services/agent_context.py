from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .agent_tools import BU_KEYS, bu_revenue_share_change_ranking, get_margin_impact_consolidated


def compute_scenario_id(sim_result: dict[str, Any]) -> str:
    return hashlib.sha256(str(sim_result.get("premissas_efetivas", {})).encode("utf-8")).hexdigest()[:12]


def _derived_metrics_block(sim_result: dict[str, Any]) -> str:
    lines: list[str] = ["\n### Métricas derivadas (cenário atual)\n"]
    try:
        shares = bu_revenue_share_change_ranking(sim_result, 2026, 2030)
        if shares:
            lines.append("\n**Participação na RL consolidada (2026 vs 2030)**\n")
            for s in shares:
                lines.append(
                    f"- {s['bu_label']}: {s['share_start']*100:.1f}% → {s['share_end']*100:.1f}% "
                    f"(Δ {s['delta_pp']:+.2f} p.p.)"
                )
        imp = get_margin_impact_consolidated(sim_result, 2026, 2030)[:5]
        if imp:
            lines.append("\n**Δ EBITDA 2026→2030 vs RL consolidada (2030)** (aprox.)\n")
            for i in imp:
                lines.append(f"- {i['bu_label']}: {i['impact_pp']:+.2f} p.p.")
    except Exception:
        lines.append("\n(métricas derivadas indisponíveis)\n")
    return "\n".join(lines) + "\n"


def detect_intent(question: str) -> str:
    q = question.lower()
    if "múltiplo" in q or "multiplo" in q or "valuation" in q or "ev/ebitda" in q:
        return "valuation"
    if "compare" in q or "compar" in q:
        return "comparison"
    if "tabela" in q:
        return "table"
    if "evolu" in q or "entre" in q:
        return "timeseries"
    return "generic"


def _fmt_num(value: Any) -> str:
    try:
        return f"{float(value):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "-"


def _fmt_pct(value: Any) -> str:
    try:
        v = float(value)
        # algumas colunas vêm em base 0-1 e outras já em %
        if abs(v) <= 1.0:
            v *= 100
        return f"{v:.1f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "-"


def _build_system_context(simulation_data: dict[str, Any]) -> str:
    context = """Voce e um analista financeiro especializado em DRE/DCF. Dados da projecao atual:

## RESUMO EXECUTIVO
"""
    consolidado = simulation_data.get("consolidado", [])
    if consolidado:
        context += "\n### DRE Consolidada (valores nominais)\n\n"
        context += "| Ano | Fat. Bruto | Receita Liquida | EBITDA | Mg EBITDA | Lucro Liquido |\n"
        context += "|-----|------------|-----------------|--------|-----------|---------------|\n"
        for row in consolidado:
            context += (
                f"| {row.get('ano', '-')} "
                f"| {_fmt_num(row.get('faturamento_bruto'))} "
                f"| {_fmt_num(row.get('receita_liquida'))} "
                f"| {_fmt_num(row.get('ebitda'))} "
                f"| {_fmt_pct(row.get('ebitda_pct_rl'))} "
                f"| {_fmt_num(row.get('lucro_liquido'))} |\n"
            )

    context += "\n### Metricas por BU (2026 vs 2030)\n\n"
    context += "| BU | Metrica | 2026 | 2030 | Delta % |\n"
    context += "|----|---------|------|------|---------|\n"

    dre = simulation_data.get("dre", {})
    for bu_name in BU_KEYS:
        bu_data = dre.get(bu_name, [])
        if not bu_data:
            continue
        inicio = next((r for r in bu_data if int(r.get("ano", -1)) == 2026), None)
        fim = next((r for r in bu_data if int(r.get("ano", -1)) == 2030), None)
        if not inicio or not fim:
            continue

        fb_inicio = float(inicio.get("faturamento_bruto", 0) or 0)
        fb_fim = float(fim.get("faturamento_bruto", 0) or 0)
        delta_fb = ((fb_fim / fb_inicio - 1) * 100) if fb_inicio else 0
        context += (
            f"| {bu_name.upper()} | Fat. Bruto | {_fmt_num(fb_inicio)} | {_fmt_num(fb_fim)} "
            f"| {delta_fb:+.1f}% |\n"
        )

        ebitda_inicio = float(inicio.get("ebitda", 0) or 0)
        ebitda_fim = float(fim.get("ebitda", 0) or 0)
        delta_ebitda = ((ebitda_fim / ebitda_inicio - 1) * 100) if ebitda_inicio else 0
        context += (
            f"| {bu_name.upper()} | EBITDA | {_fmt_num(ebitda_inicio)} | {_fmt_num(ebitda_fim)} "
            f"| {delta_ebitda:+.1f}% |\n"
        )

    dcf = simulation_data.get("dcf", {})
    if dcf:
        context += "\n### Valuation (DCF)\n\n"
        context += f"- Enterprise Value: {_fmt_num(dcf.get('enterprise_value'))}\n"
        context += f"- Equity Value: {_fmt_num(dcf.get('equity_value'))}\n"
        multiplos = dcf.get("multiplos", {})
        ev_ebitda = next((v for k, v in multiplos.items() if "EV_EBITDA" in k), None)
        if ev_ebitda is not None:
            context += f"- EV/EBITDA implicito: {float(ev_ebitda):.2f}x\n"
        context += f"- WACC: {_fmt_pct(dcf.get('wacc'))}\n"
        context += f"- g perpetuidade: {_fmt_pct(dcf.get('g'))}\n"

    premissas = simulation_data.get("premissas_efetivas", {})
    if premissas:
        context += "\n### Premissas-chave utilizadas\n\n"
        fopm_prem = premissas.get("fopm", {})
        hc = fopm_prem.get("headcount_por_ano", {})
        if hc:
            context += f"- FOPM Headcount: 2026={hc.get('2026', hc.get(2026))}, 2030={hc.get('2030', hc.get(2030))}\n"
        ren = premissas.get("renovacao", {})
        if ren:
            context += f"- Renovacao Churn: {_fmt_pct(ren.get('churn'))}\n"
            context += f"- Renovacao Spread Real: {_fmt_pct(ren.get('spread_real'))}\n"
        ams = premissas.get("ams", {})
        if ams:
            context += f"- AMS Taxa Conversao FOPM: {_fmt_pct(ams.get('taxa_conversao_fopm'))}\n"
            context += f"- AMS Churn: {_fmt_pct(ams.get('churn'))}\n"

    context += _derived_metrics_block(simulation_data)

    context += """

## SUA FUNCAO

Ao responder:
1. Use os dados acima e cite valores concretos.
2. Compare tendencias e destaque drivers relevantes.
3. Seja quantitativo sempre que possivel.
4. Explique por que o numero importa para o negocio.
5. So gere tabela/grafico se o usuario pedir explicitamente.
"""
    return context


def build_agent_context(
    sim_result: dict[str, Any],
    question: str,
    history: list[dict[str, str]],
    router_intent: str | None = None,
) -> dict[str, Any]:
    intent = detect_intent(question)
    scenario_id = compute_scenario_id(sim_result)
    base = {
        "meta_context": {
            "model_version": "sim-v1",
            "currency": "BRL",
            "years": [2026, 2027, 2028, 2029, 2030],
            "bus": BU_KEYS,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "intent_hint": intent,
            "router_intent": router_intent,
            "scenario_id": scenario_id,
            "definitions": {
                "margem_ebitda": "ebitda / receita_liquida",
                "fcff": "nopat + da_total - capex - delta_ncg",
            },
        },
        "conversation_context": {
            "history_summary": [f'{item.get("role", "user")}: {item.get("content", "")[:120]}' for item in history[-6:]],
        },
        "system_context_markdown": _build_system_context(sim_result),
    }

    if intent == "valuation":
        base["data_context"] = {"dcf": sim_result.get("dcf", {}), "consolidado": sim_result.get("consolidado", [])}
    elif intent in {"comparison", "timeseries", "table"}:
        base["data_context"] = {"dre": sim_result.get("dre", {}), "consolidado": sim_result.get("consolidado", [])}
    else:
        base["data_context"] = {
            "dcf": sim_result.get("dcf", {}),
            "dre": sim_result.get("dre", {}),
            "consolidado": sim_result.get("consolidado", []),
            "fluxo": sim_result.get("fluxo", []),
        }
    return base
