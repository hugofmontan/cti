from typing import Any, Iterable

from .premissas.defaults import default_inflacao_focus

ALIQUOTA_ISV = 0.1743

# Template somente leitura para compatibilidade legada (use SimulationContext em código novo).
INFLACAO_FOCUS = default_inflacao_focus()


def sort_years_non_empty(anos: Iterable[int]) -> list[int]:
    anos_list = sorted(int(y) for y in anos)
    if not anos_list:
        raise ValueError("Lista de anos não pode ser vazia.")
    return anos_list


def _validar_anos(anos: Iterable[int]) -> list[int]:
    """
    Legado: ordena anos. A extensão de inflação é feita no SimulationContext.
    Mantido para chamadas que ainda não recebem ctx.
    """
    return sort_years_non_empty(anos)


def extend_dict_years_float(d: dict[int, float], years: Iterable[int]) -> dict[int, float]:
    """Nova cópia: garante todas as chaves em `years` repetindo o último valor conhecido."""
    if not d:
        raise ValueError("dict de premissas não pode ser vazio.")
    out = dict(d)
    last_key = max(out.keys())
    last_val = out[last_key]
    for y in years:
        iy = int(y)
        if iy not in out:
            out[iy] = float(last_val)
    return out


def extend_dict_years_int(d: dict[int, int], years: Iterable[int]) -> dict[int, int]:
    if not d:
        raise ValueError("dict de premissas não pode ser vazio.")
    out = dict(d)
    last_key = max(out.keys())
    last_val = out[last_key]
    for y in years:
        iy = int(y)
        if iy not in out:
            out[iy] = int(last_val)
    return out


def merge_float_year_dict(
    default: dict[int, float],
    override: dict[str, Any] | dict[int, Any] | None,
) -> dict[int, float]:
    out = dict(default)
    if not override:
        return out
    for k, v in override.items():
        out[int(k)] = float(v)
    return out


def merge_int_year_dict(
    default: dict[int, int],
    override: dict[str, Any] | dict[int, Any] | None,
) -> dict[int, int]:
    out = dict(default)
    if not override:
        return out
    for k, v in override.items():
        out[int(k)] = int(v)
    return out


def ensure_years_in_dict_inplace(d: dict[int, float], years: Iterable[int]) -> None:
    """
    Legado in-place — evite em código novo; use extend_dict_years_float.
    """
    if not d:
        raise ValueError("dict de premissas nao pode ser vazio.")
    last_key = max(d.keys())
    last_val = d[last_key]
    for y in years:
        iy = int(y)
        if iy not in d:
            d[iy] = float(last_val)


from .io.csv_writer import salvar_projecao_csv
