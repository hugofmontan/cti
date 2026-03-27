"""Valores-base do plano (factories retornam cópias novas a cada chamada)."""

from __future__ import annotations

from ..dcf.constants import RATIO_FORNECEDORES_CUSTOS_EXCL_GABARITO

# --- Macro ---


def default_inflacao_focus() -> dict[int, float]:
    return {
        2026: 0.0397,
        2027: 0.0380,
        2028: 0.0350,
        2029: 0.0350,
        2030: 0.0350,
    }


def default_selic_focus() -> dict[int, float]:
    return {
        2026: 0.1213,
        2027: 0.1050,
        2028: 0.1000,
        2029: 0.0950,
        2030: 0.1000,
    }


# --- FOPM ---


def default_headcount_fopm() -> dict[int, int]:
    return {
        2026: 46,
        2027: 47,
        2028: 48,
        2029: 49,
        2030: 51,
    }


def default_ociosidade_fopm() -> dict[int, float]:
    return {
        2026: 0.245,
        2027: 0.24,
        2028: 0.23,
        2029: 0.225,
        2030: 0.21,
    }


# --- Data Science ---


def default_headcount_ds() -> dict[int, int]:
    return {
        2026: 5,
        2027: 8,
        2028: 10,
        2029: 15,
        2030: 17,
    }


def default_data_science_ticket_base() -> float:
    return 1_300_000.0


def default_data_science_custo_func_base() -> float:
    return 153_654.72


# --- Administrativa / consolidado ---


def default_rl_consolidada_ref() -> dict[int, float]:
    return {
        2026: 46_939_343.0,
        2027: 51_109_974.0,
        2028: 55_569_432.0,
        2029: 60_162_741.0,
        2030: 67_191_035.0,
    }


def default_honorarios_cfp_hist() -> dict[int, float]:
    return {
        2022: 2_280_000.0,
        2023: 2_451_000.0,
        2024: 2_508_000.0,
        2025: 2_508_000.0,
    }


# --- DCF (gabaritos operacionais) ---


def default_custos_excl_pessoal_gabarito() -> dict[int, float]:
    r = RATIO_FORNECEDORES_CUSTOS_EXCL_GABARITO
    return {
        2026: 38_456 / r,
        2027: 46_180 / r,
        2028: 58_476 / r,
        2029: 63_351 / r,
        2030: 68_767 / r,
    }


def default_pessoal_nao_alocado_adm() -> dict[int, float]:
    return {
        2026: 1_715_347.35,
        2027: 1_799_279.13,
        2028: 1_840_241.44,
        2029: 1_920_439.47,
        2030: 1_949_520.41,
    }


def default_beta_ponderado_gabarito() -> dict[int, float]:
    return {
        2025: 0.9725,
        2026: 0.9716,
        2027: 0.9751,
        2028: 0.9784,
        2029: 0.9814,
        2030: 0.9869,
    }


def func_novos_primeiro_ano_gabarito() -> float:
    """Funcionários novos no primeiro ano projetado (gabarito BP vs headcount CSV)."""
    return 26.019
