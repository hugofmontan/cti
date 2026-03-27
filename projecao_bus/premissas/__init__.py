"""Factories de premissas-base (copias mutáveis para compor o SimulationContext)."""

from .defaults import (
    default_beta_ponderado_gabarito,
    default_custos_excl_pessoal_gabarito,
    default_headcount_ds,
    default_headcount_fopm,
    default_honorarios_cfp_hist,
    default_inflacao_focus,
    default_ociosidade_fopm,
    default_pessoal_nao_alocado_adm,
    default_rl_consolidada_ref,
    default_selic_focus,
    func_novos_primeiro_ano_gabarito,
    default_data_science_ticket_base,
    default_data_science_custo_func_base,
)

__all__ = [
    "default_beta_ponderado_gabarito",
    "default_custos_excl_pessoal_gabarito",
    "default_headcount_ds",
    "default_headcount_fopm",
    "default_honorarios_cfp_hist",
    "default_inflacao_focus",
    "default_ociosidade_fopm",
    "default_pessoal_nao_alocado_adm",
    "default_rl_consolidada_ref",
    "default_selic_focus",
    "func_novos_primeiro_ano_gabarito",
    "default_data_science_ticket_base",
    "default_data_science_custo_func_base",
]
