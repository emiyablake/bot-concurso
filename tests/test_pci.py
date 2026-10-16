from pathlib import Path

import pytest

from src.scrapers import PciScraper

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


def test_coleta_containers_da_e_ea(concursos):
    # div.da (entradas com apostila) tambem devem ser coletadas;
    # SETEC Campinas com 'Vários Cargos' so aparece como div.da
    setec = [c for c in concursos if "SETEC" in c.orgao]
    assert any("Campinas" in c.orgao for c in setec)
    campinas = next(c for c in setec if "Campinas" in c.orgao)
    assert campinas.cargos == ["Vários Cargos"]
    assert campinas.vagas == "39 vagas"
    assert campinas.salario_ate == "R$ 10.428,05"


def test_extrair_cargos_da_noticia():
    from pathlib import Path

    html = (Path(__file__).parent / "fixtures" / "pci_noticia_setec.html").read_text(encoding="utf-8")
    cargos = PciScraper.extrair_cargos_noticia(html)
    assert "Analista Técnico (Informática)" in cargos
    assert "Agente Administrativo" in cargos
    assert "Engenheiro Civil" in cargos


def test_enriquecer_usa_cache_sem_rede(concursos):
    setec = next(c for c in concursos if "Campinas" in c.orgao)
    setec.cargos = ["Vários Cargos"]  # fixture compartilhada: reseta o estado
    chamadas = []

    def buscar_errada(url):
        chamadas.append(url)
        raise AssertionError("nao deveria chamar a rede com cache disponivel")

    scraper = PciScraper(html="<html/>")  # modo fixture, sem rede
    scraper.enriquecer_varios_cargos(
        [setec], ja_conhecidos=lambda url: ["Analista Técnico (Informática)"], buscar_html=buscar_errada
    )
    assert setec.cargos == ["Analista Técnico (Informática)"]
    assert chamadas == []


def test_enriquecer_busca_detalhe_para_novo(concursos):
    setec = next(c for c in concursos if "Campinas" in c.orgao)
    setec.cargos = ["Vários Cargos"]  # fixture compartilhada: reseta o estado
    from pathlib import Path

    noticia = (Path(__file__).parent / "fixtures" / "pci_noticia_setec.html").read_text(encoding="utf-8")
    scraper = PciScraper(html="<html/>")
    enriquecidos = scraper.enriquecer_varios_cargos(
        [setec], ja_conhecidos=lambda url: None, buscar_html=lambda url: noticia
    )
    assert setec in enriquecidos
    assert "Analista Técnico (Informática)" in setec.cargos
