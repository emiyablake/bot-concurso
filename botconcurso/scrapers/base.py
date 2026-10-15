from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Concurso


class ScraperBase(ABC):
    """Contrato comum de todas as fontes de concursos."""

    fonte: str = ""

    @abstractmethod
    def coletar(self) -> list[Concurso]:
        """Busca os concursos na fonte e retorna registros padronizados."""
