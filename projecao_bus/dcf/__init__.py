"""DCF: BP → NCGL → Fluxo → WACC → Equity Value e sensibilidade."""

__all__ = ["run_dcf_pipeline"]


def __getattr__(name: str):
    if name == "run_dcf_pipeline":
        from .pipeline import run_dcf_pipeline

        return run_dcf_pipeline
    raise AttributeError(name)
