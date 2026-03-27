"""
Projecao DRE Consolidada (2026-2030).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .context import SimulationContext, default_simulation_context
from .shared import salvar_projecao_csv, sort_years_non_empty
CHAVES_BU_OPERACIONAIS = ("fopm", "renovacao", "ams", "venda_sw", "data_science")
# Consolidado da planilha inclui também a BU Administrativa (rateio interno deve "fechar").
CHAVES_BU_CONSOLIDADO = CHAVES_BU_OPERACIONAIS + ("administrativa",)

SPREAD_RENDIMENTO_CAIXA = 0.95
DESPESA_FINANCEIRA_FIXA = 95_333.33
RATIO_PARTICIPACOES = 0.047806


def _carregar_projecoes_operacionais(base_dir: Path) -> dict[str, pd.DataFrame]:
    proj_dir = base_dir / "projecoes"
    arquivos = {
        "fopm": "projecao_fopm_brasil.csv",
        "renovacao": "projecao_renovacao.csv",
        "ams": "projecao_ams.csv",
        "venda_sw": "projecao_venda_softwares.csv",
        "data_science": "projecao_data_science.csv",
    }
    out: dict[str, pd.DataFrame] = {}
    for nome, arq in arquivos.items():
        caminho = proj_dir / arq
        out[nome] = pd.read_csv(caminho)
    return out


def _normalizar_dfs_operacionais(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Garante índice por ano e chaves esperadas."""
    out: dict[str, pd.DataFrame] = {}
    for k in CHAVES_BU_CONSOLIDADO:
        if k not in dfs:
            raise ValueError(f"DataFrame operacional ausente: {k}")
        df = dfs[k]
        if "ano" in df.columns:
            df = df.set_index("ano")
        out[k] = df
    return out


def projetar_dre_consolidado_de_dfs(
    dfs: dict[str, pd.DataFrame],
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
) -> pd.DataFrame:
    """
    Consolida a partir de DataFrames já calculados (sem ler CSVs).
    Chaves: fopm, renovacao, ams, venda_sw, data_science.
    """
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    dfs_i = _normalizar_dfs_operacionais(dfs)
    return _projetar_consolidado_core(dfs_i, anos_list, ctx)


