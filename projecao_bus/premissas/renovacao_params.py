"""Parâmetros de negócio da BU Renovação."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenovacaoProjectionParams:
    fb_renovacao_2025: float
    custo_func_renovacao_2025: float
    n_func_renovacao: int
    spread_reajuste_default: float
    ratio_rem_mc1_renovacao: float
    ratio_outras_adm_pct_rl_renovacao: float
    honorarios_janela_inicial: tuple[float, ...]
    custo_func_grau_livre_adicional: float


def default_renovacao_projection_params() -> RenovacaoProjectionParams:
    return RenovacaoProjectionParams(
        fb_renovacao_2025=3_385_238.39,
        custo_func_renovacao_2025=305_489.82 / 3.0,
        n_func_renovacao=3,
        spread_reajuste_default=0.02,
        ratio_rem_mc1_renovacao=0.065,
        ratio_outras_adm_pct_rl_renovacao=(
            (20_175.45 / 1_712_222.97 + 20_606.90 / 1_991_988.59 + 16_131.42 / 2_777_019.53) / 3.0
        ),
        honorarios_janela_inicial=(64_500.0, 66_000.0, 66_000.0),
        custo_func_grau_livre_adicional=0.01,
    )
