from pydantic import BaseModel


class SimulatePayload(BaseModel):
    premissas: dict | None = None
