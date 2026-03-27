"""
Agent v2 — Orquestrador.

Pipeline simplificado em 5 passos:
  1. Rodar simulação com premissas atuais + carregar histórico
  2. Montar contexto compacto
  3. Chamar LLM com tools (loop automático)
  4. Coletar artifacts das tool calls
  5. Validar e retornar
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
import unicodedata
from typing import Any

from api.config import get_settings
from api.schemas import AgentQueryResponse
from projecao_bus.historical_dre import load_historical_dre_bundle
from projecao_bus.orchestrator import resultado_para_json, run_simulation

from .agent_context_builder import build_agent_context, compute_scenario_id
from .agent_tools import AGENT_TOOLS, execute_tool
from .projection_config import get_projection_years
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


def _trace(request_id: str, stage: str, **fields: Any) -> None:
    payload = {"request_id": request_id, "stage": stage, **fields}
    print("[agent-trace]", payload)


def _normalize_text(value: Any) -> str:
    txt = str(value or "").lower()
    return "".join(ch for ch in unicodedata.normalize("NFKD", txt) if not unicodedata.combining(ch))


def _is_data_science_stress_question(question: str) -> bool:
    q = _normalize_text(question)
    has_stress = any(tok in q for tok in ("estresse", "sensibilidade", "stress"))
    has_ds = ("data science" in q) or ("data_science" in q)
    has_drivers = ("headcount" in q) or ("ociosidade" in q) or ("premissa" in q)
    return has_stress and has_ds and has_drivers


def _is_aggressive_stress_question(question: str) -> bool:
    q = _normalize_text(question)
    return any(tok in q for tok in ("agressiv", "bastante", "forte", "maximo", "delta de crescimento"))


def _is_objective_text_only_question(question: str) -> bool:
    """Heurística para perguntas objetivas que devem vir em texto puro."""
    q = _normalize_text(question)
    if not q:
        return False
    visual_tokens = (
        "tabela", "grafico", "gráfico", "chart", "plot", "heatmap", "painel", "kpi", "artifact", "artefato",
        "mostre em", "visual", "matriz",
    )
    if any(tok in q for tok in visual_tokens):
        return False
    objective_tokens = (
        "qual o efeito", "qual e o efeito", "quais seriam os efeitos", "quanto", "impacto", "se eu", "e se",
    )
    return (any(tok in q for tok in objective_tokens) and len(q) <= 260)


def _wants_chart(question: str) -> bool:
    q = _normalize_text(question)
    return any(tok in q for tok in ("grafico", "chart", "plot", "visual"))



def _is_chart_artifact(artifact: dict[str, Any]) -> bool:
    t = str(artifact.get("type", "")).lower()
    return t in {"line", "bar", "stacked_bar", "grouped_bar", "waterfall", "heatmap", "sankey", "sensitivity_matrix"}


def _is_empty_chart_artifact(artifact: dict[str, Any]) -> bool:
    if not _is_chart_artifact(artifact):
        return False
    t = str(artifact.get("type", "")).lower()
    if t in {"heatmap", "sensitivity_matrix"}:
        matrix = artifact.get("matrix", [])
        return not (isinstance(matrix, list) and len(matrix) > 0)
    if t == "sankey":
        nodes = artifact.get("nodes", [])
        links = artifact.get("links", [])
        return not (isinstance(nodes, list) and nodes and isinstance(links, list) and links)
    x = artifact.get("x", [])
    series = artifact.get("series", [])
    return not (isinstance(x, list) and x and isinstance(series, list) and series)


def _ensure_chart_artifact_if_requested(question: str, context: dict[str, Any]) -> None:
    if not _wants_chart(question):
        return
    artifacts = context.get("_accumulated_artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
        context["_accumulated_artifacts"] = artifacts

    # Remove gráficos vazios que podem aparecer por payload parcial do LLM.
    cleaned: list[dict[str, Any]] = []
    for art in artifacts:
        if not isinstance(art, dict):
            continue
        if _is_empty_chart_artifact(art):
            continue
        cleaned.append(art)
    context["_accumulated_artifacts"] = cleaned

    has_chart = any(isinstance(a, dict) and _is_chart_artifact(a) for a in cleaned)
    if has_chart:
        return

    sens = context.get("_last_sensitivity_result")
    if isinstance(sens, dict) and isinstance(sens.get("matrix"), list) and len(sens.get("matrix", [])) > 0:
        execute_tool(
            "build_artifact",
            {
                "artifact_type": "heatmap",
                "title": "Sensibilidade",
                "data": sens,
            },
            context,
        )



def _sanitize_text_only_answer(answer_markdown: str) -> str:
    text = answer_markdown or ""
    # Remove frases que prometem visual quando resposta deve ser textual.
    for token in ("Tabela abaixo.", "Tabela abaixo", "Gráfico abaixo.", "Grafico abaixo.", "Gráfico abaixo", "Grafico abaixo"):
        text = text.replace(token, "")
    return " ".join(text.split()).strip()





def _run_data_science_stress_deterministic(question: str, context: dict[str, Any]) -> AgentQueryResponse:
    aggressive = _is_aggressive_stress_question(question)
    lo, hi, steps = (0.7, 1.3, 7) if aggressive else (0.8, 1.2, 5)

    # Usa base do primeiro ano de projeção para criar ranges dinâmicos.
    py = get_projection_years()
    base_year = str(py[0]) if py else "2026"
    ds = context.get("premissas", {}).get("data_science", {}) if isinstance(context.get("premissas"), dict) else {}
    base_hc = ds.get("headcount_por_ano", {}).get(base_year) if isinstance(ds.get("headcount_por_ano"), dict) else 5
    base_oc = ds.get("ociosidade_por_ano", {}).get(base_year) if isinstance(ds.get("ociosidade_por_ano"), dict) else 0.15
    try:
        base_hc_f = float(base_hc)
    except Exception:
        base_hc_f = 5.0
    try:
        base_oc_f = float(base_oc)
    except Exception:
        base_oc_f = 0.15

    sens = execute_tool(
        "get_sensitivity_matrix",
        {
            "row_param": "data_science.ociosidade_por_ano",
            "col_param": "data_science.headcount_por_ano",
            "row_range": {"min": max(0.0, base_oc_f * lo), "max": min(1.0, base_oc_f * hi), "steps": steps},
            "col_range": {"min": max(1.0, base_hc_f * lo), "max": max(1.0, base_hc_f * hi), "steps": steps},
            "target_metric": "equity_value",
        },
        context,
    )

    execute_tool(
        "build_artifact",
        {
            "artifact_type": "heatmap",
            "title": "Sensibilidade de Equity Value - Data Science (ociosidade x headcount)",
            "data": sens,
        },
        context,
    )

    matrix = sens.get("matrix", []) if isinstance(sens, dict) else []
    values: list[float] = []
    for row in matrix if isinstance(matrix, list) else []:
        if isinstance(row, list):
            for v in row:
                if isinstance(v, (int, float)):
                    values.append(float(v))
    if values:
        min_v, max_v = min(values), max(values)
        answer = (
            f"Estresse de Data Science executado de forma deterministica com variacao "
            f"{int((lo-1)*100)}% a +{int((hi-1)*100)}% sobre a base atual. "
            f"O equity value varia de R$ {min_v/1e6:.1f} mi a R$ {max_v/1e6:.1f} mi."
        )
    else:
        answer = "Estresse de Data Science executado com matriz de sensibilidade."

    return AgentQueryResponse(
        answer_markdown=answer,
        artifacts=context.get("_accumulated_artifacts", []),
        confidence="high",
        data_used=["simulacao_atual", "premissas_efetivas", "get_sensitivity_matrix"],
        warnings=[],
        response_source="deterministic",
        intent="tool_based",
        scenario_id=context.get("scenario_id", ""),
        tools_executed=context.get("_tools_executed", []),
    )


async def run_agent_query(
    question: str,
    premissas: dict[str, Any] | None,
    history: list[dict[str, str]] | None = None,
    dissertative_mode: bool = False,
) -> AgentQueryResponse:
    """Pipeline principal do agente v2."""
    request_id = uuid.uuid4().hex[:10]
    history = history or []
    t_start = time.perf_counter()

    _trace(
        request_id, "start",
        question_preview=question[:120],
        has_premissas=bool(premissas),
        history_items=len(history),
    )

    # === Passo 1: Simulação atual + histórico (paralelo) ===
    t_sim = time.perf_counter()
    sim_future = asyncio.to_thread(run_simulation, premissas=premissas)
    hist_future = asyncio.to_thread(load_historical_dre_bundle)

    try:
        sim, historical_bundle = await asyncio.gather(sim_future, hist_future)
    except Exception as e:
        logger.error("Erro na simulação/histórico: %s", e)
        sim = run_simulation(premissas=premissas)
        historical_bundle = None

    sim_json = resultado_para_json(sim)
    scenario_id = compute_scenario_id(sim_json)
    _trace(request_id, "sim_done", duration_ms=round((time.perf_counter() - t_sim) * 1000, 1))

    # === Passo 2: Montar contexto ===
    context = build_agent_context(
        sim_json=sim_json,
        historical_bundle=historical_bundle,
        premissas=premissas or sim_json.get("premissas_efetivas", {}),
        history=history,
        scenario_id=scenario_id,
    )
    context["question"] = question

    # Caminho determinístico para "estresse de Data Science":
    # evita dependência do LLM para montar tabela detalhada corretamente.
    if _is_data_science_stress_question(question):
        _trace(request_id, "deterministic_ds_stress")
        response = _run_data_science_stress_deterministic(question, context)
        total_ms = round((time.perf_counter() - t_start) * 1000, 1)
        _trace(
            request_id, "end",
            total_ms=total_ms,
            confidence=response.confidence,
            artifacts=len(response.artifacts),
            tools_executed=response.tools_executed,
        )
        return response

    # === Passo 3: Chamar LLM com tools ===
    settings = get_settings()
    client = OpenAIClient(settings)
    _trace(request_id, "openai_status", **client.status())

    if not client.is_enabled():
        _trace(request_id, "llm_unavailable")
        return _fallback_response("O agente IA está temporariamente indisponível. Verifique a chave OpenAI.", scenario_id)

    try:
        t_llm = time.perf_counter()
        llm_result = await client.generate_with_tools(
            question=question,
            context=context,
            tools=AGENT_TOOLS,
            tool_executor=lambda name, args: execute_tool(name, args, context),
            dissertative_mode=dissertative_mode,
        )
        _trace(
            request_id, "llm_done",
            duration_ms=round((time.perf_counter() - t_llm) * 1000, 1),
            tools_executed=context.get("_tools_executed", []),
        )
    except Exception as e:
        logger.error("Erro no LLM: %s", e)
        _trace(request_id, "llm_error", error=str(e)[:200])
        return _fallback_response(
            f"Erro ao processar sua pergunta: {str(e)[:100]}. Tente reformular.",
            scenario_id,
        )

    # === Passo 4: Coletar artifacts das tools ===
    current_artifacts = context.get("_accumulated_artifacts", [])
    has_explicit_artifacts = isinstance(current_artifacts, list) and any(isinstance(a, dict) for a in current_artifacts)
    text_only = _is_objective_text_only_question(question) and not has_explicit_artifacts
    if text_only:
        context["_accumulated_artifacts"] = []
        llm_result["answer_markdown"] = _sanitize_text_only_answer(llm_result.get("answer_markdown", ""))
    else:
        _ensure_chart_artifact_if_requested(question, context)
    accumulated_artifacts = context.get("_accumulated_artifacts", [])
    tools_executed = context.get("_tools_executed", [])

    # === Passo 5: Validar e construir resposta ===
    try:
        response = AgentQueryResponse(
            answer_markdown=llm_result.get("answer_markdown", ""),
            artifacts=accumulated_artifacts,
            confidence=llm_result.get("confidence", "medium"),
            data_used=llm_result.get("data_used", []),
            warnings=llm_result.get("warnings", []),
            response_source="openai",
            intent="tool_based",
            scenario_id=scenario_id,
            tools_executed=tools_executed,
        )
    except Exception as e:
        logger.error("Erro na validação Pydantic: %s", e)
        response = AgentQueryResponse(
            answer_markdown=llm_result.get("answer_markdown", "Erro ao processar resposta."),
            artifacts=[],
            confidence="low",
            data_used=[],
            warnings=[f"Erro de validação: {str(e)}"],
            response_source="fallback",
            intent="tool_based",
            scenario_id=scenario_id,
            tools_executed=tools_executed,
        )

    total_ms = round((time.perf_counter() - t_start) * 1000, 1)
    _trace(
        request_id, "end",
        total_ms=total_ms,
        confidence=response.confidence,
        artifacts=len(response.artifacts),
        tools_executed=tools_executed,
    )
    print(
        "[agent-debug] response_source",
        {"source": response.response_source, "confidence": response.confidence, "artifacts": len(response.artifacts)},
    )

    return response


def _fallback_response(message: str, scenario_id: str) -> AgentQueryResponse:
    return AgentQueryResponse(
        answer_markdown=message,
        artifacts=[],
        confidence="low",
        data_used=[],
        warnings=["Falha no processamento"],
        response_source="fallback",
        intent="error",
        scenario_id=scenario_id,
    )
