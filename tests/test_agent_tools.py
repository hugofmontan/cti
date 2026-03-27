"""Tests for agent v2 tools (function calling)."""

from projecao_bus.orchestrator import resultado_para_json, run_simulation

from api.services.agent_tools import (
    deep_merge,
    execute_tool,
    _extract_data_from_sim,
    _build_validated_artifact,
    _linspace,
    _resolve_metric_value,
    _normalize_premissa_changes,
    _normalize_metric_list,
    _normalize_metric_name,
    _infer_premissa_changes_from_question,
    _broadcast_sensitivity_value,
    _merge_timeseries_payloads,
)
from api.services.agent_context_builder import compute_scenario_id


def _sim_json() -> dict:
    return resultado_para_json(run_simulation(premissas={}))


def _make_context(sim_json: dict | None = None) -> dict:
    sj = sim_json or _sim_json()
    return {
        "sim_json": sj,
        "historical_bundle": {},
        "premissas": sj.get("premissas_efetivas", {}),
        "scenario_id": compute_scenario_id(sj),
    }


def _historical_bundle_stub() -> dict:
    return {
        "historical_year_start": 2024,
        "historical_year_end": 2025,
        "consolidado": [
            {"ano": 2024, "ebitda": 100.0, "receita_liquida": 400.0},
            {"ano": 2025, "ebitda": 120.0, "receita_liquida": 480.0},
        ],
        "dre": {},
    }


def test_deep_merge_dot_notation() -> None:
    base = {"renovacao": {"churn": 0.15, "spread_real": 0.03}, "dcf": {"wacc": 0.12}}
    result = deep_merge(base, {"renovacao.churn": 0.25, "dcf.wacc": 0.16})
    assert result["renovacao"]["churn"] == 0.25
    assert result["renovacao"]["spread_real"] == 0.03
    assert result["dcf"]["wacc"] == 0.16


def test_deep_merge_preserves_unchanged() -> None:
    base = {"fopm": {"headcount_por_ano": {"2026": 100}}, "dcf": {"wacc": 0.12, "g": 0.035}}
    result = deep_merge(base, {"dcf.g": 0.05})
    assert result["fopm"]["headcount_por_ano"]["2026"] == 100
    assert result["dcf"]["wacc"] == 0.12
    assert result["dcf"]["g"] == 0.05


def test_linspace_basic() -> None:
    vals = _linspace(0.08, 0.16, 5)
    assert len(vals) == 5
    assert vals[0] == 0.08
    assert abs(vals[-1] - 0.16) < 1e-6


def test_tool_run_simulation() -> None:
    ctx = _make_context()
    result = execute_tool("run_simulation", {
        "premissa_changes": {"renovacao.churn": 0.25},
        "label": "churn_25pct",
    }, ctx)
    assert "scenario_id" in result
    assert result["label"] == "churn_25pct"
    assert "resumo_consolidado" in result
    assert "dcf" in result
    assert result["scenario_id"] in ctx.get("_scenario_cache", {})


def test_tool_compare_scenarios() -> None:
    ctx = _make_context()
    base_id = ctx["scenario_id"]

    sim_result = execute_tool("run_simulation", {
        "premissa_changes": {"renovacao.churn": 0.25},
        "label": "alt",
    }, ctx)
    alt_id = sim_result["scenario_id"]

    comparison = execute_tool("compare_scenarios", {
        "base_scenario_id": base_id,
        "alt_scenario_id": alt_id,
        "metrics": ["ebitda", "enterprise_value"],
        "granularity": "consolidado",
    }, ctx)

    assert "metrics" in comparison
    assert "ebitda" in comparison["metrics"]
    assert "enterprise_value" in comparison["metrics"]


def test_tool_query_data_timeseries() -> None:
    ctx = _make_context()
    result = execute_tool("query_data", {
        "source": "current",
        "metrics": ["ebitda"],
        "bus": ["consolidado"],
        "format": "timeseries",
    }, ctx)
    current = result.get("current", {})
    assert "x" in current
    assert "series" in current
    assert len(current["series"]) >= 1
    assert len(current["series"][0]["values"]) >= 1


