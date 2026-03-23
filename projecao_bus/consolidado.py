"""
Projecao DRE Consolidada (2026-2030).
"""

from pathlib import Path
from typing import Iterable

import pandas as pd

from fopm import _validar_anos, salvar_projecao_csv

CHAVES_BU_OPERACIONAIS = ("fopm", "renovacao", "ams", "venda_sw", "data_science")

ANOS_PADRAO = (2026, 2027, 2028, 2029, 2030)

AMORTIZACAO_CFP = {
    2026: -189_520.0,
    2027: -178_575.0,
    2028: -170_519.0,
    2029: -151_534.0,
    2030: -139_244.0,
}

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
    resultados: list[dict] = []
    caixa_ant = CAIXA_BASE_2025

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
        honorarios_adm = sum(float(dfs[k].at[ano, "honorarios_adm"]) for k in CHAVES_BU_OPERACIONAIS)
        ebitda = sum(float(dfs[k].at[ano, "ebitda"]) for k in CHAVES_BU_OPERACIONAIS)

        # Rateio cancela na consolidacao (transferencia interna).
        rateio_adm = 0.0

        da_ams = float(dfs["ams"].at[ano, "depreciacao_amort"])
        da_consolidada = da_ams - abs(AMORTIZACAO_CFP[ano])
        ebit = ebitda - da_consolidada

        receita_financeira = caixa_ant * (SELIC_FOCUS[ano] * SPREAD_RENDIMENTO_CAIXA)
        despesa_financeira = DESPESA_FINANCEIRA_FIXA
        lair = ebit + receita_financeira - despesa_financeira

        # IRPJ consolidado = IRPJ da AMS.
        irpj_csll = float(dfs["ams"].at[ano, "irpj_csll"])
        lucro_liquido = lair - irpj_csll
        participacoes = lucro_liquido * RATIO_PARTICIPACOES
        caixa = caixa_ant + lucro_liquido - participacoes

        resultados.append(
            {
                "ano": ano,
                "receita_bruta": receita_bruta,
                "deducoes": deducoes,
                "receita_liquida": receita_liquida,
                "incentivos": incentivos,
                "gastos_pessoal": gastos_pessoal,
                "outras_desp_diretas": outras_desp_diretas,
                "mc1": mc1,
                "mc1_pct_rl": mc1 / receita_liquida if receita_liquida else 0.0,
                "remuneracao_socios": remuneracao_socios,
                "mc2": mc2,
                "mc2_pct_rl": mc2 / receita_liquida if receita_liquida else 0.0,
                "outras_desp_adm": outras_desp_adm,
                "honorarios_adm": honorarios_adm,
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
