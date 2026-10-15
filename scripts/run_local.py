"""Orquestrador do pipeline: coletar -> normalizar -> filtrar -> comparar -> reportar.

Uso local:
    python scripts/run_local.py

E-mail so e enviado se SMTP_PASS e EMAIL_PARA estiverem definidos;
caso contrario o relatorio e apenas impresso no console.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from botconcurso.config import Config
from botconcurso.filter import filtrar
from botconcurso.mailer import enviar
from botconcurso.normalizer import normalizar_todos
from botconcurso.report import gerar_html
from botconcurso.scrapers import PciScraper
from botconcurso.storage import Estado

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("botconcurso")


def main() -> int:
    cfg = Config.do_ambiente()
    estado = Estado(cfg.estado_path)

    log.info("Coletando concursos...")
    scrapers = [PciScraper(user_agent=cfg.user_agent, delay=cfg.delay_entre_requests)]
    coletados = []
    for s in scrapers:
        try:
            itens = s.coletar()
            log.info("Fonte %s: %d concursos", s.fonte, len(itens))
            coletados.extend(itens)
        except Exception:
            log.exception("Falha ao coletar da fonte %s — continuando com as demais", s.fonte)

    if not coletados:
        log.error("Nenhum concurso coletado de nenhuma fonte. Abortando sem enviar e-mail.")
        return 1

    ti = filtrar(normalizar_todos(coletados), cfg.keywords_ti)
    log.info("Na area de TI: %d", len(ti))

    novos = estado.novos(ti)
    log.info("Novos desde a ultima execucao: %d", len(novos))

    if not novos:
        log.info("Sem novidades. Nenhum e-mail sera enviado.")
        estado.salvar()
        return 0

    html = gerar_html(novos)
    if cfg.email_configurado:
        enviar(cfg, f"🎯 {len(novos)} novo(s) concurso(s) de tecnologia", html)
    else:
        log.warning("SMTP nao configurado — relatório NAO enviado (apenas impresso abaixo).")
        print(html)

    estado.registrar(novos)
    estado.salvar()
    log.info("Estado atualizado (%d concursos acompanhados).", len(estado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
