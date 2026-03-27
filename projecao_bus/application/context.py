"""
Contexto imutável por execução de simulação (premissas-base + config + drivers).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from projecao_bus.base_values import BaseValues, default_base_values
from projecao_bus.config.year_config import YearConfig, get_active_year_config
from projecao_bus.drivers.fopm import FOPMDrivers, calcular_drivers_fopm_from_csv
from projecao_bus.premissas.defaults import (
    default_beta_ponderado_gabarito,
    default_custos_excl_pessoal_gabarito,
    default_data_science_custo_func_base,
    default_data_science_ticket_base,
    default_headcount_ds,
    default_headcount_fopm,
    default_honorarios_cfp_hist,
    default_inflacao_focus,
    default_ociosidade_fopm,
    default_pessoal_nao_alocado_adm,
    default_rl_consolidada_ref,
    default_selic_focus,
    func_novos_primeiro_ano_gabarito,
)
from projecao_bus.shared import extend_dict_years_float, extend_dict_years_int, merge_float_year_dict, merge_int_year_dict

DATA_SCIENCE_OCIOSIDADE_PADRAO = 0.15


@dataclass(frozen=True)
class SimulationContext:
    """Todas as séries e âncoras necessárias para rodar o motor sem estado global."""

    year_config: YearConfig
    base_values: BaseValues
    inflacao_focus: dict[int, float]
    selic_focus: dict[int, float]
    headcount_fopm: dict[int, int]
    ociosidade_fopm: dict[int, float]
    headcount_ds: dict[int, int]
    custos_excl_pessoal: dict[int, float]
    pessoal_nao_alocado_adm: dict[int, float]
    beta_ponderado_gabarito: dict[int, float]
    honorarios_cfp_hist: dict[int, float]
    rl_consolidada_ref: dict[int, float]
    data_science_ticket_base: float
    data_science_custo_func_base: float
    data_science_ociosidade_padrao: float
    func_novos_primeiro_ano: float
    fopm_drivers: FOPMDrivers

    @property
    def projected_years(self) -> tuple[int, ...]:
        return self.year_config.projected_years

    @property
    def primeiro_ano_projecao(self) -> int:
        return int(self.year_config.projected_years[0])

    def fator_cascata_ticket_data_science(self) -> float:
        """Cascata do ticket DS alinhada ao primeiro ano projetado (1 + inflação Focus)."""
        return 1.0 + self.inflacao_focus[self.primeiro_ano_projecao]


def build_simulation_context(
    *,
    year_config: YearConfig,
    base_values: BaseValues,
    premissas: dict[str, Any] | None = None,
    fopm_drivers: FOPMDrivers | None = None,
) -> SimulationContext:
    """
    Monta o contexto: defaults + extensão ao horizonte ativo + overrides do payload.
    """
    premissas = premissas or {}
    anos = list(year_config.projected_years)

    infl_over = premissas.get("inflacao_focus_por_ano") or premissas.get("macro", {}).get("inflacao_focus_por_ano")
    infl = merge_float_year_dict(default_inflacao_focus(), infl_over if isinstance(infl_over, dict) else None)
    infl = extend_dict_years_float(infl, anos)

    selic_over = premissas.get("selic_focus_por_ano") or premissas.get("macro", {}).get("selic_focus_por_ano")
    selic = merge_float_year_dict(default_selic_focus(), selic_over if isinstance(selic_over, dict) else None)
    selic = extend_dict_years_float(selic, anos)

    hc_fopm = merge_int_year_dict(default_headcount_fopm(), premissas.get("fopm", {}).get("headcount_por_ano"))
    hc_fopm = extend_dict_years_int(hc_fopm, anos)

    oc_fopm = merge_float_year_dict(
        default_ociosidade_fopm(),
        premissas.get("fopm", {}).get("ociosidade_por_ano"),
    )
    oc_fopm = extend_dict_years_float(oc_fopm, anos)

    hc_ds = merge_int_year_dict(default_headcount_ds(), premissas.get("data_science", {}).get("headcount_por_ano"))
    hc_ds = extend_dict_years_int(hc_ds, anos)

    custos_excl = extend_dict_years_float(dict(default_custos_excl_pessoal_gabarito()), anos)
    pess_nao = extend_dict_years_float(dict(default_pessoal_nao_alocado_adm()), anos)
    beta_bab = extend_dict_years_float(dict(default_beta_ponderado_gabarito()), anos)

    honorarios_hist = dict(default_honorarios_cfp_hist())
    rl_ref = extend_dict_years_float(dict(default_rl_consolidada_ref()), anos)

    ds_block = premissas.get("data_science", {}) or {}
    ticket_ds = float(ds_block["ticket_base"]) if ds_block.get("ticket_base") is not None else default_data_science_ticket_base()
    custo_ds = float(ds_block["custo_func_base"]) if ds_block.get("custo_func_base") is not None else default_data_science_custo_func_base()
    ocios_ds = float(ds_block["ociosidade_padrao"]) if ds_block.get("ociosidade_padrao") is not None else DATA_SCIENCE_OCIOSIDADE_PADRAO

    dcf_block = premissas.get("dcf", {}) or {}
    fn_primeiro = float(dcf_block["func_novos_primeiro_ano"]) if dcf_block.get("func_novos_primeiro_ano") is not None else func_novos_primeiro_ano_gabarito()

    drivers = fopm_drivers if fopm_drivers is not None else calcular_drivers_fopm_from_csv()

    return SimulationContext(
        year_config=year_config,
        base_values=base_values,
        inflacao_focus=infl,
        selic_focus=selic,
        headcount_fopm=hc_fopm,
        ociosidade_fopm=oc_fopm,
        headcount_ds=hc_ds,
        custos_excl_pessoal=custos_excl,
        pessoal_nao_alocado_adm=pess_nao,
        beta_ponderado_gabarito=beta_bab,
        honorarios_cfp_hist=honorarios_hist,
        rl_consolidada_ref=rl_ref,
        data_science_ticket_base=ticket_ds,
        data_science_custo_func_base=custo_ds,
        data_science_ociosidade_padrao=ocios_ds,
        func_novos_primeiro_ano=fn_primeiro,
        fopm_drivers=drivers,
    )


def default_simulation_context(premissas: dict[str, Any] | None = None) -> SimulationContext:
    """Contexto padrão para execuções isoladas (CLI/testes) usando year_config ativo."""
    return build_simulation_context(
        year_config=get_active_year_config(),
        base_values=default_base_values(),
        premissas=premissas,
    )
