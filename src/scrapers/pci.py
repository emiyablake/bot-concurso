"""Scraper do PCI Concursos (https://www.pciconcursos.com.br/concursos/).

Estrutura da pagina (HTML estatico):
  div.ua > div.uf          -> cabecalho de secao (NACIONAL, SAO PAULO, ...)
  div.na / div.da / div.ea -> um concurso (tres containers equivalentes;
                              'da'/'ea' sao entradas com apostila/vinculo)
    div.ca > a             -> nome do orgao + link
    div.cc                 -> sigla da UF (secao estadual)
    div.cd                 -> "<vagas> ate <salario><br><span><cargos><br><span><escolaridade>"
    div.ce > span          -> data(s) de inscricao

Quando a listagem informa "Vários Cargos", a pagina da noticia
(/noticias/<slug>) lista os cargos reais em <li>Cargo (N vagas + CR)</li>.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable

import requests
from bs4 import BeautifulSoup, NavigableString

from ..models import Concurso
from .base import ScraperBase

log = logging.getLogger(__name__)

URL_LISTAGEM = "https://www.pciconcursos.com.br/concursos/"

_RE_VAGAS_SALARIO = re.compile(r"^(?P<vagas>.*?)\s+até\s+(?P<salario>R\$\s*[\d.,]+)$")
# "<cargo> (1 vaga + CR)" / "<cargo> (CR)" — sufixo de quantidade no fim do <li>
_RE_CARGO_LI = re.compile(r"^(?P<cargo>.+?)\s*\((?:\d[^)]*|CR)\)$", re.IGNORECASE)

CONTAINERS_CONCURSO = ("na", "da", "ea")


class PciScraper(ScraperBase):
    fonte = "pci"

    def __init__(self, html: str | None = None, user_agent: str = "botConcurso/0.1", delay: float = 1.0):
        # html: modo fixture (testes) — nao faz requisicao de rede
        self._html = html
        self._user_agent = user_agent
        self._delay = delay

    def coletar(self) -> list[Concurso]:
        html = self._html if self._html is not None else self._baixar(URL_LISTAGEM)
        return self._parse(html)

    def enriquecer_varios_cargos(
        self,
        concursos: list[Concurso],
        ja_conhecidos: Callable[[str], list[str] | None],
        buscar_html: Callable[[str], str] | None = None,
    ) -> list[Concurso]:
        """Busca os cargos reais nas paginas de noticia dos itens 'Vários Cargos'.

        ja_conhecidos(url) devolve os cargos ja guardados no estado (cache entre
        execucoes) — assim so fazemos requisicoes para entradas novas.
        Retorna a lista dos concursos efetivamente enriquecidos nesta execucao.
        """
        buscar_html = buscar_html or (None if self._html is not None else self._baixar)
        enriquecidos: list[Concurso] = []
        for c in concursos:
            if not _eh_varios_cargos(c):
                continue
            cache = ja_conhecidos(c.url)
            if cache:
                c.cargos = cache
                continue
            if buscar_html is None:
                continue  # modo fixture/testes
            try:
                cargos = self.extrair_cargos_noticia(buscar_html(c.url))
                if cargos:
                    c.cargos = cargos
                    enriquecidos.append(c)
            except Exception:
                log.exception("Falha ao enriquecer %s — mantendo 'Vários Cargos'", c.url)
            time.sleep(self._delay)
        return enriquecidos

    def _baixar(self, url: str) -> str:
        resp = requests.get(url, headers={"User-Agent": self._user_agent}, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def extrair_cargos_noticia(html: str) -> list[str]:
        """Extrai cargos de <li>Cargo (N vagas + CR)</li> na pagina da noticia."""
        soup = BeautifulSoup(html, "lxml")
        cargos: list[str] = []
        for li in soup.select("li"):
            texto = " ".join(li.get_text(" ", strip=True).split())
            m = _RE_CARGO_LI.match(texto)
            if m:
                cargo = m.group("cargo").strip()
                if cargo and cargo not in cargos:
                    cargos.append(cargo)
        return cargos

    def _parse(self, html: str) -> list[Concurso]:
        soup = BeautifulSoup(html, "lxml")
        seletor = ", ".join(f"div.{c}" for c in ("ua",) + CONTAINERS_CONCURSO)
        resultados: list[Concurso] = []
        secao_atual: str | None = None

        for el in soup.select(seletor):
            classes = el.get("class", [])
            if "ua" in classes:
                uf_el = el.find("div", class_="uf")
                secao_atual = uf_el.get_text(strip=True) if uf_el else None
                continue
            concurso = self._parse_item(el, secao_atual)
            if concurso:
                resultados.append(concurso)
        return resultados

    def _parse_item(self, el, secao: str | None) -> Concurso | None:
        ca = el.find("div", class_="ca")
        a = ca.find("a") if ca else None
        if not a:
            return None

        vagas, salario = self._vagas_salario(el.find("div", class_="cd"))
        cargos, escolaridade = self._cargos_escolaridade(el.find("div", class_="cd"))
        inscricao_texto = self._inscricao(el.find("div", class_="ce"))

        return Concurso(
            fonte=self.fonte,
            orgao=a.get_text(strip=True),
            cargos=cargos,
            vagas=vagas,
            salario_ate=salario,
            escolaridade=escolaridade,
            inscricao_texto=inscricao_texto,
            url=(a.get("href") or el.get("data-url") or "").strip(),
            uf=secao,
        )

    @staticmethod
    def _vagas_salario(cd) -> tuple[str | None, str | None]:
        if cd is None:
            return None, None
        linha = ""
        for node in cd.children:
            if isinstance(node, NavigableString) and node.strip():
                linha = node.strip()
                break
        if not linha or linha == "\xa0":
            return None, None
        m = _RE_VAGAS_SALARIO.match(linha)
        if m:
            vagas = m.group("vagas").strip() or None
            return vagas, m.group("salario").strip()
        return linha, None

    @staticmethod
    def _cargos_escolaridade(cd) -> tuple[list[str], str | None]:
        if cd is None:
            return [], None
        outer = cd.find("span")
        if outer is None:
            return [], None
        inner = outer.find("span")
        escolaridade = None
        if inner is not None:
            escolaridade = " / ".join(inner.stripped_strings) or None
            inner.decompose()
        texto = ", ".join(outer.stripped_strings)
        cargos = [c.strip() for c in texto.split(",") if c.strip()]
        return cargos, escolaridade

    @staticmethod
    def _inscricao(ce) -> str | None:
        if ce is None:
            return None
        return " ".join(ce.stripped_strings) or None


def _eh_varios_cargos(c: Concurso) -> bool:
    return len(c.cargos) == 1 and c.cargos[0].strip().lower() == "vários cargos"
