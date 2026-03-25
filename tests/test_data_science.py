import math

from projecao_bus.data_science import projetar_dre_data_science, total_projetos_de_capacidade


def test_total_projetos_de_capacidade_padrao() -> None:
    assert total_projetos_de_capacidade(5, 0.15) == 2
    assert total_projetos_de_capacidade(8, 0.15) == 3
    assert total_projetos_de_capacidade(10, 0.15) == 4
    assert total_projetos_de_capacidade(15, 0.15) == 6
    assert total_projetos_de_capacidade(17, 0.15) == 7


def test_total_projetos_zero_se_sem_pessoal() -> None:
    assert total_projetos_de_capacidade(0, 0.15) == 0


def test_projetar_dre_deriva_projetos_do_headcount() -> None:
    df = projetar_dre_data_science()
    for _, row in df.iterrows():
        ano = int(row["ano"])
        n = int(row["n_funcionarios"])
        esperado = total_projetos_de_capacidade(n, 0.15)
        assert int(row["total_projetos"]) == esperado
        cap = float(row["capacidade_projetos"])
        assert int(row["total_projetos"]) == max(0, int(math.floor(cap)))


def test_ticket_e_fb_coerentes_com_projetos() -> None:
    df = projetar_dre_data_science()
    row = df[df["ano"] == 2026].iloc[0]
    tp = int(row["total_projetos"])
    tm = float(row["ticket_medio"])
    assert abs(float(row["faturamento_bruto"]) - tp * tm) < 0.01
