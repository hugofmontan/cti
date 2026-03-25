from __future__ import annotations

from typing import Any

from api.config import get_settings
from api.schemas import AgentQueryResponse
from projecao_bus.historical_dre import load_historical_dre_bundle
from projecao_bus.orchestrator import resultado_para_json, run_simulation

from .agent_context import build_agent_context, compute_scenario_id
from .agent_deterministic import execute_deterministic
from .agent_intent import route_question
from .agent_output_normalizer import normalize_agent_response_dict
from .openai_client import OpenAIClient


def _wants_visual(question: str) -> bool:
    q = question.lower()
    return any(token in q for token in ["grafico", "gráfico", "plot", "tabela", "visual"])


def _local_generic_fallback(question: str, scenario_id: str, routed_intent: str) -> AgentQueryResponse:
    return AgentQueryResponse(
        answer_markdown=(
            "Não consegui mapear para uma análise automática com dados do modelo. "
            "Tente reformular com: **métrica** (EBITDA, receita, margem), **BU ou consolidado** e ** período (2026–2030)**. "
            "Para **histórico** (2018–2025), peça explicitamente o ano e a BU."
        ),
        confidence="medium",
        warnings=["Resposta genérica: nenhuma intenção determinística ou LLM válida."],
        response_source="fallback",
        intent=routed_intent,
        scenario_id=scenario_id,
    )


def run_agent_query(question: str, premissas: dict[str, Any] | None, history: list[dict[str, str]]) -> AgentQueryResponse:
    print("[agent-debug] run_agent_query_start", {"question": question[:180], "has_premissas": bool(premissas)})
    sim = run_simulation(premissas=premissas)
    sim_json = resultado_para_json(sim)
    scenario_id = compute_scenario_id(sim_json)

    routed = route_question(question)
    wants_visual = _wants_visual(question)

    try:
        historical_bundle = load_historical_dre_bundle()
    except Exception:
        historical_bundle = None

    det = execute_deterministic(
        routed,
        question,
        sim_json,
        historical_bundle,
        scenario_id,
        wants_visual,
    )
    if det is not None:
        print(
            "[agent-debug] response_source",
            {"source": "deterministic", "intent": det.intent, "artifacts": len(det.artifacts)},
        )
        return det

    context = build_agent_context(sim_json, question=question, history=history, router_intent=routed.intent.value)

    settings = get_settings()
    client = OpenAIClient(settings)
    print("[agent-debug] openai_status", client.status())

    if client.is_enabled():
        try:
            llm_raw = client.generate_structured(prompt=question, context=context)
            normalized = normalize_agent_response_dict(llm_raw if isinstance(llm_raw, dict) else {})
            validated = AgentQueryResponse.model_validate(
                {**normalized, "response_source": "openai", "intent": routed.intent.value, "scenario_id": scenario_id}
            )
            print(
                "[agent-debug] response_source",
                {"source": "openai", "confidence": validated.confidence, "artifacts": len(validated.artifacts)},
            )
            return validated
        except Exception as exc:
            print("[agent-debug] openai_error_fallback", {"error": str(exc)})

    out = _local_generic_fallback(question, scenario_id, routed.intent.value)
    print(
        "[agent-debug] response_source",
        {"source": "fallback", "confidence": out.confidence, "artifacts": 0},
    )
    return out
