"""Filtro de concursos da area de tecnologia por keywords."""

from __future__ import annotations

import unicodedata

from .config import KEYWORDS_TI_PADRAO
from .models import Concurso


def _sem_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def eh_da_area(concurso: Concurso, keywords: list[str] | None = None) -> bool:
    keywords = keywords if keywords is not None else KEYWORDS_TI_PADRAO
    alvo = _sem_acentos(f"{concurso.orgao} {' '.join(concurso.cargos)}")
    return any(_sem_acentos(k) in alvo for k in keywords)


def filtrar(concursos: list[Concurso], keywords: list[str] | None = None) -> list[Concurso]:
    return [c for c in concursos if eh_da_area(c, keywords)]
