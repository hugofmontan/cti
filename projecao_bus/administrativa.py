"""
Projecao DRE Administrativa (2026-2030).
"""

from typing import Iterable

import pandas as pd

from fopm import INFLACAO_FOCUS, _validar_anos, salvar_projecao_csv

# Drivers fixos conforme plano_implementacao_administrativa.md
RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA = 0.12415802928103117
MC2_FIXO = 376_375.08
RATEIO_TOTAL_2025 = 5_047_539.09
HONORARIOS_ADM_FIXO = 1_310_000.0
HONORARIOS_RATEIO_FIXO = -1_222_000.0
N_FUNC_ADM = 0

# Referencias consolidadas da operacao (inclui Data Science).
RL_CONSOLIDADA_REF = {
    2026: 46_939_343.0,
    2027: 51_109_974.0,
    2028: 55_569_432.0,
    2029: 60_162_741.0,
    2030: 67_191_035.0,
}

TOTAL_FUNC_OPERACIONAL_REF = {
    2026: 108.186,
    2027: 113.269,
    2028: 117.418,
    2029: 124.543,
    2030: 129.923,
}

RATEIO_POR_BU_FIXO = {
    "fopm": {2026: 2_231_383.0, 2027: 2_260_328.0, 2028: 2_304_801.0, 2029: 2_295_843.0, 2030: 2_370_778.0},
    "renovacao": {2026: 145_525.0, 2027: 144_276.0, 2028: 144_050.0, 2029: 140_562.0, 2030: 139_458.0},
    "ams": {2026: 2_579_968.0, 2027: 2_609_915.0, 2028: 2_660_970.0, 2029: 2_649_267.0, 2030: 2_692_591.0},
    "venda_sw": {2026: 48_508.0, 2027: 48_092.0, 2028: 48_017.0, 2029: 46_854.0, 2030: 46_486.0},
    "data_science": {2026: 242_542.0, 2027: 384_737.0, 2028: 480_167.0, 2029: 702_809.0, 2030: 790_259.0},
}


def projetar_dre_administrativa(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "ADMINISTRATIVA",
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Administrativa com base em RL consolidada e rateio inflacionado.
    """
    anos_list = _validar_anos(anos)
    resultados: list[dict] = []

    rateio_total_ant = RATEIO_TOTAL_2025

    for ano in anos_list:
        inflacao = INFLACAO_FOCUS[ano]
        rl_consolidada_ref = RL_CONSOLIDADA_REF[ano]

        outras_desp_adm = rl_consolidada_ref * RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA
        rateio_adm_total = -(rateio_total_ant * (1.0 + inflacao))

        total_func_operacional = TOTAL_FUNC_OPERACIONAL_REF[ano]
        rateio_fopm = RATEIO_POR_BU_FIXO["fopm"][ano]
        rateio_renovacao = RATEIO_POR_BU_FIXO["renovacao"][ano]
        rateio_ams = RATEIO_POR_BU_FIXO["ams"][ano]
        rateio_venda_sw = RATEIO_POR_BU_FIXO["venda_sw"][ano]
        rateio_data_science = RATEIO_POR_BU_FIXO["data_science"][ano]

        ebitda = (
            MC2_FIXO
            - outras_desp_adm
            - rateio_adm_total
            - HONORARIOS_ADM_FIXO
            - HONORARIOS_RATEIO_FIXO
        )
        ebit = ebitda
        lair = ebit
        lucro_liquido = lair

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "mc2": MC2_FIXO,
                "outras_desp_adm": outras_desp_adm,
                "rl_consolidada_ref": rl_consolidada_ref,
                "rateio_adm_total": rateio_adm_total,
                "honorarios_adm": HONORARIOS_ADM_FIXO,
                "honorarios_rateio": HONORARIOS_RATEIO_FIXO,
                "ebitda": ebitda,
                "ebit": ebit,
                "lair": lair,
                "lucro_liquido": lucro_liquido,
                "n_funcionarios_adm": N_FUNC_ADM,
                "rateio_fopm": rateio_fopm,
                "rateio_renovacao": rateio_renovacao,
                "rateio_ams": rateio_ams,
                "rateio_venda_sw": rateio_venda_sw,
                "rateio_data_science": rateio_data_science,
                "total_func_operacional": total_func_operacional,
            }
        )

        rateio_total_ant = abs(rateio_adm_total)

    df = pd.DataFrame(resultados)
    colunas_ordenadas = [
        "bu",
        "ano",
        "mc2",
        "outras_desp_adm",
        "rl_consolidada_ref",
        "rateio_adm_total",
        "honorarios_adm",
        "honorarios_rateio",
        "ebitda",
        "ebit",
        "lair",
        "lucro_liquido",
        "n_funcionarios_adm",
        "rateio_fopm",
        "rateio_renovacao",
        "rateio_ams",
        "rateio_venda_sw",
        "rateio_data_science",
        "total_func_operacional",
    ]
    return df[colunas_ordenadas]


def projetar_e_salvar_administrativa(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "ADMINISTRATIVA",
):
    """Grava `projecoes/projecao_administrativa.csv`."""
    df = projetar_dre_administrativa(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_administrativa.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_administrativa()
    print(f"Projecao Administrativa salva em: {caminho}")
