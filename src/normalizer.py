"""Normalizacao de campos entre fontes."""

from __future__ import annotations

import re

from .models import Concurso

_RE_DATA = re.compile(r"(\d{2}/\d{2}/\d{4})")


def data_para_iso(texto: str | None) -> str | None:
    """'16/10/2026' -> '2026-10-16'. Em ranges ('17/10 a 05/11/2026'), usa a ultima data."""
    if not texto:
        return None
    datas = _RE_DATA.findall(texto)
    if not datas:
        return None
    dia, mes, ano = datas[-1].split("/")
    return f"{ano}-{mes}-{dia}"


def normalizar(concurso: Concurso) -> Concurso:
    concurso.inscricao_ate = data_para_iso(concurso.inscricao_texto)
    concurso.orgao = " ".join(concurso.orgao.split())
    concurso.cargos = [" ".join(c.split()) for c in concurso.cargos if c.strip()]
    return concurso


def normalizar_todos(concursos: list[Concurso]) -> list[Concurso]:
    return [normalizar(c) for c in concursos]
