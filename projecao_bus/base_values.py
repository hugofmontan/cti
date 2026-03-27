"""

Base-year parameters usadas pelo motor de projeção/DCF.



Âncoras vêm de `default_base_values()` ou de `extract_base_year_values` conforme o upload.

"""



from __future__ import annotations



from dataclasses import dataclass





@dataclass(frozen=True)

class BaseValues:

    base_year: int



    caixa_base: float

    imobilizado_base: float

    depr_acum_base: float

    ncg_base: float

    ac_op_base: float

    pc_op_base: float



    fb_ams_base: float

    ticket_ams_base: float

    custo_func_ams_base: float

    horas_por_nf_ams: float



    fb_renovacao_base: float

    custo_func_renovacao_base: float



    fb_venda_sw_base: float

    custo_func_venda_sw_base: float





def default_base_values() -> BaseValues:

    """Defaults atuais (base_year = último ano histórico padrão do pacote)."""

    return BaseValues(

        base_year=2025,

        caixa_base=2_291_962.0,

        imobilizado_base=2_445_435.0,

        depr_acum_base=-1_561_883.0,

        ncg_base=4_514_000.0,

        ac_op_base=7_477_000.0,

        pc_op_base=2_963_000.0,

        fb_ams_base=15_293_573.83,

        ticket_ams_base=18_246.57,

        custo_func_ams_base=145_370.0,

        horas_por_nf_ams=105.363,

        fb_renovacao_base=3_385_238.39,

        custo_func_renovacao_base=305_489.82 / 3.0,

        fb_venda_sw_base=7_722_610.43,

        custo_func_venda_sw_base=169_393.04,

    )





def get_active_base_values() -> BaseValues:

    """Legado: retorna defaults estáticos. Preferir `SimulationContext.base_values`."""

    return default_base_values()





def set_active_base_values(values: BaseValues) -> None:

    """Legado sem estado global — no-op mantido para compatibilidade de chamadas."""

    _ = values





def reset_base_values() -> None:

    """Legado sem estado global — no-op mantido para compatibilidade de chamadas."""

    return None


