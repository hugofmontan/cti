from api.services.agent_output_normalizer import normalize_agent_response_dict
from api.schemas import AgentQueryResponse


def test_normalize_confidence_float_to_enum() -> None:
    raw = {
        "answer_markdown": "ok",
        "confidence": 0.95,
        "data_used": "a",
        "warnings": "w",
    }
    n = normalize_agent_response_dict(raw)
    v = AgentQueryResponse.model_validate({**n, "response_source": "openai", "intent": "x", "scenario_id": "s"})
    assert v.confidence == "high"
    assert v.data_used == ["a"]
    assert v.warnings == ["w"]


def test_normalize_lists_already_ok() -> None:
    raw = {
        "answer_markdown": "x",
        "confidence": "low",
        "data_used": ["d1"],
        "warnings": [],
        "artifacts": [],
    }
    n = normalize_agent_response_dict(raw)
    v = AgentQueryResponse.model_validate({**n, "response_source": "deterministic", "intent": "generic", "scenario_id": "1"})
    assert v.confidence == "low"
