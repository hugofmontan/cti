import math
from pathlib import Path
from typing import Iterable, List, Optional, Union

import numpy as np
import pandas as pd


INFLACAO_FOCUS = {
    2026: 0.0397,
    2027: 0.0380,
    2028: 0.0350,
    2029: 0.0350,
    2030: 0.0350,
}

ALIQUOTA_ISV = 0.1743

HEADCOUNT_PLANEJADO = {
    2026: 46,
    2027: 47,
    2028: 48,
    2029: 49,
    2030: 51,
}

OCIOSIDADE = {
    2026: 0.245,
    2027: 0.24,
    2028: 0.23,
    2029: 0.225,
    2030: 0.21,
}


def _carregar_historico_csv(
    caminho_csv: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    Lê o CSV histórico em formato "uma linha por métrica" e retorna
    um DataFrame com índice na coluna `linha`.
    Por padrão, procura `data/dre_fopm_historico.csv` na raiz do projeto
    (um nível acima da pasta deste módulo).
    """
    if caminho_csv is None:
        base_dir = Path(__file__).resolve().parent.parent
        caminho_csv = base_dir / "data" / "dre_fopm_historico.csv"

    df = pd.read_csv(caminho_csv)
    if "linha" not in df.columns:
        raise ValueError("CSV histórico deve ter a coluna 'linha'.")

    df = df.set_index("linha")
    return df


def _media_ratio_seguro(numerador: np.ndarray, denominador: np.ndarray) -> float:
    """Calcula média de (numerador/denominador) tratando divisões por zero como NaN."""
    numerador = np.asarray(numerador, dtype="float64")
    denominador = np.asarray(denominador, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(denominador == 0, np.nan, numerador / denominador)
    return float(np.nanmean(ratio))


def _calcular_ratios_e_bases_de_csv(
    caminho_csv: Optional[Union[str, Path]] = None,
    janela_anos: int = 3,
) -> dict:
    """
    Calcula os ratios históricos e bases *a partir do CSV*,
    usando sempre que possível os dados de 2023–2025.

    Alguns drivers (ticket médio e horas por NF) ainda dependem
    de premissas externas, pois não constam no CSV.
    """
    df = _carregar_historico_csv(caminho_csv)

    # Detecta automaticamente as colunas de ano numéricas presentes no CSV
    col_anos = [c for c in df.columns if isinstance(c, str) and c.isdigit()]
    if not col_anos:
        raise ValueError("CSV histórico não possui colunas de anos numéricos (ex: '2023').")
    col_anos_ordenados = sorted(col_anos)

    # Usa sempre os últimos `janela_anos` anos disponíveis como base de cálculo
    anos_base = col_anos_ordenados[-janela_anos:]

    def linha_valores(label: str) -> np.ndarray:
        if label not in df.index:
            raise KeyError(f"Linha '{label}' não encontrada no histórico.")
        return df.loc[label, anos_base].to_numpy(dtype="float64")

    # Receitas / custos básicos
    rl = linha_valores("RECEITA LÍQUIDA")

    # Incentivos / RL
    incentivos = linha_valores("INCENTIVOS DE PROSPECÇÃO E VENDAS")
    ratio_incentivos_pct_rl = _media_ratio_seguro(incentivos, rl)

    # Outras Despesas Diretas / RL
    outras_dir = linha_valores("OUTRAS DESPESAS DIRETAS")
    ratio_outras_dir_pct_rl = _media_ratio_seguro(outras_dir, rl)

    # MC I e Remuneração Direta dos Sócios → Rem. Sócios / MC I
    mc1 = linha_valores("MARGEM CONTRIBUIÇÃO I")
    rem_socios = linha_valores("REMUNERAÇÃO DIRETA DOS SÓCIOS")
    ratio_rem_socios_pct_mc1 = _media_ratio_seguro(rem_socios, mc1)

    # Outras Desp. ADM / RL
    outras_adm = linha_valores("OUTRAS DESPESAS ADMINISTRATIVAS")
    ratio_outras_adm_pct_rl = _media_ratio_seguro(outras_adm, rl)

    # Custo/Func (R$/ano) — se tivermos # Funcionários - Média no CSV
    custo_func_base: float
    try:
        gastos_pessoal = linha_valores("GASTOS COM PESSOAL")
        n_func_hist = linha_valores("# Funcionários - Média")
        with np.errstate(divide="ignore", invalid="ignore"):
            custo_func_anos = np.where(n_func_hist == 0, np.nan, gastos_pessoal / n_func_hist)
        custo_func_base = float(np.nanmean(custo_func_anos))
    except KeyError:
        # Fallback: usa a média já calculada na planilha (144.998),
        # mantendo rastreabilidade no código.
        custo_func_base = 144998.0

    # Horas por NF (h) — derivadas de trás para frente a partir de:
    # - Horas Alocadas históricas (premissas operacionais)
    # - Total NFs (contagem na aba FAT. FOPM BRASIL)
    #
    # Aqui usamos a mesma lógica de janela móvel: se você adicionar novos
    # anos na base de premissas abaixo (ex.: incluir 2026 futuramente),
    # eles entram automaticamente na média.
    horas_alocadas_hist = {
        2023: 67830.0,
        2024: 63130.0,
        2025: 65280.0,
    }
    nfs_hist = {
        2023: 216.0,
        2024: 258.0,
        2025: 249.0,
    }
    anos_premissas_horas = sorted(horas_alocadas_hist.keys())
    anos_premissas_janela = anos_premissas_horas[-janela_anos:]

    horas_por_nf_anos = []
    for ano in anos_premissas_janela:
        h = horas_alocadas_hist[ano]
        nfs = nfs_hist.get(ano, 0.0)
        horas_por_nf_anos.append(h / nfs if nfs else np.nan)
    horas_por_nf = float(np.nanmean(np.array(horas_por_nf_anos, dtype="float64")))

    # Ticket médio 2024 e 2025 (R$/NF) — também vindo da aba de premissas
    ticket_2024 = 95_237.0
    ticket_2025 = 91_514.0
    ticket_base_2026 = (ticket_2024 + ticket_2025) / 2.0

    # Honorários base (R$/ano) — valor histórico 2024/2025
    honorarios_base = 528000.0

    return {
        "ratio_incentivos_pct_rl": ratio_incentivos_pct_rl,
        "ratio_outras_dir_pct_rl": ratio_outras_dir_pct_rl,
        "ratio_rem_socios_pct_mc1": ratio_rem_socios_pct_mc1,
        "ratio_outras_adm_pct_rl": ratio_outras_adm_pct_rl,
        "custo_func_base": custo_func_base,
        "horas_por_nf": horas_por_nf,
        "ticket_base_2026": ticket_base_2026,
        "honorarios_base": honorarios_base,
    }


_DRIVERS = _calcular_ratios_e_bases_de_csv()

RATIO_INCENTIVOS_PCT_RL = _DRIVERS["ratio_incentivos_pct_rl"]
RATIO_OUTRAS_DIR_PCT_RL = _DRIVERS["ratio_outras_dir_pct_rl"]
RATIO_REM_SOCIOS_PCT_MC1 = _DRIVERS["ratio_rem_socios_pct_mc1"]
RATIO_OUTRAS_ADM_PCT_RL = _DRIVERS["ratio_outras_adm_pct_rl"]

CUSTO_FUNC_BASE = _DRIVERS["custo_func_base"]
HORAS_POR_NF = _DRIVERS["horas_por_nf"]
TICKET_BASE_2026 = _DRIVERS["ticket_base_2026"]
HONORARIOS_BASE = _DRIVERS["honorarios_base"]

RATEIO_ADM_FIXO = {
    2026: 2_231_383.0,
    2027: 2_260_328.0,
    2028: 2_304_801.0,
    2029: 2_295_843.0,
    2030: 2_370_778.0,
}


def _validar_anos(anos: Iterable[int]) -> List[int]:
    anos_list = list(anos)
    if not anos_list:
        raise ValueError("Lista de anos não pode ser vazia.")
    for ano in anos_list:
        if ano not in INFLACAO_FOCUS:
            raise ValueError(f"Ano {ano} não possui premissas cadastradas.")
    return sorted(anos_list)


def projetar_dre_fopm_brasil(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "FOPM BRASIL",
) -> pd.DataFrame:
    """
    Projeta a DRE FOPM Brasil de 2026 a 2030 seguindo o plano de implementação.

    Retorna um DataFrame com uma linha por ano e as colunas especificadas em planfopm.md.
    """
    anos_list = _validar_anos(anos)

    resultados = []

    ticket_ant = TICKET_BASE_2026
    custo_func_ant = CUSTO_FUNC_BASE
    honorarios_ant = HONORARIOS_BASE

    for ano in anos_list:
        inflacao = INFLACAO_FOCUS[ano]
        n_funcionarios = HEADCOUNT_PLANEJADO[ano]
        ociosidade = OCIOSIDADE[ano]

        total_horas = n_funcionarios * 160.0 * 12.0
        horas_alocadas = total_horas * (1.0 - ociosidade)
        horas_por_nf = HORAS_POR_NF
        total_nfs = horas_alocadas / horas_por_nf if horas_por_nf else math.nan

        if ano == 2026:
            ticket_medio = ticket_ant
        else:
            ticket_medio = ticket_ant * (1.0 + inflacao)

        faturamento_bruto = total_nfs * ticket_medio
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * RATIO_INCENTIVOS_PCT_RL

        custo_por_func = custo_func_ant * (1.0 + inflacao + 0.01)
        gastos_pessoal = n_funcionarios * custo_por_func

        outras_desp_diretas = receita_liquida * RATIO_OUTRAS_DIR_PCT_RL

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * RATIO_REM_SOCIOS_PCT_MC1

        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        outras_desp_adm = receita_liquida * RATIO_OUTRAS_ADM_PCT_RL
        rateio_adm = RATEIO_ADM_FIXO[ano]

        honorarios_adm = honorarios_ant * (1.0 + inflacao)

        ebitda = mc2 - outras_desp_adm - rateio_adm - honorarios_adm
        ebitda_pct_rl = ebitda / receita_liquida if receita_liquida else math.nan

        ebit = ebitda
        lair = ebit
        irpj_csll = 0.0
        lucro_liquido = lair

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "n_funcionarios": n_funcionarios,
                "ociosidade": ociosidade,
                "inflacao_focus": inflacao,
                "total_horas": total_horas,
                "horas_alocadas": horas_alocadas,
                "horas_por_nf": horas_por_nf,
                "total_nfs": total_nfs,
                "ticket_medio": ticket_medio,
                "custo_por_func": custo_por_func,
                "faturamento_bruto": faturamento_bruto,
                "impostos_sv": impostos_sv,
                "receita_liquida": receita_liquida,
                "incentivos": incentivos,
                "gastos_pessoal": gastos_pessoal,
                "outras_desp_diretas": outras_desp_diretas,
                "mc1": mc1,
                "mc1_pct_rl": mc1_pct_rl,
                "remuneracao_socios": remuneracao_socios,
                "mc2": mc2,
                "mc2_pct_rl": mc2_pct_rl,
                "outras_desp_adm": outras_desp_adm,
                "rateio_adm": rateio_adm,
                "honorarios_adm": honorarios_adm,
                "ebitda": ebitda,
                "ebitda_pct_rl": ebitda_pct_rl,
                "ebit": ebit,
                "lair": lair,
                "irpj_csll": irpj_csll,
                "lucro_liquido": lucro_liquido,
            }
        )

        ticket_ant = ticket_medio
        custo_func_ant = custo_por_func
        honorarios_ant = honorarios_adm

    df = pd.DataFrame(resultados)

    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
        "ociosidade",
        "inflacao_focus",
        "total_horas",
        "horas_alocadas",
        "horas_por_nf",
        "total_nfs",
        "ticket_medio",
        "custo_por_func",
        "faturamento_bruto",
        "impostos_sv",
        "receita_liquida",
        "incentivos",
        "gastos_pessoal",
        "outras_desp_diretas",
        "mc1",
        "mc1_pct_rl",
        "remuneracao_socios",
        "mc2",
        "mc2_pct_rl",
        "outras_desp_adm",
        "rateio_adm",
        "honorarios_adm",
        "ebitda",
        "ebitda_pct_rl",
        "ebit",
        "lair",
        "irpj_csll",
        "lucro_liquido",
    ]

    df = df[colunas_ordenadas]
    return df




def salvar_projecao_csv(
    df: pd.DataFrame,
    base_dir: Path | None = None,
    nome_arquivo: str = "projecao_fopm_brasil.csv",
) -> Path:
    """
    Salva o DataFrame de projeção no caminho padrão `projecoes/projecao_fopm_brasil.csv`
    abaixo do diretório base informado (por padrão, o diretório deste arquivo).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    destino_dir = base_dir / "projecoes"
    destino_dir.mkdir(parents=True, exist_ok=True)

    destino_arquivo = destino_dir / nome_arquivo
    df.to_csv(destino_arquivo, index=False)
    return destino_arquivo


def projetar_e_salvar(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "FOPM BRASIL",
) -> Path:
    """
    Atalho para projetar a DRE e salvar diretamente o CSV na pasta `projecoes/`.
    """
    df = projetar_dre_fopm_brasil(anos=anos, bu=bu)
    return salvar_projecao_csv(df)


if __name__ == "__main__":
    df_projecao = projetar_dre_fopm_brasil()
    caminho = salvar_projecao_csv(df_projecao)
    print(f"Projeção salva em: {caminho}")

