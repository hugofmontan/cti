from api.services.agent_intent import Intent, route_question


def test_route_impact_margin() -> None:
    r = route_question("Quais BUs tiveram maior impacto na margem EBITDA consolidada?")
    assert r.intent == Intent.IMPACT_MARGIN_CONSOLIDATED


def test_route_impact_margin_negative_flag() -> None:
    r = route_question("Quais BUs impactaram negativamente a margem EBITDA consolidada?")
    assert r.intent == Intent.IMPACT_MARGIN_CONSOLIDATED
    assert r.entities.get("impact_direction") == "negative"


def test_route_bu_specific_impact_goes_generic() -> None:
    r = route_question("Explique o que mais impactou negativamente a margem EBITDA de FOPM")
    assert r.intent == Intent.GENERIC


def test_route_fopm_2025_historical() -> None:
    r = route_question("qual foi a receita de FOPM em 2025")
    assert r.intent == Intent.HISTORICAL_BU_METRIC


def test_route_projection_fopm_2026() -> None:
    r = route_question("receita fopm 2026")
    assert r.intent == Intent.PROJECTION_BU_METRIC_YEAR
