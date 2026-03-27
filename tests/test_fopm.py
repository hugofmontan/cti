from projecao_bus.fopm import projetar_dre_fopm_brasil
from projecao_bus.year_config import get_projected_years


def test_projetar_dre_fopm_colunas_essenciais() -> None:
    df = projetar_dre_fopm_brasil()
    assert not df.empty
    assert {"ano", "faturamento_bruto", "receita_liquida", "ebitda", "lucro_liquido"}.issubset(
        df.columns
    )
    assert df["ano"].tolist() == list(get_projected_years())
