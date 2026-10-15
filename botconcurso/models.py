from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field


@dataclass
class Concurso:
    """Registro padronizado de um concurso, independente da fonte."""

    fonte: str                       # "pci", "fgv", ...
    orgao: str                       # "Câmara dos Deputados"
    cargos: list[str] = field(default_factory=list)
    vagas: str | None = None         # "184 vagas" / "Cadastro de reserva"
    salario_ate: str | None = None   # "R$ 32.070,88"
    escolaridade: str | None = None  # "Superior" / "Médio / Superior"
    inscricao_ate: str | None = None # ISO "2026-11-05"
    inscricao_texto: str | None = None  # texto original p/ exibir
    url: str = ""
    uf: str | None = None            # seção da fonte: "NACIONAL", "SÃO PAULO"...

    @property
    def id_unico(self) -> str:
        base = "|".join(
            [
                self.fonte,
                self.orgao.lower().strip(),
                ",".join(sorted(c.lower().strip() for c in self.cargos)),
                self.url.strip(),
            ]
        )
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Concurso":
        return cls(**d)
