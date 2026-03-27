"""
Matriz WACC × g e cenários Bear / Base / Bull.
"""

from __future__ import annotations

import pandas as pd

from ..base_values import default_base_values


def equity_value(
    wacc: float,
    g: float,
    fcffs: list[float] | tuple[float, ...],
    caixa: float | None = None,
) -> float:
    """
    FCFFs em ordem cronológica; fator t = 1/(1+wacc)^t para t=1..N.
    VT usa FCFF do último ano e é descontado pelo fator do período N.
    """
    if len(fcffs) < 1:
        raise ValueError("Esperado ao menos 1 FCFF para calcular equity value.")
    if wacc <= g:
        raise ValueError("WACC deve ser maior que g.")
    fatores = [1.0 / (1.0 + wacc) ** t for t in range(1, len(fcffs) + 1)]
    soma_vp = sum(f * fc for f, fc in zip(fatores, fcffs))
    vt = (fcffs[-1] * (1.0 + g)) / (wacc - g)
    vp_vt = vt * fatores[-1]
    if caixa is None:
        caixa = default_base_values().caixa_base
    return soma_vp + vp_vt + caixa


def matriz_wacc_g(
    fcffs: list[float] | tuple[float, ...],
    waccs: list[float] | None = None,
    gs: list[float] | None = None,
    caixa: float | None = None,
) -> pd.DataFrame:
    if waccs is None:
        waccs = [0.1112, 0.1312, 0.1512, 0.1712, 0.1912, 0.2112, 0.2312]
    if gs is None:
        gs = [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]

    dados: list[list[float]] = []
    for w in waccs:
        linha = []
        for g in gs:
            if w <= g:
                linha.append(float("nan"))
            else:
                try:
                    linha.append(equity_value(w, g, fcffs, caixa=caixa))
                except ZeroDivisionError:
                    linha.append(float("nan"))
        dados.append(linha)
    return pd.DataFrame(dados, index=[f"{w:.4f}" for w in waccs], columns=[f"{g:.3f}" for g in gs])


def cenarios_gabarito(
    fcffs: list[float] | tuple[float, ...],
    caixa: float | None = None,
) -> pd.DataFrame:
    """Bear 21,12% / 2%; Base 17,12% / 3,5%; Bull 13,12% / 5%."""
    cenarios = [
        ("Bear", 0.2112, 0.02),
        ("Base", 0.1712, 0.035),
        ("Bull", 0.1312, 0.05),
    ]
    linhas = []
    for nome, w, g in cenarios:
        ev = equity_value(w, g, fcffs, caixa=caixa)
        linhas.append({"cenario": nome, "wacc": w, "g": g, "equity_value": ev})
    return pd.DataFrame(linhas)
