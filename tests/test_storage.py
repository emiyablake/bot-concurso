from src.models import Concurso
from src.storage import Estado


def _c(orgao, cargo="Analista de Sistemas"):
    return Concurso(fonte="pci", orgao=orgao, cargos=[cargo], url=f"https://x/{orgao}")


def test_primeira_execucao_tudo_e_novo(tmp_path):
    est = Estado(tmp_path / "estado.json")
    itens = [_c("A"), _c("B")]
    assert est.novos(itens) == itens


def test_segunda_execucao_nada_e_novo(tmp_path):
    est = Estado(tmp_path / "estado.json")
    itens = [_c("A"), _c("B")]
    est.registrar(itens)
    est.salvar()

    est2 = Estado(tmp_path / "estado.json")
    assert est2.novos(itens) == []


def test_soh_novos_aparecem(tmp_path):
    p = tmp_path / "estado.json"
    est = Estado(p)
    est.registrar([_c("A")])
    est.salvar()

    est2 = Estado(p)
    novos = est2.novos([_c("A"), _c("B")])
    assert [c.orgao for c in novos] == ["B"]


def test_persistencia_redonda(tmp_path):
    p = tmp_path / "estado.json"
    est = Estado(p)
    est.registrar([_c("A")])
    est.salvar()
    est2 = Estado(p)
    assert len(est2) == 1
    assert est2._itens[next(iter(est2._itens))]["orgao"] == "A"
