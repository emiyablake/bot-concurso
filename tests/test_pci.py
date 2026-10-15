from pathlib import Path

import pytest

from botconcurso.scrapers import PciScraper

FIXTURE = Path(__file__).parent / "fixtures" / "pci_concursos.html"


@pytest.fixture(scope="module")
def concursos():
    html = FIXTURE.read_text(encoding="utf-8")
    return PciScraper(html=html).coletar()


def test_fixture_existe():
    assert FIXTURE.exists(), "rode: curl https://www.pciconcursos.com.br/concursos/ -o tests/fixtures/pci_concursos.html"


def test_quantidade_minima(concursos):
    # a listagem real tem centenas de concursos; menos que 50 indica layout quebrado
    assert len(concursos) > 50


def test_camara_dos_deputados(concursos):
    camara = next(c for c in concursos if c.orgao == "Câmara dos Deputados")
    assert camara.vagas == "184 vagas"
    assert camara.salario_ate == "R$ 32.070,88"
    assert "Analista Legislativo" in camara.cargos
    assert camara.escolaridade == "Superior"
    assert camara.inscricao_texto == "17/11/2026"
    assert camara.uf == "NACIONAL"
    assert camara.url.startswith("https://www.pciconcursos.com.br/")


def test_cadastro_de_reserva(concursos):
    agsus = next(c for c in concursos if "AgSUS" in c.orgao)
    assert agsus.vagas == "Cadastro de reserva"
    assert agsus.cargos == ["Psicólogo"]


def test_todos_tem_orgao_url_e_fonte(concursos):
    for c in concursos:
        assert c.orgao
        assert c.url.startswith("http")
        assert c.fonte == "pci"
        assert c.id_unico


def test_ids_unicos(concursos):
    ids = [c.id_unico for c in concursos]
    assert len(ids) == len(set(ids))
