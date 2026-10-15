"""Scraper do PCI Concursos (https://www.pciconcursos.com.br/concursos/).

Estrutura da pagina (HTML estatico):
  div.ua > div.uf          -> cabecalho de secao (NACIONAL, SAO PAULO, ...)
  div.na[data-url]         -> um concurso
    div.ca > a             -> nome do orgao + link
    div.cd                 -> "<vagas> ate <salario><br><span><cargos><br><span><escolaridade>"
    div.ce > span          -> data(s) de inscricao
"""

from __future__ import annotations

import re
import time

import requests
from bs4 import BeautifulSoup, NavigableString

from ..models import Concurso
from .base import ScraperBase

URL_LISTAGEM = "https://www.pciconcursos.com.br/concursos/"

_RE_VAGAS_SALARIO = re.compile(r"^(?P<vagas>.*?)\s+até\s+(?P<salario>R\$\s*[\d.,]+)$")


class PciScraper(ScraperBase):
    fonte = "pci"

    def __init__(self, html: str | None = None, user_agent: str = "botConcurso/0.1", delay: float = 1.0):
        # html: modo fixture (testes) — nao faz requisicao de rede
        self._html = html
        self._user_agent = user_agent
        self._delay = delay

    def coletar(self) -> list[Concurso]:
        html = self._html if self._html is not None else self._baixar()
        return self._parse(html)

    def _baixar(self) -> str:
        resp = requests.get(
            URL_LISTAGEM,
            headers={"User-Agent": self._user_agent},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text

    def _parse(self, html: str) -> list[Concurso]:
        soup = BeautifulSoup(html, "lxml")
        resultados: list[Concurso] = []
        secao_atual: str | None = None

        for el in soup.select("div.ua, div.na"):
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
        a = el.find("div", class_="ca").find("a") if el.find("div", class_="ca") else None
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