def test_tool_query_data_timeseries_both_exposes_combined_full_series() -> None:
    ctx = _make_context()
    ctx["historical_bundle"] = _historical_bundle_stub()
    result = execute_tool("query_data", {
        "source": "both",
        "metrics": ["ebitda"],
        "bus": ["consolidado"],
        "format": "timeseries",
    }, ctx)
    assert "combined" in result
    combined = result["combined"]
    assert combined["x"][:2] == ["2024", "2025"]
    assert "2026" in combined["x"]
    assert "x" in result and "series" in result
    assert result["current"]["x"] == combined["x"]


def test_tool_query_data_timeseries_current_also_returns_combined() -> None:
    ctx = _make_context()
    ctx["historical_bundle"] = _historical_bundle_stub()
    result = execute_tool("query_data", {
        "source": "current",
        "metrics": ["ebitda"],
        "bus": ["consolidado"],
        "format": "timeseries",
    }, ctx)
    assert "combined" in result
    assert "2024" in result["combined"]["x"]
    assert "2026" in result["combined"]["x"]
    assert "historical" in result
    assert "current" in result
    assert result["current"]["x"] == result["combined"]["x"]


def test_merge_timeseries_collapses_metric_suffix_when_bare_name_exists() -> None:
    historical = {
        "x": ["2024", "2025"],
        "series": [
            {"name": "AMS", "values": [0.10, 0.12]},
            {"name": "FOPM", "values": [0.08, 0.09]},
        ],
    }
    projected = {
        "x": ["2026", "2027"],
        "series": [
            {"name": "AMS - faturamento_bruto_yoy_pct", "values": [0.14, 0.15]},
            {"name": "FOPM - faturamento_bruto_yoy_pct", "values": [0.09, 0.10]},
        ],
    }
    merged = _merge_timeseries_payloads(historical, projected)
    assert merged is not None
    assert merged["x"] == ["2024", "2025", "2026", "2027"]
    names = [s["name"] for s in merged["series"]]
    assert names == ["AMS", "FOPM"]
    ams_vals = merged["series"][0]["values"]
    fopm_vals = merged["series"][1]["values"]
    assert ams_vals == [0.10, 0.12, 0.14, 0.15]
    assert fopm_vals == [0.08, 0.09, 0.09, 0.10]


def test_tool_query_data_timeseries_yoy_uses_2025_as_base_for_2026_in_combined() -> None:
    ctx = _make_context()
    ctx["historical_bundle"] = {
        "historical_year_start": 2025,
        "historical_year_end": 2025,
        "consolidado": [
            {"ano": 2025, "faturamento_bruto": 100.0},
        ],
        "dre": {},
    }
    ctx["sim_json"]["consolidado"] = [
        {"ano": 2026, "faturamento_bruto": 110.0},
        {"ano": 2027, "faturamento_bruto": 121.0},
    ]
    result = execute_tool("query_data", {
        "source": "both",
        "metrics": ["faturamento_bruto_yoy_pct"],
        "bus": ["consolidado"],
        "format": "timeseries",
    }, ctx)
    series = result["series"][0]["values"]
    # 2025 (primeiro ponto) = 0; 2026 = +10% vs 2025; 2027 = +10% vs 2026
    assert abs(series[0] - 0.0) < 1e-12
    assert abs(series[1] - 0.10) < 1e-12
    assert abs(series[2] - 0.10) < 1e-12


def test_tool_query_data_snapshot() -> None:
    ctx = _make_context()
    result = execute_tool("query_data", {
        "source": "current",
        "metrics": ["enterprise_value"],
        "bus": ["consolidado"],
        "years": [2030],
        "format": "snapshot",
    }, ctx)
    current = result.get("current", {})
    assert "items" in current
    assert len(current["items"]) >= 1


def test_tool_query_data_decomposition() -> None:
    ctx = _make_context()
    result = execute_tool("query_data", {
        "source": "current",
        "metrics": ["ebitda"],
        "bus": ["fopm", "renovacao", "ams", "venda_sw", "data_science"],
        "years": [2030],
        "format": "decomposition",
    }, ctx)
    current = result.get("current", {})
    assert "categories" in current
    assert "values" in current
    assert len(current["categories"]) == 5


def test_extract_data_from_sim_decomposition_cagr_metric() -> None:
    sim_json = _sim_json()
    out = _extract_data_from_sim(
        sim_json,
        ["receita_liquida_cagr"],
        ["fopm", "renovacao", "ams", "venda_sw", "data_science"],
        [2026, 2030],
        "decomposition",
    )
    assert len(out["categories"]) == 5
    assert len(out["values"]) == 5
    assert all(isinstance(v, (int, float)) for v in out["values"])


