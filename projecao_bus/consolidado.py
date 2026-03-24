"""
Projecao DRE Consolidada (2026-2030).
"""

from pathlib import Path
from typing import Iterable

import pandas as pd

from .shared import _validar_anos, salvar_projecao_csv

CHAVES_BU_OPERACIONAIS = ("fopm", "renovacao", "ams", "venda_sw", "data_science")

ANOS_PADRAO = (2026, 2027, 2028, 2029, 2030)

SELIC_FOCUS = {
    2026: 0.1213,
    2027: 0.1050,
    2028: 0.1000,
    2029: 0.0950,
    2030: 0.1000,
}

CAIXA_BASE_2025 = 8_018_000.0
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
    for k in CHAVES_BU_OPERACIONAIS:
        if k not in dfs:
            raise ValueError(f"DataFrame operacional ausente: {k}")
        df = dfs[k]
        if "ano" in df.columns:
            df = df.set_index("ano")
        out[k] = df
    return out


def projetar_dre_consolidado_de_dfs(
    dfs: dict[str, pd.DataFrame],
    anos: Iterable[int] = ANOS_PADRAO,
) -> pd.DataFrame:
    """
    Consolida a partir de DataFrames já calculados (sem ler CSVs).
    Chaves: fopm, renovacao, ams, venda_sw, data_science.
    """
    anos_list = _validar_anos(anos)
    dfs_i = _normalizar_dfs_operacionais(dfs)
    return _projetar_consolidado_core(dfs_i, anos_list)


def _projetar_consolidado_core(
    dfs: dict[str, pd.DataFrame],
    anos_list: list[int],
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
    from .dcf.constants import PAYOUT_DIVIDENDOS
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
    for ano in anos_list:
        honorarios_cfp_por_ano[ano] = (
            honorarios_cfp_por_ano[ano - 3] + honorarios_cfp_por_ano[ano - 2] + honorarios_cfp_por_ano[ano - 1]
        ) / 3.0

    # 1) Linhas operacionais + DataFrame de entrada do BP (mesmas colunas que `montar_bp` usa)
    linhas_pre: list[dict[str, float | int]] = []
    for ano in anos_list:
        receita_bruta = sum(float(dfs[k].at[ano, "faturamento_bruto"]) for k in CHAVES_BU_OPERACIONAIS)
        deducoes = sum(float(dfs[k].at[ano, "impostos_sv"]) for k in CHAVES_BU_OPERACIONAIS)
        receita_liquida = sum(float(dfs[k].at[ano, "receita_liquida"]) for k in CHAVES_BU_OPERACIONAIS)
        incentivos = sum(float(dfs[k].at[ano, "incentivos"]) for k in CHAVES_BU_OPERACIONAIS)
        gastos_pessoal = sum(float(dfs[k].at[ano, "gastos_pessoal"]) for k in CHAVES_BU_OPERACIONAIS)
        outras_desp_diretas = sum(float(dfs[k].at[ano, "outras_desp_diretas"]) for k in CHAVES_BU_OPERACIONAIS)
        mc1 = sum(float(dfs[k].at[ano, "mc1"]) for k in CHAVES_BU_OPERACIONAIS)
        remuneracao_socios = sum(float(dfs[k].at[ano, "remuneracao_socios"]) for k in CHAVES_BU_OPERACIONAIS)
        mc2 = sum(float(dfs[k].at[ano, "mc2"]) for k in CHAVES_BU_OPERACIONAIS)
        outras_desp_adm = sum(float(dfs[k].at[ano, "outras_desp_adm"]) for k in CHAVES_BU_OPERACIONAIS)
        honorarios_adm = float(honorarios_cfp_por_ano[ano])
        ebitda = sum(float(dfs[k].at[ano, "ebitda"]) for k in CHAVES_BU_OPERACIONAIS)
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
    df_bp = montar_bp(df_bp_in, total_func, usar_custos_excl_gabarito=True)
    da_por_ano = df_bp.set_index("ano")["da_total"].to_dict()
    capex_por_ano = df_bp.set_index("ano")["capex"].to_dict()
    df_ncgl = montar_ncgl(df_bp)
    delta_ncg_por_ano = df_ncgl.set_index("ano")["delta_ncg"].to_dict()

    resultados: list[dict] = []
    caixa_ant = CAIXA_BASE_2025

    for row in linhas_pre:
        ano = int(row["ano"])
        receita_liquida = float(row["receita_liquida"])
        ebitda = float(row["ebitda"])

        # CONS.FORMATO PARCEIRO linha 40:
        # DA_CFP = (-BP!G93) - DRE_AMS!J45 = DA_nova_BP - DA_AMS
        # Mantemos aqui a mesma convenção de sinal da planilha (valor pode ficar negativo).
        da_nova_bp = float(da_por_ano[ano])
        da_ams = float(dfs["ams"].at[ano, "depreciacao_amort"])
        da_consolidada = da_nova_bp - da_ams
        ebit = ebitda - da_consolidada

        receita_financeira = caixa_ant * (SELIC_FOCUS[ano] * SPREAD_RENDIMENTO_CAIXA)
        despesa_financeira = DESPESA_FINANCEIRA_FIXA
        lair = ebit + receita_financeira - despesa_financeira

        # IRPJ/CSLL por BU (somente AMS tem valor > 0 no modelo).
        irpj_csll = sum(float(dfs[k].at[ano, "irpj_csll"]) for k in CHAVES_BU_OPERACIONAIS)
        lucro_liquido = lair - irpj_csll
        participacoes = lucro_liquido * RATIO_PARTICIPACOES

        ir_csll_nopat = float(dfs["ams"].at[ano, "irpj_csll"])
        nopat = ebit - ir_csll_nopat
        capex = float(capex_por_ano[ano])
        dncg = float(delta_ncg_por_ano[ano])
        fcff = nopat + da_consolidada - capex - dncg
        dividendos = lucro_liquido * PAYOUT_DIVIDENDOS
        caixa = caixa_ant + fcff - dividendos

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
    anos: Iterable[int] = ANOS_PADRAO,
    base_dir: Path | None = None,
) -> pd.DataFrame:
    anos_list = _validar_anos(anos)
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    dfs = _carregar_projecoes_operacionais(base_dir)
    for k in dfs:
        dfs[k] = dfs[k].set_index("ano")

    return _projetar_consolidado_core(dfs, anos_list)


def projetar_e_salvar_consolidado(
    anos: Iterable[int] = ANOS_PADRAO,
    base_dir: Path | None = None,
):
    df = projetar_dre_consolidado(anos=anos, base_dir=base_dir)
    return salvar_projecao_csv(df, base_dir=base_dir, nome_arquivo="projecao_consolidado.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_consolidado()
    print(f"Projecao Consolidado salva em: {caminho}")
