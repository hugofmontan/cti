"""
Valor presente dos FCFFs, valor terminal e Equity Value.
"""

from __future__ import annotations

import pandas as pd

from .constants import DIVIDA_LIQUIDA, G_PERPETUIDADE, WACC_FIXO
from ..context import SimulationContext


def valor_presente_fcffs(
    fcffs_por_ano: dict[int, float] | pd.Series,
    wacc: float = WACC_FIXO,
    anos: tuple[int, ...] | None = None,
) -> tuple[dict[int, float], float]:
    """Fator ano t: 1 / (1+WACC)^(i+1), i = 0..N-1."""
    if anos is None:
        raise ValueError("anos é obrigatório (use ctx.projected_years).")
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
    anos: tuple[int, ...],
    ano_ultimo: int | None = None,
) -> tuple[float, float, float, float]:
    ano_ultimo = ano_ultimo if ano_ultimo is not None else anos[-1]
    idx_ult = anos.index(ano_ultimo)
    fator_ult = 1.0 / (1.0 + wacc) ** (idx_ult + 1)

    fcff_term = fcff_ultimo_ano * (1.0 + g)
    vt = valor_terminal_gordon(fcff_term, wacc, g)
    vp_vt = vt * fator_ult
    ev = soma_vp_fcffs + vp_vt
    return ev, fcff_term, vt, vp_vt


def equity_value_bridge(ev: float, caixa: float | None = None, divida: float = DIVIDA_LIQUIDA) -> float:
    if caixa is None:
        raise ValueError("caixa é obrigatório (use ctx.base_values.caixa_base).")
    return ev + caixa - divida


def multiplos_implicitos(
    ev: float,
    ebitda_primeiro_ano: float,
    rl_primeiro_ano: float,
    ll_primeiro_ano: float,
    fcff_primeiro_ano: float,
    primeiro_ano: int,
) -> dict[str, float]:
    """Chaves dinâmicas conforme o primeiro ano projetado."""
    y = int(primeiro_ano)
    return {
        f"EV_EBITDA_{y}": ev / ebitda_primeiro_ano if ebitda_primeiro_ano else float("nan"),
        f"EV_RL_{y}": ev / rl_primeiro_ano if rl_primeiro_ano else float("nan"),
        f"P_E_{y}": ev / ll_primeiro_ano if ll_primeiro_ano else float("nan"),
        f"FCFF_Yield_{y}": fcff_primeiro_ano / ev if ev else float("nan"),
    }


def montar_tabela_dcf(
    df_fluxo: pd.DataFrame,
    df_consolidado: pd.DataFrame,
    ctx: SimulationContext,
    wacc: float = WACC_FIXO,
    g: float = G_PERPETUIDADE,
) -> dict:
    fcffs = df_fluxo.set_index("ano")["fcff"]
    dct = fcffs.to_dict()
    anos = ctx.year_config.projected_years
    vp_por_ano, soma_vp = valor_presente_fcffs(dct, wacc=wacc, anos=anos)

    ult = anos[-1]
    fcff_ult = float(fcffs.loc[ult])
    ev, fcff_term, vt, vp_vt = enterprise_value(soma_vp, fcff_ult, wacc, g, anos, ano_ultimo=ult)
    eqv = equity_value_bridge(ev, caixa=ctx.base_values.caixa_base)

    cons = df_consolidado.set_index("ano")
    first_proj_year = int(anos[0])
    ebitda_p = float(cons.at[first_proj_year, "ebitda"])
    rl_p = float(cons.at[first_proj_year, "receita_liquida"])
    ll_p = float(cons.at[first_proj_year, "lucro_liquido"])
    fcff_p = float(fcffs.loc[first_proj_year])

    mult = multiplos_implicitos(ev, ebitda_p, rl_p, ll_p, fcff_p, first_proj_year)

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
