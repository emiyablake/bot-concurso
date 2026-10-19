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

from src.config import Config
from src.filter import filtrar
from src.mailer import enviar
from src.normalizer import normalizar_todos
from src.report import gerar_html
from src.scrapers import PciScraper
from src.storage import Estado

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("botconcurso")


def main() -> int:
    cfg = Config.do_ambiente()
    estado = Estado(cfg.estado_path)

    log.info("Coletando concursos...")
    scrapers = [PciScraper(user_agent=cfg.user_agent, delay=cfg.delay_entre_requests)]
    coletados = []
    enriquecidos = []
    for s in scrapers:
        try:
            itens = s.coletar()
            log.info("Fonte %s: %d concursos", s.fonte, len(itens))
            # busca os cargos reais das entradas "Vários Cargos" (so as novas;
            # as ja vistas usam o cache do estado.json)
            enriquecidos += s.enriquecer_varios_cargos(itens, estado.cargos_conhecidos)
            log.info("Fonte %s: %d paginas de detalhe consultadas", s.fonte, len(enriquecidos))
            coletados.extend(itens)
        except Exception:
            log.exception("Falha ao coletar da fonte %s — continuando com as demais", s.fonte)

    if not coletados:
        log.error("Nenhum concurso coletado de nenhuma fonte. Abortando sem enviar e-mail.")
        return 1

    ti = filtrar(normalizar_todos(coletados), cfg.keywords_ti)
    log.info("Na area de TI: %d", len(ti))

    # modo teste: forca o envio com todos os concursos da area atuais,
    # sem alterar o estado (para validar SMTP no Actions)
    if cfg.email_teste:
        log.info("MODO TESTE: enviando e-mail com os %d concursos da area atuais (estado nao alterado).", len(ti))
        html = gerar_html(ti)
        if cfg.email_configurado:
            enviar(cfg, f"🎯 {len(ti)} concurso(s) na sua área — e-mail de teste", html)
            log.info("E-mail de teste enviado.")
        else:
            log.warning("SMTP nao configurado — relatorio de teste apenas impresso abaixo.")
            print(html)
        return 0

    novos = estado.novos(ti)
    log.info("Novos desde a ultima execucao: %d", len(novos))

    if not novos:
        log.info("Sem novidades. Nenhum e-mail sera enviado.")
        estado.salvar()
        return 0

    html = gerar_html(novos)
    if cfg.email_configurado:
        enviar(cfg, f"🎯 {len(novos)} novo(s) concurso(s) na sua área", html)
    else:
        log.warning("SMTP nao configurado — relatório NAO enviado (apenas impresso abaixo).")
        print(html)

    # registra tambem os enriquecidos que NAO sao de TI: assim nao refazemos
    # a requisicao de detalhe deles amanha (o id muda quando os cargos mudam,
    # entao se um dia entrarem na area de TI, serao reportados normalmente)
    estado.registrar([c for c in enriquecidos if c.id_unico not in estado._itens])
    estado.registrar(novos)
    estado.salvar()
    log.info("Estado atualizado (%d concursos acompanhados).", len(estado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