def test_extract_data_from_sim_timeseries_delta_pct_metric() -> None:
    sim_json = _sim_json()
    out = _extract_data_from_sim(
        sim_json,
        ["receita_liquida_delta_pct"],
        ["consolidado"],
        [2026, 2027, 2028],
        "timeseries",
    )
    series = out["series"][0]["values"]
    assert len(series) == 3
    assert abs(series[0]) < 1e-12


def test_extract_data_from_sim_timeseries_yoy_pct_includes_metric_in_series_name_when_multiple_bu() -> None:
    sim_json = _sim_json()
    out = _extract_data_from_sim(
        sim_json,
        ["receita_liquida_yoy_pct"],
        ["fopm", "consolidado"],
        [2026, 2027],
        "timeseries",
    )
    names = [s["name"] for s in out["series"]]
    assert any("fopm" in n.lower() and "receita_liquida_yoy_pct" in n.lower() for n in names)


def test_broadcast_sensitivity_value_headcount_por_ano() -> None:
    out = _broadcast_sensitivity_value("data_science.headcount_por_ano", 50)
    assert isinstance(out, dict)
    assert all(isinstance(v, int) for v in out.values())


def test_broadcast_sensitivity_value_headcount_por_ano_interprets_small_scalar_as_delta_pct() -> None:
    # Se o scalar vier entre 0 e 1, tratamos como "delta percentual" do headcount base.
    out = _broadcast_sensitivity_value(
        "data_science.headcount_por_ano",
        0.05,
        premissas={"data_science": {"headcount_por_ano": {"2026": 100}}},
    )
    assert out["2026"] == 105


def test_tool_get_sensitivity_matrix_broadcasts_dict_drivers() -> None:
    ctx = _make_context()
    result = execute_tool(
        "get_sensitivity_matrix",
        {
            "row_param": "data_science.headcount_por_ano",
            "col_param": "data_science.ociosidade_por_ano",
            "row_range": {"min": 40, "max": 40, "steps": 1},
            "col_range": {"min": 0.2, "max": 0.2, "steps": 1},
            "target_metric": "enterprise_value",
        },
        ctx,
    )
    assert "matrix" in result
    assert isinstance(result["matrix"], list)
    assert result["matrix"][0][0] is not None


def test_tool_get_sensitivity_matrix_headcount_headers_show_effective_absolute_count() -> None:
    ctx = _make_context()
    # Força headcount base 2026 para 100 para validar o header efetivo.
    ctx["premissas"] = {
        **ctx["premissas"],
        "data_science": {
            **(ctx["premissas"].get("data_science", {}) if isinstance(ctx["premissas"], dict) else {}),
            "headcount_por_ano": {"2026": 100},
        },
    }

    result = execute_tool(
        "get_sensitivity_matrix",
        {
            "row_param": "data_science.headcount_por_ano",
            "col_param": "data_science.ociosidade_por_ano",
            "row_range": {"min": 0.05, "max": 0.05, "steps": 1},  # +5% -> 105 headcount
            "col_range": {"min": 0.2, "max": 0.2, "steps": 1},
            "target_metric": "enterprise_value",
        },
        ctx,
    )
    assert result["row_values"][0] == 105.0


