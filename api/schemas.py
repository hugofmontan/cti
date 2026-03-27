from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SimulatePayload(BaseModel):
    premissas: dict[str, Any] | None = None


class AgentMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Origem da mensagem no histórico.")
    content: str = Field(min_length=1, max_length=3000)


class AgentQueryPayload(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    premissas: dict[str, Any] | None = None
    history: list[AgentMessage] = Field(default_factory=list, max_length=20)
    session_memory: dict[str, Any] | None = None
    locale: str = Field(default="pt-BR", min_length=2, max_length=16)
    dissertative_mode: bool = False

    @field_validator("question")
    @classmethod
    def _question_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question nao pode ser vazia")
        return stripped


# === Artifact schemas (frontend depende deles — manter compatíveis) ===

class ArtifactTable(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: list[str]
    rows: list[list[str | int | float | None]]
    formats: dict[str, str] = Field(default_factory=dict)


class ArtifactChartSeries(BaseModel):
    name: str
    values: list[float | int | None]


class ArtifactChart(BaseModel):
    type: Literal["chart"] = "chart"
    title: str
    chart_type: Literal["line", "bar", "waterfall", "stacked_bar", "grouped_bar", "horizontal_bar"]
    x: list[str | int]
    series: list[ArtifactChartSeries]
    unit: str | None = None
    reference_line: dict[str, Any] | None = None


class ArtifactKPI(BaseModel):
    type: Literal["kpi"] = "kpi"
    title: str
    value: str
    subtitle: str | None = None


class ArtifactKPIPanelItem(BaseModel):
    label: str
    value: str | float | int
    delta: str | None = None
    sentiment: Literal["positive", "negative", "neutral"] | None = None


class ArtifactKPIPanel(BaseModel):
    type: Literal["kpi_panel"] = "kpi_panel"
    title: str
    items: list[ArtifactKPI | ArtifactKPIPanelItem]
    highlight_index: int | None = None


class ArtifactScenarioResult(BaseModel):
    label: str
    scenario_id: str | None = None
    premise_deltas: dict[str, Any] = Field(default_factory=dict)
    key_metrics: dict[str, float | str] = Field(default_factory=dict)
    delta_vs_base: dict[str, float | str] = Field(default_factory=dict)


class ArtifactScenarioComparison(BaseModel):
    type: Literal["scenario_comparison"] = "scenario_comparison"
    title: str
    base_label: str = ""
    scenarios: list[ArtifactScenarioResult] = Field(default_factory=list)


class ArtifactSensitivityMatrix(BaseModel):
    type: Literal["sensitivity_matrix"] = "sensitivity_matrix"
    title: str
    row_param: str = ""
    col_param: str = ""
    row_values: list[float] = Field(default_factory=list)
    col_values: list[float] = Field(default_factory=list)
    matrix: list[list[float]] = Field(default_factory=list)
    highlight: dict[str, Any] | None = None


class ArtifactSankeyNode(BaseModel):
    id: str
    label: str
    color: str | None = None


class ArtifactSankeyLink(BaseModel):
    source: str
    target: str
    value: float
    label: str | None = None


class ArtifactSankey(BaseModel):
    type: Literal["sankey"] = "sankey"
    title: str
    nodes: list[ArtifactSankeyNode] = Field(default_factory=list)
    links: list[ArtifactSankeyLink] = Field(default_factory=list)
    unit: str | None = "BRL"
    year: int | str | None = None
    bu: str | None = None


AgentArtifact = (
    ArtifactTable
    | ArtifactChart
    | ArtifactKPI
    | ArtifactKPIPanel
    | ArtifactScenarioComparison
    | ArtifactSensitivityMatrix
    | ArtifactSankey
)


# === Request / Response ===

class AgentQueryResponse(BaseModel):
    answer_markdown: str
    artifacts: list[dict] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    data_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    response_source: Literal["openai", "deterministic", "fallback"] = "fallback"
    intent: str | None = None
    scenario_id: str | None = None
    tools_executed: list[str] = Field(default_factory=list)
