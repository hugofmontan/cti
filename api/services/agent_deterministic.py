"""Respostas determinísticas (dados do motor) por intenção."""

from __future__ import annotations

from typing import Any

from api.schemas import AgentQueryResponse, ArtifactChart, ArtifactChartSeries, ArtifactKPI, ArtifactTable

from .agent_intent import Intent, RoutedIntent
from .agent_tools import (
    bu_revenue_share_change_ranking,
    build_pivot_table,
    compare_bus_growth,
    extract_ev_ebitda_implicit,
    explain_equity_vs_enterprise,
    get_historical_metric_for_bu,
    get_margin_by_bu_year,
    get_margin_impact_consolidated,
    get_timeseries,
    margin_impact_year_by_year,
)


def execute_deterministic(
    routed: RoutedIntent,
    question: str,
    sim_result: dict[str, Any],
    historical_bundle: dict[str, Any] | None,
    scenario_id: str,
    wants_visual: bool,
) -> AgentQueryResponse | None:
    intent = routed.intent
    ent = routed.entities
    q = question.lower()

    if intent == Intent.HISTORICAL_BU_METRIC and historical_bundle:
        bu = str(ent.get("historical_bu", "fopm"))
        year = int(ent.get("historical_year", 2025))
        metric = str(ent.get("historical_metric", "receita_liquida"))
        val = get_historical_metric_for_bu(historical_bundle, bu, year, metric)
        if val is None:
            return AgentQueryResponse(
                answer_markdown=f"Não encontrei `{metric}` de **{bu.upper()}** em **{year}** no histórico (`data/original`).",
                confidence="medium",
                response_source="deterministic",
                intent=intent.value,
                scenario_id=scenario_id,
                warnings=[f"Fonte: historical_dre ({year})."],
            )
        label = "Receita líquida" if metric == "receita_liquida" else "Faturamento bruto"
        return AgentQueryResponse(
            answer_markdown=(
                f"**{label}** da **FOPM** em **{year}** (histórico, `data/original`): **{val:,.2f}**."
            ),
            confidence="high",
            data_used=[f"historical.dre.{bu}.{metric}[{year}]"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.PROJECTION_BU_METRIC_YEAR:
        bu = str(ent.get("bu", "fopm"))
        year = int(ent.get("year", 2026))
        metric = str(ent.get("metric", "receita_liquida"))
        row = next(
            (r for r in sim_result.get("dre", {}).get(bu, []) if int(r.get("ano", -1)) == year),
            None,
        )
        if not row:
            return None
        val = row.get(metric)
        if val is None:
            return None
        return AgentQueryResponse(
            answer_markdown=(
                f"**{metric}** da **{bu.upper()}** em **{year}** (projeção atual): **{float(val):,.2f}**."
            ),
            confidence="high",
            data_used=[f"dre.{bu}.{metric}[{year}]"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.IMPACT_MARGIN_CONSOLIDATED:
        impacts = get_margin_impact_consolidated(sim_result, 2026, 2030)
        direction = str(ent.get("impact_direction", "any"))
        if direction == "negative":
            impacts = [i for i in impacts if i["impact_pp"] < 0]
            impacts.sort(key=lambda x: x["impact_pp"])
        elif direction == "positive":
            impacts = [i for i in impacts if i["impact_pp"] > 0]
            impacts.sort(key=lambda x: x["impact_pp"], reverse=True)
        top = impacts[:5]
        if not top:
            return AgentQueryResponse(
                answer_markdown=(
                    "No cenário atual (**2026→2030**), não encontrei BUs com "
                    f"impacto **{direction if direction != 'any' else 'relevante'}** na margem EBITDA consolidada "
                    "pelo critério ΔEBITDA / RL consolidada de 2030."
                ),
                confidence="medium",
                response_source="deterministic",
                intent=intent.value,
                scenario_id=scenario_id,
                warnings=["Sem ocorrências para o filtro de direção solicitado."],
            )
        bullets = "\n".join(
            [f"- **{item['bu_label']}**: **{item['impact_pp']:+.2f} p.p.** (Δ EBITDA ≈ {item['delta_ebitda']:,.0f})" for item in top]
        )
        direction_label = {"positive": "positivo", "negative": "negativo"}.get(direction, "estimado")
        return AgentQueryResponse(
            answer_markdown=(
                f"BUs com maior **impacto {direction_label}** na margem EBITDA consolidada (**2026→2030**), "
                "usando Δ EBITDA da BU em relação à **receita líquida consolidada de 2030**:\n\n"
                f"{bullets}\n\n"
                "_Método: soma dos ΔEBITDA por BU no período, impacto em p.p. = ΔEBITDA / RL consolidado (2030)._"
            ),
            confidence="high",
            data_used=["dre.*.ebitda", "consolidado.receita_liquida"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.IMPACT_MARGIN_YEAR_BY_YEAR:
        detail = margin_impact_year_by_year(sim_result, 2026, 2030)
        if not detail:
            return None
        direction = str(ent.get("impact_direction", "any"))
        # Top 3 BUs per year by abs impact
        years = sorted({r["year"] for r in detail})
        lines: list[str] = []
        for y in years:
            chunk = [r for r in detail if r["year"] == y]
            if direction == "negative":
                chunk = [r for r in chunk if r["impact_pp"] < 0]
                chunk.sort(key=lambda x: x["impact_pp"])
            elif direction == "positive":
                chunk = [r for r in chunk if r["impact_pp"] > 0]
                chunk.sort(key=lambda x: x["impact_pp"], reverse=True)
            else:
                chunk.sort(key=lambda x: abs(x["impact_pp"]), reverse=True)
            if not chunk:
                continue
            top3 = chunk[:3]
            sub = ", ".join(f"{t['bu_label']} ({t['impact_pp']:+.2f} p.p.)" for t in top3)
            lines.append(f"- **{y}** (vs {y-1}): {sub}")
        if not lines:
            return AgentQueryResponse(
                answer_markdown="Não houve impactos com a direção solicitada no recorte ano a ano (2027–2030).",
                confidence="medium",
                response_source="deterministic",
                intent=intent.value,
                scenario_id=scenario_id,
                warnings=["Filtro de direção sem ocorrências no período."],
            )
        body = "\n".join(lines)
        return AgentQueryResponse(
            answer_markdown=(
                "**Impacto na margem consolidada** (aproximação ano a ano): para cada ano, "
                "ΔEBITDA da BU vs ano anterior, em pontos percentuais da RL consolidada daquele ano:\n\n"
                f"{body}"
            ),
            confidence="high",
            data_used=["dre.*.ebitda", "consolidado.receita_liquida"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.TIMESERIES_AMS_FATURAMENTO:
        ts = get_timeseries(sim_result, "ams", "receita_bruta", 2026, 2030)
        if not ts:
            ts = get_timeseries(sim_result, "ams", "faturamento_bruto", 2026, 2030)
        if not ts:
            return None
        first, last = ts[0]["value"], ts[-1]["value"]
        growth = ((last / first) - 1) * 100 if first else 0
        tbl = "\n".join([f"| {int(t['year'])} | {t['value']:,.1f} |" for t in ts])
        arts: list[Any] = []
        if wants_visual:
            arts = [
                ArtifactChart(
                    title="AMS — faturamento (2026-2030)",
                    chart_type="line",
                    x=[t["year"] for t in ts],
                    series=[ArtifactChartSeries(name="AMS", values=[t["value"] for t in ts])],
                    unit="BRL",
                )
            ]
        return AgentQueryResponse(
            answer_markdown=(
                f"Evolução do **faturamento (receita bruta)** da **AMS** (**2026–2030**):\n\n"
                f"| Ano | R$ |\n|---:|---:|\n{tbl}\n\n"
                f"Variação **{2026}→{2030}**: **{growth:+.1f}%**."
            ),
            artifacts=arts,
            confidence="high",
            data_used=["dre.ams.faturamento_bruto"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.MARGIN_BU_BY_YEAR:
        year = int(ent.get("year", 2028))
        if str(year) not in q and year not in (2026, 2027, 2028, 2029, 2030):
            for y in (2026, 2027, 2028, 2029, 2030):
                if str(y) in q:
                    year = y
                    break
        points = get_margin_by_bu_year(sim_result, year)
        if not points:
            return None
        lines = "\n".join([f"- **{p['bu_label']}**: **{p['margin']*100:.2f}%**" for p in points])
        return AgentQueryResponse(
            answer_markdown=f"**Margem EBITDA** por BU em **{year}** (projeção):\n\n{lines}",
            confidence="high",
            data_used=[f"dre.*.ebitda_pct_rl[{year}]"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.COMPARE_GROWTH:
        bu_a = str(ent.get("bu_a", "fopm"))
        bu_b = str(ent.get("bu_b", "data_science"))
        metric = str(ent.get("metric", "receita_liquida"))
        comp = compare_bus_growth(sim_result, metric, bu_a, bu_b, 2026, 2030)
        ga, gb = comp["bu_a"]["growth"], comp["bu_b"]["growth"]
        arts: list[Any] = []
        if wants_visual:
            arts = [
                ArtifactChart(
                    title=f"{metric}: {comp['bu_a']['label']} vs {comp['bu_b']['label']}",
                    chart_type="line",
                    x=[t["year"] for t in comp["bu_a"]["series"]],
                    series=[
                        ArtifactChartSeries(
                            name=comp["bu_a"]["label"],
                            values=[t["value"] for t in comp["bu_a"]["series"]],
                        ),
                        ArtifactChartSeries(
                            name=comp["bu_b"]["label"],
                            values=[t["value"] for t in comp["bu_b"]["series"]],
                        ),
                    ],
                    unit="BRL",
                )
            ]
        return AgentQueryResponse(
            answer_markdown=(
                f"Comparação de **`{metric}`** (**2026–2030**): "
                f"**{comp['bu_a']['label']}** crescimento acumulado "
                f"**{(ga * 100 if ga is not None else 0):.1f}%**, "
                f"**{comp['bu_b']['label']}** **{(gb * 100 if gb is not None else 0):.1f}%**."
            ),
            artifacts=arts,
            confidence="high",
            data_used=[f"dre.{bu_a}.{metric}", f"dre.{bu_b}.{metric}"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.VALUATION_EV_EBITDA:
        ev_ebitda, vm = extract_ev_ebitda_implicit(sim_result)
        wacc = vm.get("wacc")
        g = vm.get("g")
        kpi: list[Any] = []
        if wants_visual:
            kpi = [
                ArtifactKPI(title="Enterprise Value", value=f"{vm.get('enterprise_value', 0):,.2f}"),
                ArtifactKPI(title="Equity Value", value=f"{vm.get('equity_value', 0):,.2f}"),
            ]
        ev_line = f"**EV/EBITDA implícito** (mapeado nos múltiplos do DCF): **{ev_ebitda:.2f}x**.\n\n" if ev_ebitda else ""
        wacc_s = f"{wacc:.2%}" if wacc is not None else "n/d"
        g_s = f"{g:.2%}" if g is not None else "n/d"
        return AgentQueryResponse(
            answer_markdown=(
                f"{ev_line}"
                f"**WACC** (cenário): **{wacc_s}** | **g** perpetuidade: **{g_s}**.\n\n"
                "Use sensibilidade no painel de premissas DCF para stress de múltiplo."
            ),
            artifacts=kpi,
            confidence="high",
            data_used=["dcf.multiplos", "dcf.wacc", "dcf.g"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.TABLE_METRIC_BU_YEARS:
        metric = str(ent.get("metric", "ebitda"))
        pivot = build_pivot_table(sim_result, metric, 2026, 2030)
        table = ArtifactTable(
            title=f"{metric} por BU (2026-2030)",
            columns=pivot["columns"],
            rows=pivot["rows"],
        )
        return AgentQueryResponse(
            answer_markdown=f"Tabela de **`{metric}`** por BU e ano (**2026–2030**), cenário atual.",
            artifacts=[table],
            confidence="high",
            data_used=[f"dre.*.{metric}"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.EV_VS_EQUITY:
        d = explain_equity_vs_enterprise(sim_result)
        ev, eq = d["enterprise_value"], d["equity_value"]
        return AgentQueryResponse(
            answer_markdown=(
                f"**Enterprise Value** ≈ **{ev:,.2f}** e **Equity Value** ≈ **{eq:,.2f}** no DCF atual.\n\n"
                "**Por que diferem?** O EV valoriza a operação (ativos que geram FCFF); o Equity Value é o valor "
                "para o acionista após ajustar caixa e dívida líquida (posição financeira) em relação ao EV."
            ),
            confidence="high",
            data_used=["dcf.enterprise_value", "dcf.equity_value"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    if intent == Intent.BU_REVENUE_SHARE_CHANGE:
        ranked = bu_revenue_share_change_ranking(sim_result, 2026, 2030)
        if not ranked:
            return None
        worst = min(ranked, key=lambda x: x["delta_pp"])
        best = max(ranked, key=lambda x: x["delta_pp"])
        lines = "\n".join(
            [f"- **{r['bu_label']}**: {r['share_start']*100:.1f}% → {r['share_end']*100:.1f}% (Δ **{r['delta_pp']:+.2f} p.p.**)" for r in ranked]
        )
        return AgentQueryResponse(
            answer_markdown=(
                "Participação de cada BU na **receita líquida consolidada** (**2026 vs 2030**):\n\n"
                f"{lines}\n\n"
                f"A BU com **maior perda relativa de share** foi **{worst['bu_label']}** "
                f"(**{worst['delta_pp']:+.2f} p.p.**); a que mais ganhou foi **{best['bu_label']}**."
            ),
            confidence="high",
            data_used=["dre.*.receita_liquida", "consolidado.receita_liquida"],
            response_source="deterministic",
            intent=intent.value,
            scenario_id=scenario_id,
        )

    return None