def test_tool_get_sensitivity_matrix_centers_current_scenario_for_wacc_g() -> None:
    ctx = _make_context()
    base_wacc = float(ctx["premissas"]["dcf"]["wacc"])
    base_g = float(ctx["premissas"]["dcf"]["g"])

    result = execute_tool(
        "get_sensitivity_matrix",
        {
            "row_param": "dcf.wacc",
            "col_param": "dcf.g",
            "row_range": {"min": 0.09, "max": 0.16, "steps": 5},
            "col_range": {"min": 0.02, "max": 0.05, "steps": 5},
            "target_metric": "equity_value",
        },
        ctx,
    )

    row_values = result["row_values"]
    col_values = result["col_values"]
    assert len(row_values) % 2 == 1
    assert len(col_values) % 2 == 1
    assert abs(row_values[len(row_values) // 2] - base_wacc) < 1e-6
    assert abs(col_values[len(col_values) // 2] - base_g) < 1e-6


def test_tool_get_sensitivity_matrix_promotes_even_steps_to_keep_center() -> None:
    ctx = _make_context()
    base_wacc = float(ctx["premissas"]["dcf"]["wacc"])

    result = execute_tool(
        "get_sensitivity_matrix",
        {
            "row_param": "dcf.wacc",
            "col_param": "dcf.g",
            "row_range": {"min": 0.09, "max": 0.16, "steps": 4},
            "col_range": {"min": 0.02, "max": 0.05, "steps": 4},
            "target_metric": "equity_value",
        },
        ctx,
    )

    row_values = result["row_values"]
    assert len(row_values) == 5
    assert abs(row_values[len(row_values) // 2] - base_wacc) < 1e-6


def test_tool_build_artifact_chart() -> None:
    ctx = _make_context()
    result = execute_tool("build_artifact", {
        "artifact_type": "line",
        "title": "EBITDA Evolution",
        "data": {
            "x": ["2026", "2027", "2028"],
            "series": [{"name": "Consolidado", "values": [10, 20, 30]}],
            "unit": "BRL",
        },
    }, ctx)
    assert result["status"] == "artifact_created"
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "chart"
    assert artifacts[0]["chart_type"] == "line"


def test_tool_build_artifact_chart_skips_when_data_is_empty() -> None:
    ctx = _make_context()
    result = execute_tool("build_artifact", {
        "artifact_type": "line",
        "title": "CAGR por BU",
        "data": {
            "x": [],
            "series": [],
        },
    }, ctx)
    assert result["status"] == "artifact_skipped"
    assert result["reason"] == "insufficient_data_for_chart"
    assert len(ctx.get("_accumulated_artifacts", [])) == 0


def test_tool_build_artifact_does_not_split_mixed_units_by_default() -> None:
    ctx = _make_context()
    result = execute_tool("build_artifact", {
        "artifact_type": "line",
        "title": "Evolucao BU",
        "data": {
            "x": ["2026", "2027"],
            "series": [
                {"name": "FOPM - ebitda", "values": [100, 110]},
                {"name": "FOPM - margem_ebitda", "values": [0.3, 0.31]},
            ],
        },
    }, ctx)
    assert result["status"] == "artifact_created"
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1


def test_tool_build_artifact_kpi_panel() -> None:
    ctx = _make_context()
    execute_tool("build_artifact", {
        "artifact_type": "kpi_panel",
        "title": "Valuation",
        "data": {
            "items": [
                {"label": "EV", "value": "150M"},
                {"label": "Equity", "value": "120M"},
            ],
        },
    }, ctx)
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "kpi_panel"


def test_tool_build_artifact_table() -> None:
    ctx = _make_context()
    execute_tool("build_artifact", {
        "artifact_type": "table",
        "title": "DRE por BU",
        "data": {
            "columns": ["BU", "2026", "2030"],
            "rows": [["FOPM", 100, 200]],
        },
    }, ctx)
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "table"


def test_tool_build_artifact_heatmap() -> None:
    ctx = _make_context()
    execute_tool("build_artifact", {
        "artifact_type": "heatmap",
        "title": "Sensibilidade EV",
        "data": {
            "row_param": "wacc",
            "col_param": "g",
            "row_values": [0.08, 0.12, 0.16],
            "col_values": [0.02, 0.035, 0.05],
            "matrix": [[100, 120, 140], [80, 100, 120], [60, 80, 100]],
        },
    }, ctx)
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "sensitivity_matrix"


def test_tool_build_artifact_waterfall() -> None:
    ctx = _make_context()
    execute_tool("build_artifact", {
        "artifact_type": "waterfall",
        "title": "DRE Breakdown",
        "data": {
            "categories": ["Receita", "(-) Custos", "EBITDA"],
            "values": [100, -30, 70],
            "unit": "BRL",
        },
    }, ctx)
    artifacts = ctx.get("_accumulated_artifacts", [])
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "chart"
    assert artifacts[0]["chart_type"] == "waterfall"


def test_resolve_metric_value_derived_ratio_rule() -> None:
    row = {"ebitda": 50.0, "receita_liquida": 200.0}
    value = _resolve_metric_value(row, "margem_ebitda")
    assert value == 0.25


def test_resolve_metric_value_derived_sum_rule() -> None:
    row = {
        "gastos_pessoal": 80.0,
        "outras_desp_diretas": 15.0,
        "outras_desp_adm": 5.0,
    }
    value = _resolve_metric_value(row, "custos_totais")
    assert value == 100.0


def test_resolve_metric_value_headcount_alias() -> None:
    row = {"n_funcionarios": 17.0}
    assert _resolve_metric_value(row, "headcount") == 17.0


def test_normalize_metric_list_dedupes_headcount_aliases() -> None:
    metrics = _normalize_metric_list(["n_funcionarios", "headcount", "ebitda"])
    assert metrics == ["headcount", "ebitda"]


def test_normalize_metric_name_variacao_anual_percentual_alias() -> None:
    metric = _normalize_metric_name("variacao anual percentual receita liquida")
    assert metric == "receita_liquida_yoy_pct"


def test_unknown_tool_returns_error() -> None:
    ctx = _make_context()
    result = execute_tool("nonexistent_tool", {}, ctx)
    assert "error" in result


def test_normalize_premissa_changes_alias_and_percent() -> None:
    normalized = _normalize_premissa_changes({"wacc": 14, "g": 3.5})
    assert normalized["dcf.wacc"] == 0.14
    assert normalized["dcf.g"] == 0.035


def test_normalize_premissa_changes_uppercase_and_percent_string() -> None:
    normalized = _normalize_premissa_changes({"WACC": "14%", "G": "3,5%"})
    assert normalized["dcf.wacc"] == 0.14
    assert normalized["dcf.g"] == 0.035


def test_run_simulation_applies_wacc_change_from_alias() -> None:
    ctx = _make_context()
    base_wacc = float(ctx["sim_json"]["dcf"]["wacc"])
    result = execute_tool("run_simulation", {
        "premissa_changes": {"wacc": 14},
        "label": "wacc_14pct",
    }, ctx)
    scenario_id = result["scenario_id"]
    alt_wacc = float(ctx["_scenario_cache"][scenario_id]["sim_json"]["dcf"]["wacc"])
    assert abs(alt_wacc - 0.14) < 1e-9
    assert abs(base_wacc - alt_wacc) > 1e-9


def test_run_simulation_accepts_flat_args_without_premissa_changes() -> None:
    ctx = _make_context()
    result = execute_tool("run_simulation", {
        "wacc": 14,
        "label": "wacc_flat",
    }, ctx)
    scenario_id = result["scenario_id"]
    alt_wacc = float(ctx["_scenario_cache"][scenario_id]["sim_json"]["dcf"]["wacc"])
    assert abs(alt_wacc - 0.14) < 1e-9


def test_run_simulation_without_changes_returns_error() -> None:
    ctx = _make_context()
    result = execute_tool("run_simulation", {"label": "sem_mudancas"}, ctx)
    assert "error" in result


def test_infer_premissa_changes_from_question_half_ams_conversion() -> None:
    inferred = _infer_premissa_changes_from_question(
        "E se a taxa de conversão na AMS cair pela metade?",
        {"ams": {"taxa_conversao_fopm": 0.2}},
    )
    assert inferred["ams.taxa_conversao_fopm"] == 0.1


def test_infer_premissa_changes_from_question_hiring_fopm() -> None:
    inferred = _infer_premissa_changes_from_question(
        "E se eu contratar mais 5 pessoas na FOPM em 2027?",
        {"fopm": {"headcount_por_ano": {"2027": 54}}},
    )
    assert inferred["fopm.headcount_por_ano.2027"] == 59


def test_run_simulation_infers_changes_from_question_when_missing_payload() -> None:
    ctx = _make_context()
    ctx["question"] = "E se a taxa de conversão na AMS cair pela metade?"
    # Garante base conhecida para validar halving.
    ctx["premissas"] = {**ctx["premissas"], "ams": {"taxa_conversao_fopm": 0.2}}
    result = execute_tool("run_simulation", {"label": "auto_half"}, ctx)
    assert "scenario_id" in result


def test_run_simulation_infers_fopm_headcount_hiring_when_missing_payload() -> None:
    ctx = _make_context()
    ctx["question"] = "E se eu contratar mais 5 pessoas na FOPM em 2027?"
    ctx["premissas"] = {
        **ctx["premissas"],
        "fopm": {
            **(ctx["premissas"].get("fopm", {}) if isinstance(ctx["premissas"], dict) else {}),
            "headcount_por_ano": {"2027": 54},
        },
    }
    result = execute_tool("run_simulation", {"label": "auto_fopm_hiring"}, ctx)
    assert "scenario_id" in result
