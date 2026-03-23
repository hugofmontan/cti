"""
Valor presente dos FCFFs, valor terminal e Equity Value.
"""

from __future__ import annotations

import pandas as pd

from .constants import ANOS_PROJECAO, CAIXA_BASE_2025, DIVIDA_LIQUIDA, G_PERPETUIDADE, WACC_FIXO


def valor_presente_fcffs(
    fcffs_por_ano: dict[int, float] | pd.Series,
    wacc: float = WACC_FIXO,
    anos: tuple[int, ...] = ANOS_PROJECAO,
) -> tuple[dict[int, float], float]:
    """
    Fator ano t: 1 / (1+WACC)^(i+1), i = 0..4 para 2026..2030.
    """
    vp: dict[int, float] = {}
    soma = 0.0
    for i, ano in enumerate(anos):
        fcff = float(fcffs_por_ano[ano])
        fator = 1.0 / (1.0 + wacc) ** (i + 1)
        v = fcff * fator
        vp[ano] = v
        soma += v
    return vp, soma


def valor_terminal_gordon(fcff_terminal_ano: float, wacc: float, g: float) -> float:
    return fcff_terminal_ano / (wacc - g)


def enterprise_value(
    soma_vp_fcffs: float,
    fcff_ultimo_ano: float,
    wacc: float,
    g: float,
    ano_ultimo: int = 2030,
) -> tuple[float, float, float, float]:
    """
    FCFF_terminal = FCFF_ultimo * (1+g)
    VP_VT = VT * fator do último ano (5 períodos).
    """
    anos = list(ANOS_PROJECAO)
    idx_ult = anos.index(ano_ultimo)
    fator_ult = 1.0 / (1.0 + wacc) ** (idx_ult + 1)

    fcff_term = fcff_ultimo_ano * (1.0 + g)
    vt = valor_terminal_gordon(fcff_term, wacc, g)
    vp_vt = vt * fator_ult
    ev = soma_vp_fcffs + vp_vt
    return ev, fcff_term, vt, vp_vt


def equity_value_bridge(ev: float, caixa_2025: float = CAIXA_BASE_2025, divida: float = DIVIDA_LIQUIDA) -> float:
    return ev + caixa_2025 - divida


def multiplos_implicitos(
    ev: float,
    ebitda_2026: float,
    rl_2026: float,
    ll_2026: float,
    fcff_2026: float,
) -> dict[str, float]:
    return {
        "EV_EBITDA_2026": ev / ebitda_2026 if ebitda_2026 else float("nan"),
        "EV_RL_2026": ev / rl_2026 if rl_2026 else float("nan"),
        "P_E_2026": ev / ll_2026 if ll_2026 else float("nan"),
        "FCFF_Yield_2026": fcff_2026 / ev if ev else float("nan"),
    }


def montar_tabela_dcf(
    df_fluxo: pd.DataFrame,
    df_consolidado: pd.DataFrame,
    wacc: float = WACC_FIXO,
    g: float = G_PERPETUIDADE,
) -> dict:
    fcffs = df_fluxo.set_index("ano")["fcff"]
    dct = fcffs.to_dict()
    vp_por_ano, soma_vp = valor_presente_fcffs(dct, wacc=wacc)

    ult = 2030
    fcff_ult = float(fcffs.loc[ult])
    ev, fcff_term, vt, vp_vt = enterprise_value(soma_vp, fcff_ult, wacc, g, ano_ultimo=ult)
    eqv = equity_value_bridge(ev)

    cons = df_consolidado.set_index("ano")
    ebitda26 = float(cons.at[2026, "ebitda"])
    rl26 = float(cons.at[2026, "receita_liquida"])
    ll26 = float(cons.at[2026, "lucro_liquido"])
    fcff26 = float(fcffs.loc[2026])

    mult = multiplos_implicitos(ev, ebitda26, rl26, ll26, fcff26)

    return {
        "wacc": wacc,
        "g": g,
        "vp_fcff_por_ano": vp_por_ano,
        "soma_vp_fcffs": soma_vp,
        "fcff_terminal": fcff_ult * (1.0 + g),
        "valor_terminal": vt,
        "vp_valor_terminal": vp_vt,
        "enterprise_value": ev,
        "equity_value": eqv,
        "multiplos": mult,
    }
