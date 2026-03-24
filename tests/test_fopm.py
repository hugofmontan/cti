from projecao_bus.fopm import projetar_dre_fopm_brasil


def test_projetar_dre_fopm_colunas_essenciais() -> None:
    df = projetar_dre_fopm_brasil()
    assert not df.empty
    assert {"ano", "faturamento_bruto", "receita_liquida", "ebitda", "lucro_liquido"}.issubset(
        df.columns
    )
