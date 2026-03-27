from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .agent_tools import BU_KEYS


@dataclass(frozen=True)
class AnomalyFlag:
    severity: str  # "warning" | "info"
    description: str
    suggested_question: str


def _as_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _get_row_for_year(rows: list[dict[str, Any]], year: int) -> dict[str, Any] | None:
    for r in rows:
        if int(r.get("ano", -1)) == year:
            return r
    return None


def _get_dre_value(sim_json: dict[str, Any], bu: str, year: int, key: str) -> float | None:
    if bu == "consolidado":
        row = _get_row_for_year(sim_json.get("consolidado", []), year)
    else:
        row = _get_row_for_year(sim_json.get("dre", {}).get(bu, []), year)
    if not row:
        return None
    return _as_float(row.get(key))


def _growth(sim_json: dict[str, Any], bu: str, year_start: int, year_end: int, key: str) -> float | None:
    v0 = _get_dre_value(sim_json, bu, year_start, key)
    v1 = _get_dre_value(sim_json, bu, year_end, key)
    if v0 is None or v1 is None or v0 == 0:
        return None
    return v1 / v0 - 1.0


def _iter_anomalies(sim_json: dict[str, Any], historical_bundle: dict[str, Any] | None) -> Iterable[AnomalyFlag]:
    year_start, year_end = 2026, 2030

    # 1) Divergência BU vs consolidado (proxy: crescimento de receita líquida)
    cons_growth = _growth(sim_json, "consolidado", year_start, year_end, "receita_liquida")
    if cons_growth is not None:
        for bu in BU_KEYS:
            g_bu = _growth(sim_json, bu, year_start, year_end, "receita_liquida")
            if g_bu is None:
                continue
            if abs(g_bu - cons_growth) > 0.20:
                yield AnomalyFlag(
                    severity="warning",
                    description=(
                        f"{bu.upper()} cresce ~{g_bu:.0%} entre {year_start}–{year_end}, "
                        f"enquanto o consolidado cresce ~{cons_growth:.0%}. "
                        "Isso sugere contração relativa das demais BUs."
                    ),
                    suggested_question=f"Qual o impacto por BU no consolidado ({year_start}→{year_end})?",
                )

    # 2) Concentração de receita (maior share em 2030)
    cons_end = _get_dre_value(sim_json, "consolidado", year_end, "receita_liquida") or 0.0
    if cons_end > 0:
        shares: list[tuple[str, float]] = []
        for bu in BU_KEYS:
            bu_v = _get_dre_value(sim_json, bu, year_end, "receita_liquida") or 0.0
            shares.append((bu, bu_v / cons_end))
        top_bu, top_share = max(shares, key=lambda x: x[1])
        if top_share >= 0.60:
            yield AnomalyFlag(
                severity="warning",
                description=f"{top_bu.upper()} representa ~{top_share:.0%} da receita líquida consolidada em {year_end}.",
                suggested_question=f"Quais os riscos se {top_bu.upper()} desacelerar em {year_end}?",
            )

    # 3) Margem projetada vs histórico (proxy: EBITDA margin)
    if historical_bundle:
        for bu in BU_KEYS:
            cons_rows = historical_bundle.get("dre", {}).get(bu, [])
            if not cons_rows:
                continue

            projected_margin = None
            ebitda_p = _get_dre_value(sim_json, bu, year_end, "ebitda")
            rl_p = _get_dre_value(sim_json, bu, year_end, "receita_liquida")
            if ebitda_p is not None and rl_p:
                projected_margin = ebitda_p / rl_p

            if projected_margin is None:
                continue

            hist_margins: list[float] = []
            for r in cons_rows:
                # históricos vêm como dicionários com "ano" e chaves mapeadas
                y = int(r.get("ano", -1))
                if y < 2018 or y > 2025:
                    continue
                ebitda_h = _as_float(r.get("ebitda"))
                rl_h = _as_float(r.get("receita_liquida"))
                if ebitda_h is None or rl_h in (None, 0):
                    continue
                hist_margins.append(ebitda_h / rl_h)

            if not hist_margins:
                continue

            hist_avg = sum(hist_margins) / len(hist_margins)
            # Se a margem projetada sai demais da média histórica, sinalizamos.
            if hist_avg > 0 and (projected_margin / hist_avg) >= 1.25:
                yield AnomalyFlag(
                    severity="info",
                    description=(
                        f"Margem EBITDA projetada para {bu.upper()} em {year_end} (~{projected_margin:.0%}) "
                        f"está acima da média histórica (~{hist_avg:.0%})."
                    ),
                    suggested_question=f"Comparar histórico vs projeção de margem para {bu.upper()} ({year_end}).",
                )
            elif hist_avg > 0 and (projected_margin / hist_avg) <= 0.80:
                yield AnomalyFlag(
                    severity="warning",
                    description=(
                        f"Margem EBITDA projetada para {bu.upper()} em {year_end} (~{projected_margin:.0%}) "
                        f"está abaixo da média histórica (~{hist_avg:.0%})."
                    ),
                    suggested_question=f"Quais drivers explicam a queda de margem de {bu.upper()}?",
                )


def detect_anomalies(sim_json: dict[str, Any], historical_bundle: dict[str, Any] | None) -> list[AnomalyFlag]:
    flags = list(_iter_anomalies(sim_json, historical_bundle))
    # Limita para não poluir a resposta
    flags = sorted(flags, key=lambda f: 0 if f.severity == "warning" else 1)[:3]
    return flags


def format_anomalies_for_response(flags: list[AnomalyFlag]) -> str:
    if not flags:
        return ""

    blocks: list[str] = []
    for flag in flags:
        icon = "⚠" if flag.severity == "warning" else "ℹ"
        blocks.append(f"{icon} {flag.description}\n  → *{flag.suggested_question}*")

    return "\n\n---\n\n" + "\n\n".join(blocks)

