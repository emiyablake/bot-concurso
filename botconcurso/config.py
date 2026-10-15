"""Configuração por variáveis de ambiente (locais) ou secrets (GitHub Actions)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


KEYWORDS_TI_PADRAO = [
    "desenvolvedor",
    "desenvolvimento de sistemas",
    "desenvolvimento de software",
    "analista de sistemas",
    "analista de ti",
    "analista de tecnologia",
    "engenheiro de software",
    "programador",
    "técnico de informática",
    "técnico em informática",
    "técnico de tecnologia da informação",
    "suporte técnico",
    "infraestrutura",
    "redes",
    "segurança da informação",
    "dados",
    "ciência de dados",
    "sistemas de informação",
    "computação",
]


def _raiz() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class Config:
    estado_path: Path = field(default_factory=lambda: _raiz() / "data" / "estado.json")
    user_agent: str = "botConcurso/0.1 (+indexador de concursos de TI; contato via repositorio)"
    delay_entre_requests: float = 1.0  # segundos; scraping educado

    # e-mail (SMTP genérico; Gmail por padrao)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    email_de: str = ""
    email_para: str = ""

    # filtro de area; sobrescrever com KEYWORDS_TI separadas por virgula
    keywords_ti: list[str] = field(default_factory=lambda: list(KEYWORDS_TI_PADRAO))

    @staticmethod
    def _env(nome: str, padrao: str = "") -> str:
        # variavel definida mas vazia (ex.: secret nao criado no Actions)
        # deve cair no padrao, nao sobrescreve-lo
        valor = os.environ.get(nome, "")
        return valor.strip() if valor.strip() else padrao

    @classmethod
    def do_ambiente(cls) -> "Config":
        cfg = cls()
        cfg.smtp_user = cls._env("SMTP_USER")
        cfg.smtp_pass = cls._env("SMTP_PASS")
        cfg.email_de = cls._env("EMAIL_DE", cfg.smtp_user)
        cfg.email_para = cls._env("EMAIL_PARA")
        cfg.smtp_host = cls._env("SMTP_HOST", cfg.smtp_host)
        cfg.smtp_port = int(cls._env("SMTP_PORT", str(cfg.smtp_port)))
        if cls._env("ESTADO_PATH"):
            cfg.estado_path = Path(cls._env("ESTADO_PATH"))
        kw = cls._env("KEYWORDS_TI")
        if kw:
            cfg.keywords_ti = [k.strip() for k in kw.split(",") if k.strip()]
        return cfg

    @property
    def email_configurado(self) -> bool:
        return bool(self.smtp_pass and self.email_para)
