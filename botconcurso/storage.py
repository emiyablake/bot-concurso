"""Estado persistente dos concursos ja reportados (arquivo JSON versionado)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Concurso


class Estado:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._itens: dict[str, dict] = {}
        self.carregar()

    def carregar(self) -> None:
        if self.path.exists():
            dados = json.loads(self.path.read_text(encoding="utf-8"))
            self._itens = dados.get("itens", {})
        else:
            self._itens = {}

    def novos(self, concursos: list[Concurso]) -> list[Concurso]:
        return [c for c in concursos if c.id_unico not in self._itens]

    def registrar(self, concursos: list[Concurso]) -> None:
        hoje = date.today().isoformat()
        for c in concursos:
            d = c.to_dict()
            d["id_unico"] = c.id_unico
            d["visto_em"] = hoje
            self._itens[c.id_unico] = d

    def salvar(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"versao": 1, "total": len(self._itens), "itens": self._itens}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def __len__(self) -> int:
        return len(self._itens)
