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
    locale: str = Field(default="pt-BR", min_length=2, max_length=16)

    @field_validator("question")
    @classmethod
    def _question_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question nao pode ser vazia")
        return stripped


class ArtifactTable(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: list[str]
    rows: list[list[str | int | float | None]]
    formats: dict[str, str] = Field(default_factory=dict)


class ArtifactChartSeries(BaseModel):
    name: str
    values: list[float | int]


class ArtifactChart(BaseModel):
    type: Literal["chart"] = "chart"
    title: str
    chart_type: Literal["line", "bar"]
    x: list[str | int]
    series: list[ArtifactChartSeries]
    unit: str | None = None


class ArtifactKPI(BaseModel):
    type: Literal["kpi"] = "kpi"
    title: str
    value: str
    subtitle: str | None = None


AgentArtifact = ArtifactTable | ArtifactChart | ArtifactKPI


class AgentQueryResponse(BaseModel):
    answer_markdown: str
    artifacts: list[AgentArtifact] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    data_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    response_source: Literal["openai", "deterministic", "fallback"] = "fallback"
    intent: str | None = None
    scenario_id: str | None = None
    validation_repaired: bool = False