def _projetar_consolidado_core(
    dfs: dict[str, pd.DataFrame],
    anos_list: list[int],
    ctx: SimulationContext,
) -> pd.DataFrame:
    """
    D&A consolidada = D&A total do BP (cascata CAPEX × 20% por safra).

    Caixa e receita financeira seguem a cadeia do modelo (sem circularidade):
    Rec.Fin(t) = SELIC(t)×0,95×Caixa(t−1); depois DRE (EBIT, LAIR, LL);
    NOPAT = EBIT − IRPJ/CSLL_AMS (IR da DRE AMS, LAIR AMS × 34%); FCFF = NOPAT + D&A − CAPEX − ΔNCG;
    Caixa(t) = Caixa(t−1) + FCFF(t) − Dividendos(t), Dividendos = 50%×LL.
    Participações são apenas linha de DRE (não entram nesse saldo de caixa).
    """
    from .dcf.bp import montar_bp
    from .dcf.constants import MESES_RESERVA_CAIXA
    from .dcf.ncgl import montar_ncgl
    from .rateio_administrativo import total_func_operacional_de_dfs

    # CFP linha 37 (Honorários ADM Sócios Diretores): média rolling de 3 anos
    # sobre o consolidado, sem somar as BUs na projeção.
    honorarios_cfp_hist: dict[int, float] = {
        2022: 2_280_000.0,
        2023: 2_451_000.0,
        2024: 2_508_000.0,
        2025: 2_508_000.0,
    }
    honorarios_cfp_por_ano: dict[int, float] = dict(honorarios_cfp_hist)
    # Média móvel de 3 anos: Honorários(t) = média(t-3,t-2,t-1). Precisamos preencher
    # todos os anos até max(anos_list), senão quando a projeção começa em 2027+ (ex.:
    # histórico termina em 2026) falta a entrada intermediária de 2026 e dá KeyError.
    y_hi = max(anos_list)
    y_next = max(honorarios_cfp_por_ano.keys()) + 1
    while y_next <= y_hi:
        honorarios_cfp_por_ano[y_next] = (
            honorarios_cfp_por_ano[y_next - 3]
            + honorarios_cfp_por_ano[y_next - 2]
            + honorarios_cfp_por_ano[y_next - 1]
        ) / 3.0
        y_next += 1

    # 1) Linhas operacionais + DataFrame de entrada do BP (mesmas colunas que `montar_bp` usa)
    linhas_pre: list[dict[str, float | int]] = []
    selic_map = ctx.selic_focus
    _selic_last_year = max(selic_map.keys())
    _selic_last_val = selic_map[_selic_last_year]
    for ano in anos_list:
        receita_bruta = sum(float(dfs[k].at[ano, "faturamento_bruto"]) for k in CHAVES_BU_CONSOLIDADO)
        deducoes = sum(float(dfs[k].at[ano, "impostos_sv"]) for k in CHAVES_BU_CONSOLIDADO)
        receita_liquida = sum(float(dfs[k].at[ano, "receita_liquida"]) for k in CHAVES_BU_CONSOLIDADO)
        incentivos = sum(float(dfs[k].at[ano, "incentivos"]) for k in CHAVES_BU_CONSOLIDADO)
        gastos_pessoal = sum(float(dfs[k].at[ano, "gastos_pessoal"]) for k in CHAVES_BU_CONSOLIDADO)
        outras_desp_diretas = sum(float(dfs[k].at[ano, "outras_desp_diretas"]) for k in CHAVES_BU_CONSOLIDADO)
        mc1 = sum(float(dfs[k].at[ano, "mc1"]) for k in CHAVES_BU_CONSOLIDADO)
        remuneracao_socios = sum(float(dfs[k].at[ano, "remuneracao_socios"]) for k in CHAVES_BU_CONSOLIDADO)
        mc2 = sum(float(dfs[k].at[ano, "mc2"]) for k in CHAVES_BU_CONSOLIDADO)
        outras_desp_adm = sum(float(dfs[k].at[ano, "outras_desp_adm"]) for k in CHAVES_BU_CONSOLIDADO)
        honorarios_adm = float(honorarios_cfp_por_ano[ano])
        ebitda = sum(float(dfs[k].at[ano, "ebitda"]) for k in CHAVES_BU_CONSOLIDADO)
        linhas_pre.append(
            {
                "ano": ano,
                "receita_bruta": receita_bruta,
                "deducoes": deducoes,
                "receita_liquida": receita_liquida,
                "incentivos": incentivos,
                "gastos_pessoal": gastos_pessoal,
                "outras_desp_diretas": outras_desp_diretas,
                "mc1": mc1,
                "remuneracao_socios": remuneracao_socios,
                "mc2": mc2,
                "outras_desp_adm": outras_desp_adm,
                "honorarios_adm": honorarios_adm,
                "ebitda": ebitda,
            }
        )

    df_bp_in = pd.DataFrame(linhas_pre)
    total_func = total_func_operacional_de_dfs(dfs, anos_list)
    df_bp = montar_bp(df_bp_in, total_func, ctx, usar_custos_excl_gabarito=True)
    da_por_ano = df_bp.set_index("ano")["da_total"].to_dict()
    capex_por_ano = df_bp.set_index("ano")["capex"].to_dict()
    df_ncgl = montar_ncgl(df_bp, ctx)
    delta_ncg_por_ano = df_ncgl.set_index("ano")["delta_ncg"].to_dict()

    resultados: list[dict] = []
    caixa_ant = ctx.base_values.caixa_base

    for row in linhas_pre:
        ano = int(row["ano"])
        receita_liquida = float(row["receita_liquida"])
        ebitda = float(row["ebitda"])

        # CONS.FORMATO PARCEIRO linha 40:
        # D&A consolidada para DRE = D&A_presumido_bp + D&A_ams (valor positivo),
        # sem dupla contagem. No motor atual, `da_nova_bp` já reflete o total
        # consolidado da cascata, então usamos esse total diretamente.
        da_nova_bp = float(da_por_ano[ano])
        da_consolidada = da_nova_bp
        ebit = ebitda - da_consolidada

        selic = selic_map.get(int(ano), _selic_last_val)
        receita_financeira = caixa_ant * (selic * SPREAD_RENDIMENTO_CAIXA)
        despesa_financeira = DESPESA_FINANCEIRA_FIXA
        lair = ebit + receita_financeira - despesa_financeira

        # IRPJ/CSLL por BU (somente AMS tem valor > 0 no modelo).
        irpj_csll = sum(float(dfs[k].at[ano, "irpj_csll"]) for k in CHAVES_BU_CONSOLIDADO if "irpj_csll" in dfs[k].columns)
        lucro_liquido = lair - irpj_csll
        participacoes = lucro_liquido * RATIO_PARTICIPACOES

        ir_csll_nopat = float(dfs["ams"].at[ano, "irpj_csll"])
        nopat = ebit - ir_csll_nopat
        capex = float(capex_por_ano[ano])
        dncg = float(delta_ncg_por_ano[ano])
        fcff = nopat + da_consolidada - capex - dncg
        # Política do modelo Excel:
        # FLUXO!B20 = (CONSOLIDADO!K11 + CONSOLIDADO!K18) * 4/12
        # K11 = incentivos + gastos_pessoal + outras_desp_diretas
        # K18 = remuneracao_socios + outras_desp_adm + rateio_adm + honorarios_adm + incentivos
        # Observação: incentivos entra duas vezes (K11 e K18), conforme planilha.
        k11 = (
            float(row["incentivos"])
            + float(row["gastos_pessoal"])
            + float(row["outras_desp_diretas"])
        )
        k18 = (
            float(row["remuneracao_socios"])
            + float(row["outras_desp_adm"])
            + float(row.get("rateio_adm", 0.0))
            + float(row["honorarios_adm"])
            + float(row["incentivos"])
        )
        custos_despesas_totais = k11 + k18
        caixa_minimo = custos_despesas_totais * (MESES_RESERVA_CAIXA / 12.0)
        caixa_antes_dividendos = caixa_ant + fcff
        dividendos = max(caixa_antes_dividendos - caixa_minimo, 0.0)
        caixa = caixa_antes_dividendos - dividendos

        mc1 = float(row["mc1"])
        mc2 = float(row["mc2"])

        resultados.append(
            {
                "ano": ano,
                "receita_bruta": float(row["receita_bruta"]),
                "deducoes": float(row["deducoes"]),
                "receita_liquida": receita_liquida,
                "incentivos": float(row["incentivos"]),
                "gastos_pessoal": float(row["gastos_pessoal"]),
                "outras_desp_diretas": float(row["outras_desp_diretas"]),
                "mc1": mc1,
                "mc1_pct_rl": mc1 / receita_liquida if receita_liquida else 0.0,
                "remuneracao_socios": float(row["remuneracao_socios"]),
                "mc2": mc2,
                "mc2_pct_rl": mc2 / receita_liquida if receita_liquida else 0.0,
                "outras_desp_adm": float(row["outras_desp_adm"]),
                "honorarios_adm": float(row["honorarios_adm"]),
                "ebitda": ebitda,
                "ebitda_pct_rl": ebitda / receita_liquida if receita_liquida else 0.0,
                "da_consolidada": da_consolidada,
                "ebit": ebit,
                "receita_financeira": receita_financeira,
                "despesa_financeira": despesa_financeira,
                "lair": lair,
                "irpj_csll": irpj_csll,
                "lucro_liquido": lucro_liquido,
                "lucro_liquido_pct_rl": lucro_liquido / receita_liquida if receita_liquida else 0.0,
                "participacoes": participacoes,
                "caixa": caixa,
            }
        )

        caixa_ant = caixa

    return pd.DataFrame(resultados)


def projetar_dre_consolidado(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    base_dir: Path | None = None,
) -> pd.DataFrame:
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    dfs = _carregar_projecoes_operacionais(base_dir)
    for k in dfs:
        dfs[k] = dfs[k].set_index("ano")

    return _projetar_consolidado_core(dfs, anos_list, ctx)


def projetar_e_salvar_consolidado(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    base_dir: Path | None = None,
):
    df = projetar_dre_consolidado(ctx=ctx, anos=anos, base_dir=base_dir)
    return salvar_projecao_csv(df, base_dir=base_dir, nome_arquivo="projecao_consolidado.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_consolidado()
    print(f"Projecao Consolidado salva em: {caminho}")
