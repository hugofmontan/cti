from __future__ import annotations

from typing import Any

BU_KEYS = ["fopm", "renovacao", "ams", "venda_sw", "data_science"]
BU_LABELS = {
    "fopm": "FOPM",
    "renovacao": "Renovacao",
    "ams": "AMS",
    "venda_sw": "Venda SW",
    "data_science": "Data Science",
}


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_metric_by_bu_year(sim_result: dict[str, Any], metric: str, year: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for bu in BU_KEYS:
        rows = sim_result.get("dre", {}).get(bu, [])
        row = next((r for r in rows if int(r.get("ano", -1)) == year), None)
        if not row:
            continue
        value = _as_float(row.get(metric))
        if value is None:
            continue
        output.append({"bu": bu, "bu_label": BU_LABELS[bu], "year": year, "metric": metric, "value": value})
    return output


def get_timeseries(
    sim_result: dict[str, Any],
    bu: str,
    metric: str,
    start_year: int,
    end_year: int,
) -> list[dict[str, Any]]:
    if bu == "consolidado":
        rows = sim_result.get("consolidado", [])
    else:
        rows = sim_result.get("dre", {}).get(bu, [])
    out: list[dict[str, Any]] = []
    for row in rows:
        year = int(row.get("ano", -1))
        if start_year <= year <= end_year:
            value = _as_float(row.get(metric))
            if value is not None:
                out.append({"year": year, "value": value})
    return sorted(out, key=lambda item: item["year"])


def get_row_for_year(sim_result: dict[str, Any], bu: str, year: int) -> dict[str, Any] | None:
    rows = sim_result.get("consolidado", []) if bu == "consolidado" else sim_result.get("dre", {}).get(bu, [])
    return next((r for r in rows if int(r.get("ano", -1)) == year), None)


def get_margin_by_bu_year(sim_result: dict[str, Any], year: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for bu in BU_KEYS:
        row = get_row_for_year(sim_result, bu, year)
        if not row:
            continue
        margin = _as_float(row.get("ebitda_pct_rl"))
        if margin is None:
            ebitda = _as_float(row.get("ebitda"))
            rl = _as_float(row.get("receita_liquida"))
            if ebitda is not None and rl not in (None, 0):
                margin = ebitda / rl
        if margin is None:
            continue
        out.append({"bu": bu, "bu_label": BU_LABELS[bu], "year": year, "margin": margin})
    return sorted(out, key=lambda item: item["margin"], reverse=True)


def get_margin_impact_consolidated(sim_result: dict[str, Any], start_year: int, end_year: int) -> list[dict[str, Any]]:
    cons_end = get_row_for_year(sim_result, "consolidado", end_year)
    if not cons_end:
        return []
    cons_rl_end = _as_float(cons_end.get("receita_liquida")) or 0.0
    if cons_rl_end == 0:
        return []

    impacts: list[dict[str, Any]] = []
    for bu in BU_KEYS:
        row_start = get_row_for_year(sim_result, bu, start_year)
        row_end = get_row_for_year(sim_result, bu, end_year)
        if not row_start or not row_end:
            continue
        ebitda_start = _as_float(row_start.get("ebitda")) or 0.0
        ebitda_end = _as_float(row_end.get("ebitda")) or 0.0
        delta_ebitda = ebitda_end - ebitda_start
        impact_pp = (delta_ebitda / cons_rl_end) * 100
        impacts.append(
            {
                "bu": bu,
                "bu_label": BU_LABELS[bu],
                "delta_ebitda": delta_ebitda,
                "impact_pp": impact_pp,
            }
        )
    return sorted(impacts, key=lambda item: item["impact_pp"], reverse=True)


def compare_bus_growth(
    sim_result: dict[str, Any],
    metric: str,
    bu_a: str,
    bu_b: str,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    ts_a = get_timeseries(sim_result, bu_a, metric, start_year, end_year)
    ts_b = get_timeseries(sim_result, bu_b, metric, start_year, end_year)

    def _growth(ts: list[dict[str, Any]]) -> float | None:
        if len(ts) < 2:
            return None
        first = ts[0]["value"]
        last = ts[-1]["value"]
        if first == 0:
            return None
        return (last / first) - 1.0

    return {
        "metric": metric,
        "period": f"{start_year}-{end_year}",
        "bu_a": {"key": bu_a, "label": BU_LABELS.get(bu_a, bu_a), "growth": _growth(ts_a), "series": ts_a},
        "bu_b": {"key": bu_b, "label": BU_LABELS.get(bu_b, bu_b), "growth": _growth(ts_b), "series": ts_b},
    }


def get_valuation_metrics(sim_result: dict[str, Any]) -> dict[str, float]:
    dcf = sim_result.get("dcf", {})
    out: dict[str, float] = {}
    for key in ["wacc", "g", "enterprise_value", "equity_value", "soma_vp_fcffs"]:
        value = _as_float(dcf.get(key))
        if value is not None:
            out[key] = value
    multiplos = dcf.get("multiplos", {})
    for key, value in multiplos.items():
        fv = _as_float(value)
        if fv is not None:
            out[f"multiplos.{key}"] = fv
    return out


def margin_impact_year_by_year(
    sim_result: dict[str, Any],
    start_year: int,
    end_year: int,
) -> list[dict[str, Any]]:
    """Para cada ano Y em (start_year+1..end_year), delta EBITDA BU / RL consolidado em Y."""
    rows_out: list[dict[str, Any]] = []
    for year in range(start_year + 1, end_year + 1):
        cons = get_row_for_year(sim_result, "consolidado", year)
        if not cons:
            continue
        cons_rl = _as_float(cons.get("receita_liquida")) or 0.0
        if cons_rl == 0:
            continue
        prev_y = year - 1
        for bu in BU_KEYS:
            r0 = get_row_for_year(sim_result, bu, prev_y)
            r1 = get_row_for_year(sim_result, bu, year)
            if not r0 or not r1:
                continue
            e0 = _as_float(r0.get("ebitda")) or 0.0
            e1 = _as_float(r1.get("ebitda")) or 0.0
            d_ebitda = e1 - e0
            impact_pp = (d_ebitda / cons_rl) * 100
            rows_out.append(
                {
                    "year": year,
                    "bu": bu,
                    "bu_label": BU_LABELS[bu],
                    "delta_ebitda": d_ebitda,
                    "impact_pp": impact_pp,
                }
            )
    return rows_out


def bu_revenue_share_change_ranking(
    sim_result: dict[str, Any],
    year_start: int,
    year_end: int,
) -> list[dict[str, Any]]:
    """Variação de participação na receita líquida consolidada (BU RL / RL consolidado)."""
    cons_s = get_row_for_year(sim_result, "consolidado", year_start)
    cons_e = get_row_for_year(sim_result, "consolidado", year_end)
    if not cons_s or not cons_e:
        return []
    rl_cons_s = _as_float(cons_s.get("receita_liquida")) or 0.0
    rl_cons_e = _as_float(cons_e.get("receita_liquida")) or 0.0
    if rl_cons_s == 0 or rl_cons_e == 0:
        return []

    out: list[dict[str, Any]] = []
    for bu in BU_KEYS:
        rs = get_row_for_year(sim_result, bu, year_start)
        re_ = get_row_for_year(sim_result, bu, year_end)
        if not rs or not re_:
            continue
        rl_bu_s = _as_float(rs.get("receita_liquida")) or 0.0
        rl_bu_e = _as_float(re_.get("receita_liquida")) or 0.0
        share_s = rl_bu_s / rl_cons_s
        share_e = rl_bu_e / rl_cons_e
        out.append(
            {
                "bu": bu,
                "bu_label": BU_LABELS[bu],
                "share_start": share_s,
                "share_end": share_e,
                "delta_pp": (share_e - share_s) * 100,
            }
        )
    return sorted(out, key=lambda x: x["delta_pp"])


def extract_ev_ebitda_implicit(sim_result: dict[str, Any]) -> tuple[float | None, dict[str, float]]:
    vm = get_valuation_metrics(sim_result)
    ev_ebitda = next((v for k, v in vm.items() if "EV_EBITDA" in k), None)
    return ev_ebitda, vm


def explain_equity_vs_enterprise(sim_result: dict[str, Any]) -> dict[str, float]:
    vm = get_valuation_metrics(sim_result)
    ev = vm.get("enterprise_value")
    eq = vm.get("equity_value")
    return {
        "enterprise_value": float(ev) if ev is not None else 0.0,
        "equity_value": float(eq) if eq is not None else 0.0,
    }


def get_historical_metric_for_bu(
    historical_bundle: dict[str, Any],
    bu_key: str,
    year: int,
    metric: str,
) -> float | None:
    dre = historical_bundle.get("dre", {}).get(bu_key, [])
    row = next((r for r in dre if int(r.get("ano", -1)) == year), None)
    if not row:
        return None
    return _as_float(row.get(metric))


def build_pivot_table(
    sim_result: dict[str, Any],
    metric: str,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    columns = ["BU"] + [str(year) for year in range(start_year, end_year + 1)]
    rows: list[list[str | float | None]] = []
    for bu in BU_KEYS:
        series = {item["year"]: item["value"] for item in get_timeseries(sim_result, bu, metric, start_year, end_year)}
        row: list[str | float | None] = [BU_LABELS[bu]]
        for year in range(start_year, end_year + 1):
            row.append(series.get(year))
        rows.append(row)
    return {"columns": columns, "rows": rows}
