"""
Agent v2 — Tools (Function Calling).

Define as 6 tools disponíveis para o LLM via OpenAI function calling:
  1. run_simulation    — roda cenário alternativo
  2. compare_scenarios — compara cenários
  3. get_sensitivity_matrix — sensibilidade WACC×g (ou outros)
  4. query_data        — consulta dados da simulação/histórico
  5. build_artifact    — constrói artefato visual
  6. get_sankey_data   — gera nodes/links para Sankey da DRE

Inclui o dispatcher (execute_tool) e todas as funções auxiliares.
"""

from __future__ import annotations

import copy
import re
import unicodedata
import math
from typing import Any

from projecao_bus.orchestrator import resultado_para_json, run_simulation

from .agent_context_builder import (
    BU_KEYS,
    BU_LABELS,
    compute_scenario_id,
    _get_row_for_year,
    _safe_float,
)
from .projection_config import get_projection_years

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function calling format)
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_simulation",
            "description": (
                "Roda uma nova simulação financeira com premissas alteradas. "
                "Use quando o usuário pedir cenários alternativos: 'e se...', "
                "'roda com...', 'simula com...', 'testa com churn de X%'. "
                "Retorna DRE consolidada e por BU, DCF e FCFF do cenário alternativo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "premissa_changes": {
                        "type": "object",
                        "description": (
                            "Premissas a alterar. Use dot-notation. "
                            "Chaves válidas: "
                            "fopm.headcount_por_ano (dict ano->valor), "
                            "fopm.ociosidade_por_ano (dict ano->valor), "
                            "renovacao.churn (float 0-1), "
                            "renovacao.spread_real (float), "
                            "ams.taxa_conversao_fopm (float 0-1), "
                            "ams.churn (float 0-1), "
                            "venda_softwares.fator_crescimento_real (float; alias: venda_sw.fator_crescimento_real), "
                            "data_science.headcount_por_ano (dict ano->valor), "
                            "data_science.ociosidade_por_ano (dict ano->valor), "
                            "dcf.wacc (float 0-1, ex: 0.12 = 12%), "
                            "dcf.g (float 0-1, ex: 0.03 = 3%). "
                            "Só inclua as premissas que devem mudar."
                        ),
                        "additionalProperties": True,
                    },
                    "label": {
                        "type": "string",
                        "description": "Rótulo curto para este cenário (ex: 'churn_20pct', 'pessimista')",
                    },
                },
                "required": ["premissa_changes", "label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_scenarios",
            "description": (
                "Compara dois cenários lado a lado. "
                "Use após rodar uma simulação alternativa, ou quando o "
                "usuário pedir comparação explícita entre cenários. "
                "Retorna deltas absolutos e percentuais por métrica."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "base_scenario_id": {
                        "type": "string",
                        "description": "ID do cenário base (usar o scenario_id do contexto atual)",
                    },
                    "alt_scenario_id": {
                        "type": "string",
                        "description": "ID do cenário alternativo (retornado por run_simulation)",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Métricas a comparar. Opções: "
                            "receita_liquida, ebitda, margem_ebitda, lucro_liquido, "
                            "enterprise_value, equity_value, fcff, "
                            "faturamento_bruto, custos_totais"
                        ),
                    },
                    "granularity": {
                        "type": "string",
                        "enum": ["consolidado", "por_bu", "ambos"],
                        "description": "Nível de detalhe da comparação",
                    },
                },
                "required": ["base_scenario_id", "alt_scenario_id", "metrics"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensitivity_matrix",
            "description": (
                "Gera uma matriz de sensibilidade cruzando dois parâmetros. "
                "Use para análise WACC×g, ou qualquer cruzamento de premissas "
                "que o usuário pedir. Retorna uma matriz numérica pronta para heatmap."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "row_param": {
                        "type": "string",
                        "description": "Parâmetro para as linhas. Use dot-notation (ex: 'dcf.wacc', 'dcf.g', 'renovacao.churn')",
                    },
                    "col_param": {
                        "type": "string",
                        "description": "Parâmetro para as colunas. Use dot-notation (ex: 'dcf.g', 'dcf.wacc', 'renovacao.churn')",
                    },
                    "row_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "steps": {"type": "integer"},
                        },
                        "required": ["min", "max", "steps"],
                        "description": "Range do parâmetro de linhas (ex: wacc de 0.08 a 0.16, 5 steps)",
                    },
                    "col_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "steps": {"type": "integer"},
                        },
                        "required": ["min", "max", "steps"],
                        "description": "Range do parâmetro de colunas (ex: g de 0.01 a 0.05, 5 steps)",
                    },
                    "target_metric": {
                        "type": "string",
                        "enum": ["enterprise_value", "equity_value", "ev_ebitda"],
                        "description": "Métrica-alvo da sensibilidade",
                    },
                },
                "required": ["row_param", "col_param", "row_range", "col_range", "target_metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": (
                "Consulta dados específicos da simulação atual ou do histórico. "
                "Use para qualquer pergunta que precise de dados numéricos: "
                "métricas pontuais, evolução temporal, decomposição por BU, "
                "ou comparação com dados históricos. "
                "SEMPRE use esta tool antes de build_artifact quando precisar de dados."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["current", "historical", "both"],
                        "description": "'current' = simulação atual, 'historical' = dados históricos, 'both' = comparação",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Métricas a consultar. Opções: "
                            "faturamento_bruto, receita_liquida, custos_totais, "
                            "ebitda, ebitda_pct_rl, lucro_liquido, "
                            "headcount (canônica; n_funcionarios é alias), "
                            "fcff, nopat, capex, da_total, delta_ncg, "
                            "enterprise_value, equity_value, ev_ebitda_implicito, "
                            "gastos_pessoal, outras_desp_diretas, outras_desp_adm. "
                            "Também aceita derivadas com sufixo: "
                            "<metrica>_delta_pct, <metrica>_cagr, <metrica>_yoy_pct "
                            "(ex: receita_liquida_cagr)."
                        ),
                    },
                    "bus": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "BUs a consultar. Opções: "
                            "'consolidado', 'fopm', 'renovacao', 'ams', 'venda_sw', 'data_science'. "
                            "Use ['consolidado'] para dados totais, ou lista de BUs para decomposição."
                        ),
                    },
                    "years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Anos a consultar (2012-2030). Se omitido, retorna todo o horizonte de projeção (2026-2030).",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["timeseries", "snapshot", "decomposition"],
                        "description": (
                            "'timeseries' = dados ao longo do tempo (para line/bar charts), "
                            "'snapshot' = dados pontuais de um ano (para KPI/waterfall), "
                            "'decomposition' = dados decompostos por BU (para stacked/waterfall)"
                        ),
                    },
                },
                "required": ["source", "metrics", "bus"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_artifact",
            "description": (
                "Constrói um artefato visual (gráfico, tabela, KPI) a partir de dados. "
                "REGRAS IMPORTANTES: "
                "1) SEMPRE use esta tool quando a resposta envolver dados numéricos. "
                "2) SEMPRE chame query_data ou outra tool de dados ANTES desta. "
                "3) Se o usuário especificou tipo de gráfico, use exatamente o tipo pedido. "
                "4) Se não especificou, escolha o tipo mais adequado aos dados. "
                "5) NUNCA construa JSON de artifact no texto — sempre use esta tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artifact_type": {
                        "type": "string",
                        "enum": ["line", "bar", "stacked_bar", "grouped_bar", "waterfall", "heatmap", "table", "kpi_panel", "sankey"],
                        "description": "Tipo de visualização",
                    },
                    "title": {
                        "type": "string",
                        "description": "Título descritivo do artifact (ex: 'Evolução EBITDA por BU (2026-2030)')",
                    },
                    "data": {
                        "type": "object",
                        "description": (
                            "Dados para o artifact. Estrutura depende do tipo: "
                            "Para charts (line/bar/stacked_bar/grouped_bar): "
                            "  { x: ['2026','2027',...], series: [{name: 'FOPM', values: [1,2,3]}], unit: 'BRL' } "
                            "Para waterfall: "
                            "  { categories: ['Receita','(-) Custos',...], values: [100,-30,...], unit: 'BRL' } "
                            "Para heatmap: "
                            "  { row_param: 'wacc', col_param: 'g', row_values: [...], col_values: [...], matrix: [[...]] } "
                            "Para table: "
                            "  { columns: ['BU','2026','2027',...], rows: [['FOPM','100','200',...]] } "
                            "Para kpi_panel: "
                            "  { items: [{label: 'EV', value: '150M', delta: '+12%', sentiment: 'positive'}] }"
                        ),
                        "additionalProperties": True,
                    },
                    "config": {
                        "type": "object",
                        "description": "Configurações opcionais: x_label, y_label, unit (BRL/% /#), highlight, reference_line",
                        "additionalProperties": True,
                    },
                },
                "required": ["artifact_type", "title", "data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sankey_data",
            "description": (
                "Gera dados de Sankey (nodes + links) a partir da DRE de uma BU ou do consolidado. "
                "Use quando o usuário pedir sankey, breakdown, fluxo da DRE, "
                "breakdown da DRE, decomposição visual de receita a lucro, "
                "ou diagrama de fluxo financeiro. "
                "Retorna nodes e links prontos para build_artifact(type='sankey'). "
                "SEMPRE chame esta tool antes de build_artifact(type='sankey')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bu": {
                        "type": "string",
                        "enum": ["consolidado", "fopm", "renovacao", "ams", "venda_sw", "data_science"],
                        "description": "BU ou consolidado para gerar o Sankey",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Ano para o Sankey (2026-2030). Se omitido, usa último ano projetado.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["dre_flow", "bu_composition"],
                        "description": (
                            "'dre_flow' = fluxo da DRE (receita -> lucro) de uma BU ou consolidado. "
                            "'bu_composition' = como cada BU contribui para o consolidado. "
                            "Default: 'dre_flow'."
                        ),
                    },
                },
                "required": ["bu"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


def execute_tool(tool_name: str, arguments: dict, context: dict) -> dict:
    """Dispatcher central de tools. Chamado pelo openai_client quando
    o LLM faz um tool call."""

    if tool_name == "run_simulation":
        return _tool_run_simulation(arguments, context)
    elif tool_name == "compare_scenarios":
        return _tool_compare_scenarios(arguments, context)
    elif tool_name == "get_sensitivity_matrix":
        return _tool_get_sensitivity_matrix(arguments, context)
    elif tool_name == "query_data":
        return _tool_query_data(arguments, context)
    elif tool_name == "build_artifact":
        return _tool_build_artifact(arguments, context)
    elif tool_name == "get_sankey_data":
        return _tool_get_sankey_data(arguments, context)
    else:
        return {"error": f"Tool desconhecida: {tool_name}"}


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _tool_run_simulation(args: dict, ctx: dict) -> dict:
    """Roda simulação com premissas alteradas."""
    premissa_changes_raw = args.get("premissa_changes")
    if not isinstance(premissa_changes_raw, dict) or not premissa_changes_raw:
        known_meta = {"premissa_changes", "label", "scenario_id", "base_scenario_id", "alt_scenario_id"}
        premissa_changes_raw = {k: v for k, v in args.items() if k not in known_meta}
    premissa_changes = _normalize_premissa_changes(premissa_changes_raw)
    if not premissa_changes:
        inferred = _infer_premissa_changes_from_question(ctx.get("question", ""), ctx.get("premissas", {}))
        if inferred:
            premissa_changes = inferred
    if not premissa_changes:
        return {
            "error": (
                "Nenhuma premissa válida foi informada para run_simulation. "
                "Envie premissa_changes com chaves como dcf.wacc, dcf.g, renovacao.churn."
            )
        }
    premissas_novas = deep_merge(ctx["premissas"], premissa_changes)

    sim = run_simulation(premissas=premissas_novas)
    sim_json = resultado_para_json(sim)
    scenario_id = compute_scenario_id(sim_json)

    cache = ctx.setdefault("_scenario_cache", {})
    cache[scenario_id] = {
        "sim_json": sim_json,
        "label": args.get("label", "alternativo"),
        "premissa_changes": premissa_changes,
    }

    return {
        "scenario_id": scenario_id,
        "label": args.get("label", "alternativo"),
        "premissa_changes": premissa_changes,
        "resumo_consolidado": _extract_resumo_consolidado(sim_json),
        "dcf": _extract_dcf_summary(sim_json),
    }


def _tool_compare_scenarios(args: dict, ctx: dict) -> dict:
    """Compara dois cenários por métricas selecionadas."""
    base_id = args.get("base_scenario_id", ctx.get("scenario_id", ""))
    alt_id = args.get("alt_scenario_id", "")
    metrics = args.get("metrics", ["ebitda", "enterprise_value"])
    granularity = args.get("granularity", "ambos")

    cache = ctx.get("_scenario_cache", {})

    if base_id == ctx.get("scenario_id"):
        base_data = ctx.get("sim_json")
    else:
        base_data = cache.get(base_id, {}).get("sim_json")

    alt_entry = cache.get(alt_id, {})
    alt_data = alt_entry.get("sim_json")

    if not base_data or not alt_data:
        return {"error": "Cenário não encontrado. Rode run_simulation primeiro."}

    result = _compute_comparison(
        base_data, alt_data, metrics, granularity,
        base_label="base",
        alt_label=alt_entry.get("label", "alternativo"),
    )
    ctx["_last_comparison_result"] = result
    return result


def _tool_get_sensitivity_matrix(args: dict, ctx: dict) -> dict:
    """Gera matriz de sensibilidade rodando múltiplas simulações."""
    row_param = args.get("row_param", "dcf.wacc")
    col_param = args.get("col_param", "dcf.g")
    row_range = args.get("row_range", {"min": 0.08, "max": 0.16, "steps": 5})
    col_range = args.get("col_range", {"min": 0.01, "max": 0.05, "steps": 5})
    target_metric = args.get("target_metric", "enterprise_value")
    base_year = str(get_projection_years()[0]) if get_projection_years() else "2026"

    # Se a matriz já veio pré-calculada no sim_json (caso WACC×g) usa direto
    if (
        _normalize_param(row_param) in ("dcf.wacc", "wacc")
        and _normalize_param(col_param) in ("dcf.g", "g")
        and target_metric == "enterprise_value"
    ):
        existing = ctx.get("sim_json", {}).get("dcf", {}).get("sensitivity_matrix")
        if isinstance(existing, dict) and existing.get("matrix"):
            result = {
                "row_param": existing.get("row_param", row_param),
                "col_param": existing.get("col_param", col_param),
                "row_values": existing["row_values"],
                "col_values": existing["col_values"],
                "matrix": existing["matrix"],
                "target_metric": target_metric,
                "source": "pre_calculated",
            }
            ctx["_last_sensitivity_result"] = result
            return result

    norm_row_param = _normalize_param(row_param)
    norm_col_param = _normalize_param(col_param)

    def _axis_base_value(param_key: str) -> float | None:
        """Base do eixo (caso base efetivo) para enriquecer a UI."""
        norm = _normalize_param(param_key)
        prem = ctx.get("premissas")
        if not isinstance(prem, dict):
            return None

        if norm.endswith("headcount_por_ano"):
            bu_key = norm.split(".", 1)[0] if "." in norm else norm
            hc = prem.get(bu_key, {}).get("headcount_por_ano")
            if isinstance(hc, dict):
                v = hc.get(base_year)
                if v is None:
                    v = hc.get(int(base_year))  # type: ignore[arg-type]
                return _safe_float(v)

        if norm.endswith("ociosidade_por_ano"):
            bu_key = norm.split(".", 1)[0] if "." in norm else norm
            oc = prem.get(bu_key, {}).get("ociosidade_por_ano")
            if isinstance(oc, dict):
                v = oc.get(base_year)
                if v is None:
                    v = oc.get(int(base_year))  # type: ignore[arg-type]
                return _safe_float(v)

        # Parâmetros escalares em dot-notation (ex.: dcf.wacc, dcf.g, renovacao.churn).
        target: Any = prem
        for part in norm.split("."):
            if not isinstance(target, dict):
                return None
            target = target.get(part)
        return _safe_float(target)

    def _build_centered_axis_values(param_key: str, axis_range: dict[str, Any]) -> list[float]:
        """
        Constrói eixo de sensibilidade com o cenário atual no centro da grade.
        Se `steps` vier par, promove para ímpar para existir célula central.
        """
        min_v = _safe_float(axis_range.get("min"))
        max_v = _safe_float(axis_range.get("max"))
        try:
            steps = int(axis_range.get("steps", 5))
        except Exception:
            steps = 5
        if steps < 1:
            steps = 1

        base_val = _axis_base_value(param_key)

        # Sem base conhecida, mantém comportamento original (linspace puro).
        if base_val is None:
            lo = float(min_v) if min_v is not None else 0.0
            hi = float(max_v) if max_v is not None else lo
            return _linspace(lo, hi, steps)

        # Com 1 passo, preserva valor solicitado no range (comportamento histórico).
        # Se não vier min/max, usa o cenário atual.
        if steps == 1:
            if min_v is not None:
                return [round(float(min_v), 6)]
            if max_v is not None:
                return [round(float(max_v), 6)]
            return [round(float(base_val), 6)]

        # Para garantir centro exato na grade, precisamos de steps ímpar.
        if steps % 2 == 0:
            steps += 1

        lo = float(min_v) if min_v is not None else float(base_val)
        hi = float(max_v) if max_v is not None else float(base_val)
        radius = max(abs(float(base_val) - lo), abs(hi - float(base_val)))
        if radius == 0:
            radius = abs(float(base_val)) * 0.2 if float(base_val) != 0 else 0.01

        values = _linspace(float(base_val) - radius, float(base_val) + radius, steps)
        values[steps // 2] = round(float(base_val), 6)
        return values

    row_axis_meta = {"base_year": base_year, "base_value": _axis_base_value(row_param)}
    col_axis_meta = {"base_year": base_year, "base_value": _axis_base_value(col_param)}

    row_values_raw = _build_centered_axis_values(row_param, row_range)
    col_values_raw = _build_centered_axis_values(col_param, col_range)

    def _header_value(param_key: str, scalar_value: float) -> float:
        broadcast = _broadcast_sensitivity_value(param_key, scalar_value, premissas=ctx.get("premissas"))
        if isinstance(broadcast, dict):
            base_year = str(get_projection_years()[0]) if get_projection_years() else "2026"
            v = broadcast.get(base_year)
            if isinstance(v, (int, float)) and math.isfinite(float(v)):
                return float(v)
            # fallback: primeiro valor
            for _, v2 in broadcast.items():
                if isinstance(v2, (int, float)) and math.isfinite(float(v2)):
                    return float(v2)
        if isinstance(broadcast, (int, float)):
            return float(broadcast)
        return float(scalar_value)

    row_values = (
        [_header_value(row_param, rv) for rv in row_values_raw]
        if norm_row_param.endswith("headcount_por_ano")
        else row_values_raw
    )
    col_values = (
        [_header_value(col_param, cv) for cv in col_values_raw]
        if norm_col_param.endswith("headcount_por_ano")
        else col_values_raw
    )

    def _get_series_from_premissas(prem: dict[str, Any] | None, bu_key: str, series_key: str) -> dict[str, Any] | None:
        if not isinstance(prem, dict):
            return None
        bu = prem.get(bu_key)
        if not isinstance(bu, dict):
            return None
        v = bu.get(series_key)
        if not isinstance(v, dict):
            return None
        # Garante chaves strings (anos geralmente já são strings no premissas_efetivas).
        return {str(k): v[k] for k in v.keys()}

    # Monta breakdown por cenário (útil para a LLM descrever em texto).
    # Mantemos baixo acoplamento: apenas quando os eixos envolvem Data Science
    # e o usuário vai pedir "detalhadamente ... em cada cenário".
    base_prem = ctx.get("premissas")
    _row_is_ds_hc = norm_row_param.endswith("data_science.headcount_por_ano") or norm_row_param.endswith("data_science.n_funcionarios")
    _row_is_ds_oc = norm_row_param.endswith("data_science.ociosidade_por_ano")
    _col_is_ds_hc = norm_col_param.endswith("data_science.headcount_por_ano") or norm_col_param.endswith("data_science.n_funcionarios")
    _col_is_ds_oc = norm_col_param.endswith("data_science.ociosidade_por_ano")
    want_breakdown = (_row_is_ds_hc or _row_is_ds_oc or _col_is_ds_hc or _col_is_ds_oc)

    scenario_breakdown: list[dict[str, Any]] | None = None
    if want_breakdown:
        ds_base_hc = _get_series_from_premissas(base_prem, "data_science", "headcount_por_ano") or {}
        ds_base_oc = _get_series_from_premissas(base_prem, "data_science", "ociosidade_por_ano") or {}
        fopm_base_hc = _get_series_from_premissas(base_prem, "fopm", "headcount_por_ano") or {}
        fopm_base_oc = _get_series_from_premissas(base_prem, "fopm", "ociosidade_por_ano") or {}

        # pré-calcula séries efetivas para os ticks, evitando recomputar no loop duplo
        row_effective = [  # one per rv tick
            _broadcast_sensitivity_value(row_param, rv, premissas=ctx.get("premissas")) for rv in row_values_raw
        ]
        col_effective = [  # one per cv tick
            _broadcast_sensitivity_value(col_param, cv, premissas=ctx.get("premissas")) for cv in col_values_raw
        ]

        scenario_breakdown = []
        for i, rv in enumerate(row_values_raw):
            for j, cv in enumerate(col_values_raw):
                ds_hc = dict(ds_base_hc)
                ds_oc = dict(ds_base_oc)

                # aplica override do eixo de linha
                r_eff = row_effective[i]
                if _row_is_ds_hc and isinstance(r_eff, dict):
                    ds_hc = r_eff
                if _row_is_ds_oc and isinstance(r_eff, dict):
                    ds_oc = r_eff

                # aplica override do eixo de coluna
                c_eff = col_effective[j]
                if _col_is_ds_hc and isinstance(c_eff, dict):
                    ds_hc = c_eff
                if _col_is_ds_oc and isinstance(c_eff, dict):
                    ds_oc = c_eff

                scenario_breakdown.append(
                    {
                        "row_param": row_param,
                        "col_param": col_param,
                        "row_tick": float(rv),
                        "col_tick": float(cv),
                        "data_science": {
                            "headcount_por_ano": ds_hc,
                            "ociosidade_por_ano": ds_oc,
                        },
                        "fopm": {
                            "headcount_por_ano": fopm_base_hc,
                            "ociosidade_por_ano": fopm_base_oc,
                        },
                    }
                )

    matrix: list[list[float | None]] = []
    for rv in row_values_raw:
        row: list[float | None] = []
        for cv in col_values_raw:
            changes = {
                _normalize_param(row_param): _broadcast_sensitivity_value(
                    row_param,
                    rv,
                    premissas=ctx.get("premissas"),
                ),
                _normalize_param(col_param): _broadcast_sensitivity_value(
                    col_param,
                    cv,
                    premissas=ctx.get("premissas"),
                ),
            }
            premissas_temp = deep_merge(ctx["premissas"], changes)
            try:
                sim = run_simulation(premissas=premissas_temp)
                sim_json = resultado_para_json(sim)
                value = _extract_metric(sim_json, target_metric)
                row.append(value)
            except Exception:
                row.append(None)
        matrix.append(row)

    result = {
        "row_param": row_param,
        "col_param": col_param,
        "row_values": row_values,
        "col_values": col_values,
        "matrix": matrix,
        "target_metric": target_metric,
        "row_axis_meta": row_axis_meta,
        "col_axis_meta": col_axis_meta,
        "scenario_breakdown": scenario_breakdown,
    }
    ctx["_last_sensitivity_result"] = result
    return result


def _tool_query_data(args: dict, ctx: dict) -> dict:
    """Consulta dados da simulação atual ou histórico."""
    source = args.get("source", "current")
    metrics = _normalize_metric_list(args.get("metrics", []))
    bus = args.get("bus", ["consolidado"])
    years = args.get("years")
    fmt = args.get("format", "timeseries")
    if fmt == "timeseries":
        # Regra de produto: toda consulta temporal usada para gráfico deve
        # retornar série completa (histórico + projeção), independentemente
        # do source pedido pelo LLM.
        source = "both"

    result: dict[str, Any] = {}

    hist_bundle = ctx.get("historical_bundle", {}) or {}
    hist_start = int(hist_bundle.get("historical_year_start", 2018)) if isinstance(hist_bundle, dict) else 2018
    hist_end = int(hist_bundle.get("historical_year_end", 2025)) if isinstance(hist_bundle, dict) else 2025
    proj_years = list(get_projection_years())
    hist_years, proj_years_filtered = _partition_requested_years(years, hist_start, hist_end, proj_years)

    if source in ("current", "both"):
        result["current"] = _extract_data_from_sim(
            ctx["sim_json"], metrics, bus, proj_years_filtered if years is not None else years, fmt
        )

    if source in ("historical", "both"):
        result["historical"] = _extract_data_from_historical(
            hist_bundle, metrics, bus, hist_years if years is not None else years, fmt
        )

    # Para séries temporais, expõe também uma visão contínua (histórico + projeção).
    # Isso evita que o agente retorne apenas metade da série quando o usuário
    # pede "evolução" sem restringir explicitamente o período.
    if fmt == "timeseries":
        if source == "both":
            combined = _merge_timeseries_payloads(
                result.get("historical"),
                result.get("current"),
            )
            if combined:
                # Para métricas derivadas (%), recalcula sobre a série completa
                # (histórico + projeção), evitando quebra artificial em 2026.
                combined = _rebuild_combined_for_derived_metrics(
                    combined=combined,
                    metrics=metrics,
                    bus=bus,
                    sim_json=ctx["sim_json"],
                    historical_bundle=hist_bundle,
                    hist_years=hist_years if years is not None else years,
                    proj_years=proj_years_filtered if years is not None else years,
                ) or combined
                result["combined"] = combined
                # Compatibilidade: muitos fluxos do LLM consomem apenas "current".
                # Em timeseries, "current" passa a representar a série contínua.
                result["current"] = combined
                result["x"] = combined.get("x", [])
                result["series"] = combined.get("series", [])
                if combined.get("unit"):
                    result["unit"] = combined.get("unit")
        elif source in ("current", "historical"):
            # Mesmo quando o LLM pedir uma fonte só, devolve também a série
            # consolidada para facilitar respostas com horizonte completo.
            current_payload = (
                result.get("current")
                if source == "current"
                else _extract_data_from_sim(ctx["sim_json"], metrics, bus, None, fmt)
            )
            historical_payload = (
                result.get("historical")
                if source == "historical"
                else _extract_data_from_historical(hist_bundle, metrics, bus, None, fmt)
            )
            combined = _merge_timeseries_payloads(historical_payload, current_payload)
            if combined:
                combined = _rebuild_combined_for_derived_metrics(
                    combined=combined,
                    metrics=metrics,
                    bus=bus,
                    sim_json=ctx["sim_json"],
                    historical_bundle=hist_bundle,
                    hist_years=None,
                    proj_years=None,
                ) or combined
                result["combined"] = combined
                result["current"] = combined
                result["x"] = combined.get("x", [])
                result["series"] = combined.get("series", [])
                if combined.get("unit"):
                    result["unit"] = combined.get("unit")

    ctx["_last_query_result"] = result
    return result


def _partition_requested_years(
    years: list[int] | None,
    hist_start: int,
    hist_end: int,
    projection_years: list[int],
) -> tuple[list[int] | None, list[int] | None]:
    """Separa anos solicitados entre histórico e projeção."""
    if years is None:
        return None, None

    projection_set = set(int(y) for y in projection_years)
    historical: list[int] = []
    projected: list[int] = []
    for y in years:
        iy = int(y)
        if hist_start <= iy <= hist_end:
            historical.append(iy)
        if iy in projection_set:
            projected.append(iy)

    return historical, projected


def _tool_get_sankey_data(args: dict, ctx: dict) -> dict:
    """Gera nodes/links para Sankey da DRE (determinístico)."""
    bu = args.get("bu", "consolidado")
    year = args.get("year") or get_projection_years()[-1]
    year = int(year)
    mode = args.get("mode", "dre_flow")
    sim = ctx["sim_json"]

    if mode == "bu_composition":
        return _build_bu_composition_sankey(sim, year)

    if bu == "consolidado":
        rows = sim.get("consolidado", [])
    else:
        rows = sim.get("dre", {}).get(bu, [])

    row = _get_row_for_year(rows, year)
    if not row:
        return {"error": f"Sem dados para {bu} em {year}"}

    rb = _safe_float(row.get("receita_bruta") or row.get("faturamento_bruto")) or 0
    ded = _safe_float(row.get("deducoes") or row.get("impostos_sv")) or 0
    rl = _safe_float(row.get("receita_liquida")) or 0
    mc1_val = _safe_float(row.get("mc1")) or 0
    mc2_val = _safe_float(row.get("mc2")) or 0
    ebitda_val = _safe_float(row.get("ebitda")) or 0
    ebit_val = _safe_float(row.get("ebit")) or 0
    lair_reportado = _safe_float(row.get("lair"))
    ll = _safe_float(row.get("lucro_liquido")) or 0

    # Fonte unica da verdade: subtotais ja calculados na DRE.
    # O Sankey deriva os "(-)" pela diferenca entre subtotais consecutivos.
    lair_val = lair_reportado if lair_reportado is not None else ebit_val
    custos_diretos = max(rl - mc1_val, 0.0)
    rem_socios = max(mc1_val - mc2_val, 0.0)
    desp_adm_total = max(mc2_val - ebitda_val, 0.0)
    da_total = max(ebitda_val - ebit_val, 0.0)
    resultado_fin_ganho = max(lair_val - ebit_val, 0.0)
    resultado_fin_perda = max(ebit_val - lair_val, 0.0)
    ir_csll_total = max(lair_val - ll, 0.0)

    nodes = [
        {"id": "receita_bruta", "label": "Receita Bruta"},
        {"id": "impostos", "label": "(-) Impostos"},
        {"id": "receita_liquida", "label": "Receita Líquida"},
        {"id": "custos_diretos", "label": "(-) Custos Diretos"},
        {"id": "mc1", "label": "MC1"},
        {"id": "rem_socios", "label": "(-) Rem. Sócios"},
        {"id": "mc2", "label": "MC2"},
        {"id": "desp_adm", "label": "(-) Desp. ADM"},
        {"id": "ebitda", "label": "EBITDA"},
        {"id": "da", "label": "(-) D&A"},
        {"id": "ebit", "label": "EBIT"},
        {"id": "resultado_fin", "label": "Result. Financeiro"},
        {"id": "lair", "label": "LAIR"},
        {"id": "irpj_csll", "label": "(-) IR/CSLL"},
        {"id": "lucro_liquido", "label": "Lucro Líquido"},
    ]

    links = [
        {"source": "receita_bruta", "target": "impostos", "value": abs(ded)},
        {"source": "receita_bruta", "target": "receita_liquida", "value": rl},
        {"source": "receita_liquida", "target": "custos_diretos", "value": custos_diretos},
        {"source": "receita_liquida", "target": "mc1", "value": mc1_val},
        {"source": "mc1", "target": "rem_socios", "value": rem_socios},
        {"source": "mc1", "target": "mc2", "value": mc2_val},
        {"source": "mc2", "target": "desp_adm", "value": desp_adm_total},
        {"source": "mc2", "target": "ebitda", "value": ebitda_val},
        {"source": "ebitda", "target": "da", "value": da_total},
        {"source": "ebitda", "target": "ebit", "value": ebit_val},
        {"source": "ebit", "target": "resultado_fin", "value": resultado_fin_perda},
        {"source": "ebit", "target": "lair", "value": lair_val - resultado_fin_ganho},
        {"source": "resultado_fin", "target": "lair", "value": resultado_fin_ganho},
        {"source": "lair", "target": "irpj_csll", "value": ir_csll_total},
        {"source": "lair", "target": "lucro_liquido", "value": max(0, ll)},
    ]

    links = [lk for lk in links if lk["value"] > 0]
    used_ids = {lk["source"] for lk in links} | {lk["target"] for lk in links}
    nodes = [n for n in nodes if n["id"] in used_ids]

    result = {
        "nodes": nodes,
        "links": links,
        "year": year,
        "bu": bu,
        "unit": "BRL",
    }
    ctx["_last_sankey_result"] = result
    return result


def _build_bu_composition_sankey(sim: dict, year: int) -> dict:
    """Sankey showing how each BU feeds into the consolidated result."""
    nodes = []
    links = []

    for bu_key in BU_KEYS:
        bu_rows = sim.get("dre", {}).get(bu_key, [])
        bu_row = _get_row_for_year(bu_rows, year)
        rl_bu = _safe_float(bu_row.get("receita_liquida")) or 0
        if rl_bu > 0:
            nodes.append({"id": bu_key, "label": BU_LABELS.get(bu_key, bu_key)})
            links.append({"source": bu_key, "target": "receita_liquida", "value": rl_bu})

    cons_row = _get_row_for_year(sim.get("consolidado", []), year)
    if not cons_row:
        return {"error": f"Sem dados consolidados para {year}"}

    rl = _safe_float(cons_row.get("receita_liquida")) or 0
    ebitda_val = _safe_float(cons_row.get("ebitda")) or 0
    ll = _safe_float(cons_row.get("lucro_liquido")) or 0
    custos_totais = rl - ebitda_val if rl > ebitda_val else 0
    deducoes_ll = ebitda_val - ll if ebitda_val > ll else 0

    nodes.extend([
        {"id": "receita_liquida", "label": "Receita Líquida"},
        {"id": "custos_totais", "label": "(-) Custos e Despesas"},
        {"id": "ebitda", "label": "EBITDA"},
        {"id": "abaixo_ebitda", "label": "(-) D&A, Fin. e IR"},
        {"id": "lucro_liquido", "label": "Lucro Líquido"},
    ])

    if custos_totais > 0:
        links.append({"source": "receita_liquida", "target": "custos_totais", "value": custos_totais})
    if ebitda_val > 0:
        links.append({"source": "receita_liquida", "target": "ebitda", "value": ebitda_val})
    if deducoes_ll > 0:
        links.append({"source": "ebitda", "target": "abaixo_ebitda", "value": deducoes_ll})
    if ll > 0:
        links.append({"source": "ebitda", "target": "lucro_liquido", "value": ll})

    links = [lk for lk in links if lk["value"] > 0]
    used_ids = {lk["source"] for lk in links} | {lk["target"] for lk in links}
    nodes = [n for n in nodes if n["id"] in used_ids]

    return {
        "nodes": nodes,
        "links": links,
        "year": year,
        "bu": "consolidado",
        "unit": "BRL",
    }


def _tool_build_artifact(args: dict, ctx: dict) -> dict:
    """Constrói um artifact com schema garantido e registra no acumulador."""
    artifact_type = args.get("artifact_type", "table")
    title = args.get("title", "")
    data = args.get("data")
    config = args.get("config", {})

    # Fallback: se o LLM não aninhou em "data", extrair campos conhecidos do nível raiz
    if data is None:
        known_meta = {"artifact_type", "title", "config", "type"}
        data = {k: v for k, v in args.items() if k not in known_meta}

    # Se o payload tem estrutura de matriz de sensibilidade, força heatmap.
    if isinstance(data, dict):
        has_matrix_shape = (
            isinstance(data.get("matrix"), list)
            and isinstance(data.get("row_values"), list)
            and isinstance(data.get("col_values"), list)
        )
        if has_matrix_shape:
            artifact_type = "heatmap"

    if artifact_type in ("line", "bar", "stacked_bar", "grouped_bar") and isinstance(data, dict):
        x_vals = data.get("x")
        series_vals = data.get("series")
        is_empty_chart = (not isinstance(x_vals, list) or len(x_vals) == 0) and (
            not isinstance(series_vals, list) or len(series_vals) == 0
        )
        if is_empty_chart:
            last_query = ctx.get("_last_query_result", {})
            candidates = []
            if isinstance(last_query, dict):
                if isinstance(last_query.get("current"), dict):
                    candidates.append(last_query["current"])
                if isinstance(last_query.get("historical"), dict):
                    candidates.append(last_query["historical"])
                candidates.append(last_query)
            for candidate in candidates:
                cand_x = candidate.get("x") if isinstance(candidate, dict) else None
                cand_series = candidate.get("series") if isinstance(candidate, dict) else None
                if isinstance(cand_x, list) and cand_x and isinstance(cand_series, list) and cand_series:
                    data = {
                        **data,
                        "x": cand_x,
                        "series": cand_series,
                        "unit": data.get("unit") or candidate.get("unit"),
                    }
                    break

        # Política conservadora: sem dados válidos, não inventar gráfico.
        # Evita casos em que o agente pede um chart (ex: CAGR) e o fallback
        # gera uma métrica padrão sem relação com a pergunta (ex: EBITDA).
        x_vals = data.get("x")
        series_vals = data.get("series")
        still_empty_chart = (not isinstance(x_vals, list) or len(x_vals) == 0) and (
            not isinstance(series_vals, list) or len(series_vals) == 0
        )
        if still_empty_chart:
            return {
                "status": "artifact_skipped",
                "reason": "insufficient_data_for_chart",
                "message": (
                    "Dados insuficientes para construir gráfico com segurança. "
                    "Rode query_data com a métrica/formato corretos ou use table/kpi_panel."
                ),
            }

    if artifact_type == "heatmap" and isinstance(data, dict):
        has_heatmap_data = (
            isinstance(data.get("row_values"), list)
            and len(data.get("row_values", [])) > 0
            and isinstance(data.get("col_values"), list)
            and len(data.get("col_values", [])) > 0
            and isinstance(data.get("matrix"), list)
            and len(data.get("matrix", [])) > 0
        )
        if not has_heatmap_data:
            last_sens = ctx.get("_last_sensitivity_result", {})
            if isinstance(last_sens, dict) and isinstance(last_sens.get("matrix"), list) and len(last_sens.get("matrix", [])) > 0:
                data = {
                    **data,
                    "row_param": data.get("row_param") or last_sens.get("row_param", "wacc"),
                    "col_param": data.get("col_param") or last_sens.get("col_param", "g"),
                    "row_values": last_sens.get("row_values", []),
                    "col_values": last_sens.get("col_values", []),
                    "matrix": last_sens.get("matrix", []),
                }

    if artifact_type == "sankey" and isinstance(data, dict):
        has_sankey_data = (
            isinstance(data.get("nodes"), list)
            and len(data.get("nodes", [])) > 0
            and isinstance(data.get("links"), list)
            and len(data.get("links", [])) > 0
        )
        if not has_sankey_data:
            last_sankey = ctx.get("_last_sankey_result", {})
            if isinstance(last_sankey, dict) and isinstance(last_sankey.get("nodes"), list) and len(last_sankey.get("nodes", [])) > 0:
                data = {
                    **data,
                    "nodes": last_sankey.get("nodes", []),
                    "links": last_sankey.get("links", []),
                    "year": data.get("year") or last_sankey.get("year"),
                    "bu": data.get("bu") or last_sankey.get("bu"),
                    "unit": data.get("unit") or last_sankey.get("unit", "BRL"),
                }

    if artifact_type == "table" and isinstance(data, dict):
        has_table_data = (
            isinstance(data.get("columns"), list)
            and len(data.get("columns", [])) > 0
            and isinstance(data.get("rows"), list)
            and len(data.get("rows", [])) > 0
        )
        if not has_table_data:
            last_query = ctx.get("_last_query_result", {})
            candidates: list[dict] = []
            if isinstance(last_query, dict):
                if isinstance(last_query.get("current"), dict):
                    candidates.append(last_query["current"])
                if isinstance(last_query.get("historical"), dict):
                    candidates.append(last_query["historical"])
                candidates.append(last_query)

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                cand_x = candidate.get("x")
                cand_series = candidate.get("series")
                if isinstance(cand_x, list) and cand_x and isinstance(cand_series, list) and cand_series:
                    columns = ["Série", *[str(x) for x in cand_x]]
                    rows = []
                    for s in cand_series:
                        if not isinstance(s, dict):
                            continue
                        rows.append([str(s.get("name", "Série")), *list(s.get("values", []))])
                    if rows:
                        data = {**data, "columns": columns, "rows": rows}
                        break

                cand_items = candidate.get("items")
                if isinstance(cand_items, list) and cand_items:
                    columns = ["Indicador", "Valor"]
                    rows = []
                    for item in cand_items:
                        if isinstance(item, dict):
                            rows.append([str(item.get("label", "")), item.get("value")])
                    if rows:
                        data = {**data, "columns": columns, "rows": rows}
                        break

    if artifact_type in ("line", "bar", "stacked_bar", "grouped_bar") and isinstance(data, dict):
        split_payloads = _split_chart_payloads_if_needed(title, artifact_type, data, config)
        if len(split_payloads) > 1:
            created = 0
            for payload in split_payloads:
                artifact = _build_validated_artifact(
                    payload["artifact_type"],
                    payload["title"],
                    payload["data"],
                    payload["config"],
                )
                ctx.setdefault("_accumulated_artifacts", []).append(artifact)
                created += 1
            return {
                "status": "artifact_created_multiple",
                "type": artifact_type,
                "title": title,
                "artifacts_created": created,
            }

    artifact = _build_validated_artifact(artifact_type, title, data, config)

    import logging as _log
    _log.getLogger(__name__).info(
        "build_artifact: type=%s chart_type=%s x_len=%s series_len=%s",
        artifact.get("type"), artifact.get("chart_type"),
        len(artifact.get("x", [])), len(artifact.get("series", [])),
    )

    ctx.setdefault("_accumulated_artifacts", []).append(artifact)

    return {
        "status": "artifact_created",
        "type": artifact_type,
        "title": title,
    }


# ---------------------------------------------------------------------------
# Auxiliary functions
# ---------------------------------------------------------------------------


def deep_merge(base: dict, overrides: dict) -> dict:
    """Merge profundo. Dot-notation keys são expandidas.
    Ex: {"renovacao.churn": 0.20} -> {"renovacao": {"churn": 0.20}}
    """
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        parts = key.split(".")
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        if isinstance(value, dict) and isinstance(target.get(parts[-1]), dict):
            target[parts[-1]] = deep_merge(target[parts[-1]], value)
        else:
            target[parts[-1]] = value
    return result


def _normalize_param(param: str) -> str:
    """Normaliza nomes de parâmetros para dot-notation."""
    raw = str(param).strip().replace(" ", "").lower()
    shortcuts = {
        "wacc": "dcf.wacc",
        "g": "dcf.g",
        "churn": "renovacao.churn",
    }
    return shortcuts.get(raw, raw)


def _canonical_premissa_dot_key(dot_key: str) -> str:
    """Alinha aliases de BU com as chaves do run_simulation (premissas)."""
    k = str(dot_key).strip()
    if k.startswith("venda_sw."):
        return "venda_softwares." + k[len("venda_sw.") :]
    return k


RATIO_PARAM_KEYS = {
    "dcf.wacc",
    "dcf.g",
    "renovacao.churn",
    "renovacao.spread_real",
    "ams.taxa_conversao_fopm",
    "ams.churn",
    "venda_softwares.fator_crescimento_real",
}


_METRIC_ALIASES: dict[str, str] = {
    "n_funcionarios": "headcount",
}


def _normalize_metric_name(metric: Any) -> str:
    """Normaliza aliases de métrica para uma chave canônica."""
    raw = str(metric).strip().lower()
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    normalized = raw.replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    normalized = _METRIC_ALIASES.get(normalized, normalized)

    # Aliases textuais comuns para métricas derivadas.
    base_candidates = ("receita_liquida", "ebitda", "faturamento_bruto", "lucro_liquido", "headcount")
    for base in base_candidates:
        has_base = base in normalized
        if not has_base and base == "faturamento_bruto" and "receita_bruta" in normalized:
            has_base = True
        if not has_base:
            continue
        if "cagr" in normalized:
            return f"{base}_cagr"
        if "yoy" in normalized or "variacao_anual_percentual" in normalized or "variacao_percentual_anual" in normalized:
            return f"{base}_yoy_pct"
        if "delta_pct" in normalized or "variacao_percentual" in normalized:
            return f"{base}_delta_pct"

    return normalized


def _normalize_metric_list(metrics: list[Any]) -> list[str]:
    """Normaliza lista de métricas preservando ordem e removendo duplicadas."""
    normalized: list[str] = []
    seen: set[str] = set()
    for metric in metrics:
        name = _normalize_metric_name(metric)
        if name in seen:
            continue
        normalized.append(name)
        seen.add(name)
    return normalized


def _parse_derived_metric(metric: str) -> tuple[str, str] | None:
    """Retorna (kind, base_metric) para métricas derivadas com sufixo conhecido."""
    raw = str(metric).strip().lower()
    for suffix, kind in (
        ("_yoy_pct", "yoy_pct"),
        ("_delta_pct", "delta_pct"),
        ("_cagr", "cagr"),
    ):
        if raw.endswith(suffix) and len(raw) > len(suffix):
            base = raw[: -len(suffix)]
            return (kind, base)
    return None


def _is_percent_metric_name(metric_name: str) -> bool:
    m = str(metric_name).lower()
    return (
        "margem" in m
        or "_pct" in m
        or m.endswith("_cagr")
        or m.endswith("_yoy_pct")
        or m.endswith("_delta_pct")
    )


def _extract_metric_hint_from_series_name(series_name: str) -> str:
    raw = str(series_name or "").strip().lower()
    if " - " in raw:
        return raw.split(" - ")[-1].strip()
    return raw


def _split_chart_payloads_if_needed(title: str, artifact_type: str, data: dict, config: dict) -> list[dict[str, Any]]:
    """Divide charts apenas quando houver excesso de séries (legibilidade)."""
    series = data.get("series")
    if not isinstance(series, list) or len(series) <= 1:
        return [{"artifact_type": artifact_type, "title": title, "data": data, "config": config}]

    metric_hints: set[str] = set()
    for item in series:
        if not isinstance(item, dict):
            continue
        hint = _extract_metric_hint_from_series_name(str(item.get("name", "")))
        metric_hints.add(hint)

    too_many_series = len(series) > 6 and len(metric_hints) > 1
    if not too_many_series:
        return [{"artifact_type": artifact_type, "title": title, "data": data, "config": config}]

    # Com muitas séries heterogêneas, ainda dividimos em dois blocos para leitura.
    midpoint = len(series) // 2
    return [
        {
            "artifact_type": artifact_type,
            "title": f"{title} — Parte 1",
            "data": {**data, "series": series[:midpoint]},
            "config": config,
        },
        {
            "artifact_type": artifact_type,
            "title": f"{title} — Parte 2",
            "data": {**data, "series": series[midpoint:]},
            "config": config,
        },
    ]


def _pct_delta_ratio(initial: float | None, current: float | None) -> float | None:
    if initial in (None, 0) or current is None:
        return None
    return (current - initial) / initial


def _cagr_ratio(initial: float | None, current: float | None, periods: int) -> float | None:
    if periods <= 0 or initial in (None, 0) or current is None:
        return None
    # CAGR real requer base e final positivos para evitar resultados complexos.
    if initial <= 0 or current <= 0:
        return None
    return (current / initial) ** (1.0 / periods) - 1.0


def _broadcast_sensitivity_value(
    param_key: str,
    scalar_value: float,
    premissas: dict[str, Any] | None = None,
) -> Any:
    """
    Sensibilidade pode variar drivers que no motor são dict por ano (ex: headcount_por_ano).
    O heatmap passa um escalar; aqui transformamos em dict ano->valor para o motor não quebrar.
    """
    norm = _normalize_param(param_key)
    if norm.endswith("headcount_por_ano"):
        # Para `*_por_ano`, o heatmap passa um escalar (um tick do eixo).
        # Para manter coerência com uma série temporal, tratamos o escalar como:
        # - se |scalar_value| <= 1 e houver caso base: delta percentual do headcount base_year
        # - caso contrário: headcount absoluto no base_year
        #
        # Em ambos os casos, escalamos proporcionalmente o CASO BASE (ano->valor) mantendo o "shape"
        # da série ao longo do horizonte.
        bu_key = norm.split(".", 1)[0] if "." in norm else norm
        base_year = str(get_projection_years()[0]) if get_projection_years() else "2026"

        hc_by_year: dict[Any, Any] | None = None
        base_hc: float | None = None
        if premissas and isinstance(premissas.get(bu_key), dict):
            candidate = premissas.get(bu_key, {}).get("headcount_por_ano")
            if isinstance(candidate, dict):
                hc_by_year = candidate
                base_hc = _safe_float(
                    hc_by_year.get(base_year)
                    if base_year in hc_by_year
                    else hc_by_year.get(int(base_year))  # type: ignore[arg-type]
                )

        scalar_fv = float(scalar_value)
        if base_hc is None:
            # Fallback: sem caso base (ou sem premissas), preserva o comportamento anterior.
            v = int(round(scalar_fv))
            return {str(y): v for y in get_projection_years()}

        # Target headcount no base_year
        if -1.0 <= scalar_fv <= 1.0:
            target_base_hc = base_hc * (1.0 + scalar_fv)
        else:
            target_base_hc = scalar_fv

        ratio = 0.0 if base_hc == 0.0 else (target_base_hc / base_hc)

        out: dict[str, int] = {}
        for y in get_projection_years():
            if hc_by_year is not None:
                base_y_val = _safe_float(
                    hc_by_year.get(str(y))
                    if str(y) in hc_by_year
                    else hc_by_year.get(int(y))  # type: ignore[arg-type]
                )
            else:
                base_y_val = None

            if base_y_val is None:
                base_y_val = base_hc

            v = int(round(max(0.0, base_y_val * ratio)))
            out[str(y)] = v
        return out

    if norm.endswith("ociosidade_por_ano"):
        # Ociosidade normalmente é razão (0-1). Se vier como "percentual" (5 -> 5%), convertemos.
        fv = float(scalar_value)
        ratio = fv / 100.0 if abs(fv) > 1.0 else fv
        return {str(y): ratio for y in get_projection_years()}

    return scalar_value


def _normalize_ratio_value(param_key: str, value: Any) -> Any:
    """Normaliza percentuais para ratio (14 -> 0.14) quando aplicável."""
    if param_key not in RATIO_PARAM_KEYS:
        return value
    if isinstance(value, str):
        txt = value.strip().replace("%", "").replace(",", ".")
        numeric = _safe_float(txt)
    else:
        numeric = _safe_float(value)
    if numeric is None:
        return value
    if abs(numeric) > 1.0:
        return numeric / 100.0
    return numeric


def _normalize_premissa_changes(changes: dict) -> dict:
    """Normaliza payload de premissas da tool (aliases + escala percentual)."""
    if not isinstance(changes, dict):
        return {}

    flattened: dict[str, Any] = {}

    def _walk(node: Any, prefix: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                key = str(k)
                path = f"{prefix}.{key}" if prefix else key
                _walk(v, path)
            return

        normalized_key = _canonical_premissa_dot_key(_normalize_param(prefix))
        flattened[normalized_key] = _normalize_ratio_value(normalized_key, node)

    _walk(changes)
    return flattened


def _infer_premissa_changes_from_question(question: str, premissas: dict[str, Any]) -> dict[str, Any]:
    """Inferência conservadora de premissas para pedidos comuns em linguagem natural."""
    q = str(question or "").lower()
    if not q:
        return {}

    asks_half = any(token in q for token in ("metade", "50%", "meio"))
    mentions_ams = "ams" in q
    mentions_conversao = "convers" in q
    if asks_half and mentions_ams and mentions_conversao:
        base_val = _safe_float(
            premissas.get("ams", {}).get("taxa_conversao_fopm") if isinstance(premissas.get("ams"), dict) else None
        )
        if base_val is not None:
            return {"ams.taxa_conversao_fopm": max(0.0, base_val * 0.5)}

    # Ex.: "contratar mais 5 pessoas na FOPM em 2027"
    mentions_people = any(token in q for token in ("pessoa", "pessoas", "funcionario", "funcionarios", "headcount"))
    mentions_hiring = any(token in q for token in ("contratar", "aumentar", "subir", "acrescentar", "adicionar", "mais"))
    mentions_firing = any(token in q for token in ("reduzir", "diminuir", "cortar", "demitir", "menos"))
    bu_key = None
    if "fopm" in q:
        bu_key = "fopm"
    elif "data science" in q or "data_science" in q:
        bu_key = "data_science"
    if mentions_people and bu_key:
        year_match = re.search(r"\b(20[0-9]{2})\b", q)
        delta_match = (
            re.search(r"(?:mais|aumentar|subir|acrescentar|adicionar)\s+([0-9]+)", q)
            or re.search(r"(?:menos|reduzir|diminuir|cortar|demitir)\s+([0-9]+)", q)
            or re.search(r"([+-][0-9]+)", q)
        )
        if year_match and delta_match:
            year = year_match.group(1)
            delta = int(delta_match.group(1))
            if mentions_firing and delta > 0:
                delta = -delta
            elif mentions_hiring and delta < 0:
                delta = abs(delta)

            base_val = _safe_float(
                premissas.get(bu_key, {}).get("headcount_por_ano", {}).get(year)
                if isinstance(premissas.get(bu_key), dict)
                else None
            )
            if base_val is not None:
                new_val = max(0, int(round(base_val + delta)))
                return {f"{bu_key}.headcount_por_ano.{year}": new_val}

    # Ex.: "wacc para 14%" (aceita formato decimal e percentual)
    if "wacc" in q:
        m = re.search(r"wacc[^0-9]*([0-9]+(?:[.,][0-9]+)?)", q)
        if m:
            raw = m.group(1).replace(",", ".")
            val = _safe_float(raw)
            if val is not None:
                return {"dcf.wacc": val / 100.0 if val > 1 else val}

    return {}


def _linspace(start: float, stop: float, steps: int) -> list[float]:
    if steps <= 1:
        return [start]
    step_size = (stop - start) / (steps - 1)
    return [round(start + i * step_size, 6) for i in range(steps)]


def _extract_resumo_consolidado(sim_json: dict) -> dict:
    consolidado_rows = sim_json.get("consolidado", [])
    result = {}
    for year in get_projection_years():
        row = _get_row_for_year(consolidado_rows, year)
        if not row:
            continue
        result[str(year)] = {
            "receita_liquida": _safe_float(row.get("receita_liquida")),
            "ebitda": _safe_float(row.get("ebitda")),
            "margem_ebitda": _safe_float(row.get("ebitda_pct_rl")),
            "lucro_liquido": _safe_float(row.get("lucro_liquido")),
        }
    return result


def _extract_dcf_summary(sim_json: dict) -> dict:
    dcf = sim_json.get("dcf", {})
    result = {
        "enterprise_value": _safe_float(dcf.get("enterprise_value")),
        "equity_value": _safe_float(dcf.get("equity_value")),
        "wacc": _safe_float(dcf.get("wacc")),
        "g": _safe_float(dcf.get("g")),
    }
    multiplos = dcf.get("multiplos", {})
    ev_ebitda = next((v for k, v in multiplos.items() if "EV_EBITDA" in k), None)
    if ev_ebitda is not None:
        result["ev_ebitda_implicito"] = _safe_float(ev_ebitda)
    return result


def _extract_metric(sim_json: dict, metric: str) -> float | None:
    dcf = sim_json.get("dcf", {})
    if metric in dcf:
        return _safe_float(dcf[metric])
    if metric == "ev_ebitda":
        multiplos = dcf.get("multiplos", {})
        val = next((v for k, v in multiplos.items() if "EV_EBITDA" in k), None)
        return _safe_float(val) if val is not None else None
    consolidado_rows = sim_json.get("consolidado", [])
    if consolidado_rows:
        last_row = consolidado_rows[-1]
        return _resolve_metric_value(last_row, metric)
    return None


def _compute_comparison(
    base: dict, alt: dict, metrics: list, granularity: str,
    base_label: str = "base", alt_label: str = "alternativo",
) -> dict:
    result: dict[str, Any] = {
        "base_label": base_label,
        "alt_label": alt_label,
        "metrics": {},
    }

    anos = [str(y) for y in get_projection_years()]

    for metric in metrics:
        if metric in ("enterprise_value", "equity_value"):
            base_val = _safe_float(base.get("dcf", {}).get(metric, 0)) or 0
            alt_val = _safe_float(alt.get("dcf", {}).get(metric, 0)) or 0
            delta = alt_val - base_val
            delta_pct = (delta / base_val * 100) if base_val != 0 else 0
            result["metrics"][metric] = {
                "valor": {
                    "base": base_val,
                    "alternativo": alt_val,
                    "delta": round(delta, 2),
                    "delta_pct": round(delta_pct, 2),
                }
            }
            continue

        metric_result: dict[str, Any] = {}

        if granularity in ("consolidado", "ambos"):
            metric_result["consolidado"] = {}
            base_rows = base.get("consolidado", [])
            alt_rows = alt.get("consolidado", [])
            for ano_str in anos:
                ano_int = int(ano_str)
                base_row = _get_row_for_year(base_rows, ano_int)
                alt_row = _get_row_for_year(alt_rows, ano_int)
                base_val = _resolve_metric_value(base_row, metric) or 0
                alt_val = _resolve_metric_value(alt_row, metric) or 0
                delta = alt_val - base_val
                delta_pct = (delta / base_val * 100) if base_val != 0 else 0
                metric_result["consolidado"][ano_str] = {
                    "base": round(base_val, 2),
                    "alternativo": round(alt_val, 2),
                    "delta": round(delta, 2),
                    "delta_pct": round(delta_pct, 2),
                }

        if granularity in ("por_bu", "ambos"):
            metric_result["por_bu"] = {}
            for bu in BU_KEYS:
                metric_result["por_bu"][bu] = {}
                base_bu_rows = base.get("dre", {}).get(bu, [])
                alt_bu_rows = alt.get("dre", {}).get(bu, [])
                for ano_str in anos:
                    ano_int = int(ano_str)
                    base_row = _get_row_for_year(base_bu_rows, ano_int)
                    alt_row = _get_row_for_year(alt_bu_rows, ano_int)
                    base_val = _resolve_metric_value(base_row, metric) or 0
                    alt_val = _resolve_metric_value(alt_row, metric) or 0
                    delta = alt_val - base_val
                    delta_pct = (delta / base_val * 100) if base_val != 0 else 0
                    metric_result["por_bu"][bu][ano_str] = {
                        "base": round(base_val, 2),
                        "alternativo": round(alt_val, 2),
                        "delta": round(delta, 2),
                        "delta_pct": round(delta_pct, 2),
                    }

        result["metrics"][metric] = metric_result

    return result


DERIVED_METRIC_RULES: dict[str, dict[str, Any]] = {
    # Regras declarativas de métricas derivadas (genérico e extensível).
    "margem_ebitda": {"op": "ratio", "num": "ebitda", "den": "receita_liquida"},
    "ebitda_pct_rl": {"op": "ratio", "num": "ebitda", "den": "receita_liquida"},
    "custos_totais": {"op": "sum", "fields": ["gastos_pessoal", "outras_desp_diretas", "outras_desp_adm"]},
}


def _apply_derived_rule(row: dict, metric: str) -> float | None:
    rule = DERIVED_METRIC_RULES.get(metric)
    if not rule:
        return None

    op = rule.get("op")
    if op == "sum":
        values = [_safe_float(row.get(field)) for field in rule.get("fields", [])]
        valid = [v for v in values if v is not None]
        return float(sum(valid)) if valid else None

    if op == "ratio":
        num = _safe_float(row.get(rule.get("num", "")))
        den = _safe_float(row.get(rule.get("den", "")))
        if num is None or den in (None, 0):
            return None
        return num / den

    return None


def _resolve_metric_value(row: dict, metric: str) -> float | None:
    """Resolve aliases de métricas e fallback de cálculo."""
    normalized_metric = _normalize_metric_name(metric)
    aliases = {
        "margem_ebitda": ["margem_ebitda", "ebitda_pct_rl", "ebitda_margin"],
        "ebitda_pct_rl": ["ebitda_pct_rl", "margem_ebitda", "ebitda_margin"],
        "faturamento_bruto": ["faturamento_bruto", "receita_bruta"],
        "headcount": ["headcount", "n_funcionarios", "n_funcionarios_adm"],
        "n_funcionarios": ["headcount", "n_funcionarios", "n_funcionarios_adm"],
    }
    candidates = aliases.get(normalized_metric, [normalized_metric])

    for key in candidates:
        val = _safe_float(row.get(key))
        if val is not None:
            return val

    return _apply_derived_rule(row, normalized_metric)


def _extract_data_from_sim(
    sim_json: dict, metrics: list, bus: list, years: list | None, fmt: str,
) -> dict:
    """Extrai dados da simulação atual conforme parâmetros."""
    anos = years or list(get_projection_years())
    anos_str = [str(a) for a in anos]
    result: dict[str, Any] = {}

    if fmt == "timeseries":
        result["x"] = anos_str
        result["series"] = []

        for bu in bus:
            for metric in metrics:
                if bu == "consolidado":
                    rows = sim_json.get("consolidado", [])
                else:
                    rows = sim_json.get("dre", {}).get(bu, [])

                values = []
                derived = _parse_derived_metric(metric)
                if derived:
                    kind, base_metric = derived
                    base_values: list[float] = []
                    for ano_int in anos:
                        row = _get_row_for_year(rows, ano_int)
                        base_val = _resolve_metric_value(row, base_metric)
                        base_values.append(0 if base_val is None else base_val)
                    for idx, current in enumerate(base_values):
                        if kind == "yoy_pct":
                            if idx == 0:
                                values.append(0)
                            else:
                                ratio = _pct_delta_ratio(base_values[idx - 1], current)
                                values.append(0 if ratio is None else ratio)
                        elif kind == "delta_pct":
                            ratio = _pct_delta_ratio(base_values[0], current)
                            values.append(0 if ratio is None else ratio)
                        elif kind == "cagr":
                            ratio = _cagr_ratio(base_values[0], current, idx)
                            values.append(0 if ratio is None else ratio)
                        else:
                            values.append(0)
                else:
                    for ano_int in anos:
                        row = _get_row_for_year(rows, ano_int)
                        val = _resolve_metric_value(row, metric)
                        if val is None:
                            val = 0
                        values.append(val)

                metric_lower = str(metric).lower()
                metric_is_pct = (
                    "margem" in metric_lower
                    or "_pct" in metric_lower
                    or metric_lower.endswith("_yoy_pct")
                    or metric_lower.endswith("_delta_pct")
                    or metric_lower.endswith("_cagr")
                    or "yoy" in metric_lower
                    or "cagr" in metric_lower
                    or "delta_pct" in metric_lower
                )

                if len(bus) > 1 and len(metrics) > 1:
                    series_name = f"{BU_LABELS.get(bu, bu)} - {metric}"
                elif len(bus) > 1:
                    # Para métricas percentuais derivadas, inclui o nome da métrica
                    # para que a tabela possa formatar corretamente.
                    series_name = f"{BU_LABELS.get(bu, bu)} - {metric}" if metric_is_pct else BU_LABELS.get(bu, bu)
                elif len(metrics) > 1:
                    series_name = metric
                else:
                    series_name = BU_LABELS.get(bu, bu) if bu != "consolidado" else metric
                result["series"].append({"name": series_name, "values": values})

    elif fmt == "snapshot":
        ano = anos[0] if anos else 2030
        result["items"] = []
        for bu in bus:
            if bu == "consolidado":
                rows = sim_json.get("consolidado", [])
            else:
                rows = sim_json.get("dre", {}).get(bu, [])
            for metric in metrics:
                derived = _parse_derived_metric(metric)
                if derived and len(anos) >= 2:
                    kind, base_metric = derived
                    first_row = _get_row_for_year(rows, anos[0])
                    last_row = _get_row_for_year(rows, anos[-1])
                    first_val = _resolve_metric_value(first_row, base_metric)
                    last_val = _resolve_metric_value(last_row, base_metric)
                    if kind == "yoy_pct":
                        val = _pct_delta_ratio(first_val, last_val)
                    elif kind == "delta_pct":
                        val = _pct_delta_ratio(first_val, last_val)
                    else:
                        val = _cagr_ratio(first_val, last_val, max(1, len(anos) - 1))
                else:
                    row = _get_row_for_year(rows, ano)
                    val = _resolve_metric_value(row, metric)
                label = f"{metric} ({BU_LABELS.get(bu, bu)}) — {ano}"
                result["items"].append({"label": label, "value": val})

        dcf = sim_json.get("dcf", {})
        for metric in metrics:
            if metric in dcf:
                result["items"].append({
                    "label": metric,
                    "value": _safe_float(dcf[metric]),
                })
            elif metric == "ev_ebitda_implicito":
                multiplos = dcf.get("multiplos", {})
                val = next((v for k, v in multiplos.items() if "EV_EBITDA" in k), None)
                if val is not None:
                    result["items"].append({
                        "label": "EV/EBITDA implícito",
                        "value": _safe_float(val),
                    })

    elif fmt == "decomposition":
        metric = metrics[0] if metrics else "ebitda"
        result["categories"] = []
        result["values"] = []
        derived = _parse_derived_metric(metric)
        for bu in bus:
            if bu == "consolidado":
                continue
            rows = sim_json.get("dre", {}).get(bu, [])
            if derived and len(anos) >= 2:
                kind, base_metric = derived
                first_row = _get_row_for_year(rows, anos[0])
                last_row = _get_row_for_year(rows, anos[-1])
                first_val = _resolve_metric_value(first_row, base_metric)
                last_val = _resolve_metric_value(last_row, base_metric)
                if kind in ("yoy_pct", "delta_pct"):
                    val = _pct_delta_ratio(first_val, last_val)
                else:
                    val = _cagr_ratio(first_val, last_val, max(1, len(anos) - 1))
            else:
                ano = anos[-1] if anos else 2030
                row = _get_row_for_year(rows, ano)
                val = _resolve_metric_value(row, metric)
            if val is None:
                val = 0
            result["categories"].append(BU_LABELS.get(bu, bu))
            result["values"].append(val)

    return result


def _extract_data_from_historical(
    historical_bundle: dict, metrics: list, bus: list, years: list | None, fmt: str,
) -> dict:
    """Extrai dados históricos. Mesmo formato de saída que _extract_data_from_sim."""
    if not historical_bundle:
        return {"error": "Dados históricos não disponíveis"}

    hist_start = historical_bundle.get("historical_year_start", 2018)
    hist_end = historical_bundle.get("historical_year_end", 2025)
    anos = years or list(range(hist_start, hist_end + 1))
    anos_str = [str(a) for a in anos]
    result: dict[str, Any] = {}

    if fmt == "timeseries":
        result["x"] = anos_str
        result["series"] = []

        for bu in bus:
            for metric in metrics:
                if bu == "consolidado":
                    rows = historical_bundle.get("consolidado", [])
                else:
                    rows = historical_bundle.get("dre", {}).get(bu, [])

                values = []
                derived = _parse_derived_metric(metric)
                if derived:
                    kind, base_metric = derived
                    base_values: list[float] = []
                    for ano_int in anos:
                        row = _get_row_for_year(rows, ano_int)
                        base_val = _resolve_metric_value(row, base_metric)
                        base_values.append(0 if base_val is None else base_val)
                    for idx, current in enumerate(base_values):
                        if kind == "yoy_pct":
                            if idx == 0:
                                values.append(0)
                            else:
                                ratio = _pct_delta_ratio(base_values[idx - 1], current)
                                values.append(0 if ratio is None else ratio)
                        elif kind == "delta_pct":
                            ratio = _pct_delta_ratio(base_values[0], current)
                            values.append(0 if ratio is None else ratio)
                        elif kind == "cagr":
                            ratio = _cagr_ratio(base_values[0], current, idx)
                            values.append(0 if ratio is None else ratio)
                        else:
                            values.append(0)
                else:
                    for ano_int in anos:
                        row = _get_row_for_year(rows, ano_int)
                        val = _resolve_metric_value(row, metric)
                        if val is None:
                            val = 0
                        values.append(val)

                if len(bus) > 1 and len(metrics) > 1:
                    series_name = f"{BU_LABELS.get(bu, bu)} - {metric}"
                elif len(bus) > 1:
                    series_name = BU_LABELS.get(bu, bu)
                else:
                    series_name = metric
                result["series"].append({"name": series_name, "values": values})

    elif fmt == "snapshot":
        ano = anos[-1] if anos else hist_end
        result["items"] = []
        for bu in bus:
            if bu == "consolidado":
                rows = historical_bundle.get("consolidado", [])
            else:
                rows = historical_bundle.get("dre", {}).get(bu, [])
            for metric in metrics:
                derived = _parse_derived_metric(metric)
                if derived and len(anos) >= 2:
                    kind, base_metric = derived
                    first_row = _get_row_for_year(rows, anos[0])
                    last_row = _get_row_for_year(rows, anos[-1])
                    first_val = _resolve_metric_value(first_row, base_metric)
                    last_val = _resolve_metric_value(last_row, base_metric)
                    if kind in ("yoy_pct", "delta_pct"):
                        val = _pct_delta_ratio(first_val, last_val)
                    else:
                        val = _cagr_ratio(first_val, last_val, max(1, len(anos) - 1))
                else:
                    row = _get_row_for_year(rows, ano)
                    val = _resolve_metric_value(row, metric)
                label = f"{metric} ({BU_LABELS.get(bu, bu)}) — {ano}"
                result["items"].append({"label": label, "value": val})

    elif fmt == "decomposition":
        metric = metrics[0] if metrics else "ebitda"
        result["categories"] = []
        result["values"] = []
        derived = _parse_derived_metric(metric)
        for bu in bus:
            if bu == "consolidado":
                continue
            rows = historical_bundle.get("dre", {}).get(bu, [])
            if derived and len(anos) >= 2:
                kind, base_metric = derived
                first_row = _get_row_for_year(rows, anos[0])
                last_row = _get_row_for_year(rows, anos[-1])
                first_val = _resolve_metric_value(first_row, base_metric)
                last_val = _resolve_metric_value(last_row, base_metric)
                if kind in ("yoy_pct", "delta_pct"):
                    val = _pct_delta_ratio(first_val, last_val)
                else:
                    val = _cagr_ratio(first_val, last_val, max(1, len(anos) - 1))
            else:
                ano = anos[-1] if anos else hist_end
                row = _get_row_for_year(rows, ano)
                val = _resolve_metric_value(row, metric)
            if val is None:
                val = 0
            result["categories"].append(BU_LABELS.get(bu, bu))
            result["values"].append(val)

    return result


def _build_validated_artifact(
    artifact_type: str, title: str, data: dict, config: dict,
) -> dict:
    """Constrói artifact com schema validado, mapeando do formato tool para o formato Pydantic."""
    def _normalize_xy_payload(payload: dict) -> tuple[list, list[dict]]:
        x_vals = payload.get("x")
        if not isinstance(x_vals, list):
            x_vals = payload.get("labels")
        if not isinstance(x_vals, list):
            x_vals = payload.get("categories")
        if not isinstance(x_vals, list):
            x_vals = []

        raw_series = payload.get("series")
        series: list[dict] = []

        if isinstance(raw_series, list):
            for item in raw_series:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("label") or "Série"
                values = item.get("values")
                if not isinstance(values, list):
                    values = item.get("data")
                if not isinstance(values, list):
                    values = []
                series.append({"name": str(name), "values": values})
        elif isinstance(raw_series, dict):
            for key, values in raw_series.items():
                if isinstance(values, list):
                    series.append({"name": str(key), "values": values})

        if not series and isinstance(payload.get("datasets"), list):
            for ds in payload["datasets"]:
                if not isinstance(ds, dict):
                    continue
                name = ds.get("name") or ds.get("label") or "Série"
                values = ds.get("values")
                if not isinstance(values, list):
                    values = ds.get("data")
                if not isinstance(values, list):
                    values = []
                series.append({"name": str(name), "values": values})

        if not series and isinstance(payload.get("values"), list):
            series = [{"name": str(payload.get("name") or payload.get("label") or title), "values": payload.get("values", [])}]

        return x_vals, series

    if artifact_type in ("line", "bar", "stacked_bar", "grouped_bar"):
        x_vals, series = _normalize_xy_payload(data)
        return {
            "type": "chart",
            "chart_type": artifact_type,
            "title": title,
            "x": x_vals,
            "series": series,
            "unit": data.get("unit") or config.get("unit", ""),
            "reference_line": config.get("reference_line"),
        }

    elif artifact_type == "waterfall":
        return {
            "type": "chart",
            "chart_type": "waterfall",
            "title": title,
            "x": data.get("categories", []),
            "series": [{"name": title, "values": data.get("values", [])}],
            "unit": data.get("unit") or config.get("unit", ""),
        }

    elif artifact_type == "heatmap":
        return {
            "type": "sensitivity_matrix",
            "title": title,
            "row_param": data.get("row_param", ""),
            "col_param": data.get("col_param", ""),
            "row_values": data.get("row_values", []),
            "col_values": data.get("col_values", []),
            "matrix": data.get("matrix", []),
        }

    elif artifact_type == "sankey":
        return {
            "type": "sankey",
            "title": title,
            "nodes": data.get("nodes", []),
            "links": data.get("links", []),
            "unit": data.get("unit") or config.get("unit", "BRL"),
            "year": data.get("year"),
            "bu": data.get("bu"),
        }

    elif artifact_type == "table":
        return {
            "type": "table",
            "title": title,
            "columns": data.get("columns", []),
            "rows": data.get("rows", []),
        }

    elif artifact_type == "kpi_panel":
        items = data.get("items", [])
        kpi_items = []
        for item in items:
            if "title" in item:
                kpi_items.append({
                    "type": "kpi",
                    "title": item.get("title", item.get("label", "")),
                    "value": str(item.get("value", "")),
                    "subtitle": item.get("subtitle") or item.get("delta"),
                })
            else:
                kpi_items.append({
                    "type": "kpi",
                    "title": item.get("label", ""),
                    "value": str(item.get("value", "")),
                    "subtitle": item.get("delta"),
                })
        return {
            "type": "kpi_panel",
            "title": title,
            "items": kpi_items,
        }

    else:
        return {
            "type": "table",
            "title": title,
            "columns": ["Info"],
            "rows": [["Tipo de artifact não reconhecido"]],
        }


def _merge_timeseries_payloads(
    historical_payload: dict | None,
    current_payload: dict | None,
) -> dict[str, Any] | None:
    """Mescla payloads de timeseries em uma série contínua por nome."""
    hist = historical_payload if isinstance(historical_payload, dict) else {}
    curr = current_payload if isinstance(current_payload, dict) else {}

    hist_x = hist.get("x")
    curr_x = curr.get("x")
    hist_series = hist.get("series")
    curr_series = curr.get("series")

    if not isinstance(hist_x, list) and not isinstance(curr_x, list):
        return None
    if not isinstance(hist_series, list) and not isinstance(curr_series, list):
        return None

    x_values: list[str] = []
    for x_list in (hist_x, curr_x):
        if isinstance(x_list, list):
            for val in x_list:
                sval = str(val)
                if sval not in x_values:
                    x_values.append(sval)

    try:
        x_values = sorted(x_values, key=lambda v: int(v))
    except Exception:
        pass

    hist_map = {str(x): idx for idx, x in enumerate(hist_x or [])} if isinstance(hist_x, list) else {}
    curr_map = {str(x): idx for idx, x in enumerate(curr_x or [])} if isinstance(curr_x, list) else {}

    merged_by_name: dict[str, dict[str, Any]] = {}
    raw_names: set[str] = set()
    for series_list in (hist_series, curr_series):
        if not isinstance(series_list, list):
            continue
        for item in series_list:
            if isinstance(item, dict):
                raw_names.add(str(item.get("name", "Série")))

    def _canonical_series_name(name: str) -> str:
        # Caso comum: histórico vem como "AMS" e projeção como
        # "AMS - faturamento_bruto_yoy_pct". Para série contínua, deve virar
        # apenas "AMS" (mesma entidade ao longo do tempo).
        if " - " in name:
            prefix = name.split(" - ", 1)[0].strip()
            if prefix in raw_names:
                return prefix
        return name

    def _consume(series_list: Any, idx_map: dict[str, int]) -> None:
        if not isinstance(series_list, list):
            return
        for item in series_list:
            if not isinstance(item, dict):
                continue
            raw_name = str(item.get("name", "Série"))
            name = _canonical_series_name(raw_name)
            values = item.get("values")
            if not isinstance(values, list):
                continue
            target = merged_by_name.setdefault(name, {"name": name, "values": [None] * len(x_values)})
            out_values = target["values"]
            for year_str, x_idx in idx_map.items():
                global_idx = x_values.index(year_str) if year_str in x_values else -1
                if global_idx < 0 or x_idx >= len(values):
                    continue
                out_values[global_idx] = values[x_idx]

    _consume(hist_series, hist_map)
    _consume(curr_series, curr_map)

    unit = hist.get("unit") or curr.get("unit")
    return {
        "x": x_values,
        "series": list(merged_by_name.values()),
        "unit": unit,
    }


def _rebuild_combined_for_derived_metrics(
    combined: dict[str, Any],
    metrics: list[str],
    bus: list[str],
    sim_json: dict,
    historical_bundle: dict,
    hist_years: list[int] | None,
    proj_years: list[int] | None,
) -> dict[str, Any] | None:
    """Recalcula métricas derivadas sobre a série contínua combinada."""
    derived = [_parse_derived_metric(m) for m in metrics]
    if not derived or not any(d is not None for d in derived):
        return None
    if any(d is None for d in derived):
        # Mantém comportamento atual para payloads mistos (derivadas + absolutas).
        return None

    base_metrics = []
    for d in derived:
        if d is None:
            continue
        _, base_metric = d
        if base_metric not in base_metrics:
            base_metrics.append(base_metric)

    hist_base = _extract_data_from_historical(
        historical_bundle, base_metrics, bus, hist_years, "timeseries"
    )
    curr_base = _extract_data_from_sim(
        sim_json, base_metrics, bus, proj_years, "timeseries"
    )
    combined_base = _merge_timeseries_payloads(hist_base, curr_base)
    if not combined_base:
        return None

    x_vals = combined_base.get("x", [])
    base_series = combined_base.get("series", [])
    if not isinstance(x_vals, list) or not isinstance(base_series, list):
        return None

    rebuilt_series: list[dict[str, Any]] = []
    multi_bus = len(bus) > 1
    multi_metric = len(metrics) > 1

    for item in base_series:
        if not isinstance(item, dict):
            continue
        base_name = str(item.get("name", "Série"))
        values = item.get("values")
        if not isinstance(values, list):
            continue

        for metric in metrics:
            parsed = _parse_derived_metric(metric)
            if not parsed:
                continue
            kind, _ = parsed
            out_vals: list[float] = []
            for idx, cur in enumerate(values):
                cur_f = _safe_float(cur)
                prev_f = _safe_float(values[idx - 1]) if idx > 0 else None
                first_f = _safe_float(values[0]) if values else None
                if kind == "yoy_pct":
                    ratio = _pct_delta_ratio(prev_f, cur_f)
                    out_vals.append(0 if ratio is None else ratio)
                elif kind == "delta_pct":
                    ratio = _pct_delta_ratio(first_f, cur_f)
                    out_vals.append(0 if ratio is None else ratio)
                elif kind == "cagr":
                    ratio = _cagr_ratio(first_f, cur_f, idx)
                    out_vals.append(0 if ratio is None else ratio)
                else:
                    out_vals.append(0)

            if multi_bus and multi_metric:
                out_name = f"{base_name} - {metric}"
            else:
                out_name = base_name
            rebuilt_series.append({"name": out_name, "values": out_vals})

    return {
        "x": x_vals,
        "series": rebuilt_series,
        "unit": "%",
    }
