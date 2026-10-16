from src.filter import eh_da_area, filtrar
from src.models import Concurso


def _c(orgao, cargos):
    return Concurso(fonte="pci", orgao=orgao, cargos=cargos, url="https://exemplo")


def test_aceita_analista_de_sistemas():
    assert eh_da_area(_c("Tribunal de Justiça", ["Analista de Sistemas"]))


def test_aceita_desenvolvedor_sem_acento():
    assert eh_da_area(_c("Assembleia Legislativa", ["Analista Legislativo - Desenvolvedor"]))


def test_aceita_tecnico_informatica():
    assert eh_da_area(_c("Prefeitura", ["Técnico em Informática"]))


def test_aceita_analista_tecnico_informatica():
    # formato do PCI: area entre parenteses
    assert eh_da_area(_c("Prefeitura", ["Analista Técnico (Informática)"]))


def test_rejeita_instrutor_de_informatica():
    # 'instrutor/professor de informatica' nao e vaga de TI
    assert not eh_da_area(_c("Escola Técnica", ["Instrutor de Informática"]))
    assert not eh_da_area(_c("Prefeitura", ["Professor de Informática Habilitado"]))


def test_rejeita_cargos_nao_ti():
    assert not eh_da_area(_c("Prefeitura", ["Professor de Educação Básica", "Pedagogo"]))


def test_rejeita_orgao_sem_relacao_com_cargos_ti():
    assert not eh_da_area(_c("Câmara Municipal", ["Assistente Legislativo", "Contador"]))


def test_filtrar_mantem_so_ti():
    concursos = [
        _c("IBGE", ["Analista de Sistemas"]),
        _c("Prefeitura", ["Enfermeiro"]),
        _c("TJ", ["Analista Judiciário - Desenvolvedor de Sistemas"]),
    ]
    resultado = filtrar(concursos)
    assert len(resultado) == 2
    assert all("Enfermeiro" not in c.cargos for c in resultado)


def test_keywords_customizaveis():
    c = _c("Prefeitura", ["Engenheiro Civil"])
    assert not eh_da_area(c)
    assert eh_da_area(c, keywords=["engenheiro civil"])
