"""Envio de e-mail via SMTP (Gmail por padrao; qualquer provedor SMTP funciona)."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from .config import Config

log = logging.getLogger(__name__)


def enviar(cfg: Config, assunto: str, html: str) -> None:
    if not cfg.email_configurado:
        raise RuntimeError(
            "E-mail nao configurado. Defina SMTP_USER, SMTP_PASS e EMAIL_PARA."
        )
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = assunto
    msg["From"] = formataddr(("BotConcurso", cfg.email_de or cfg.smtp_user))
    msg["To"] = cfg.email_para

    with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=30) as smtp:
        smtp.login(cfg.smtp_user, cfg.smtp_pass)
        smtp.send_message(msg)
    log.info("E-mail enviado para %s", cfg.email_para)
