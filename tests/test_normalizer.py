from botconcurso.models import Concurso
from botconcurso.normalizer import data_para_iso, normalizar


def test_data_simples():
    assert data_para_iso("16/10/2026") == "2026-10-16"


def test_data_range_usa_ultima():
    assert data_para_iso("17/10 a 05/11/2026") == "2026-11-05"


def test_data_com_rotulo():
    assert data_para_iso("Prorrogado até 15/10/2026") == "2026-10-15"


def test_data_invalida():
    assert data_para_iso("a definir") is None
    assert data_para_iso(None) is None


def test_normalizar_preenche_iso_e_limpa():
    c = Concurso(
        fonte="pci",
        orgao="  Câmara   dos Deputados ",
        cargos=[" Analista  Legislativo "],
        inscricao_texto="17/11/2026",
    )
    normalizar(c)
    assert c.inscricao_ate == "2026-11-17"
    assert c.orgao == "Câmara dos Deputados"
    assert c.cargos == ["Analista Legislativo"]
