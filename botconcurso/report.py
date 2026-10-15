"""Geracao do relatorio HTML enviado por e-mail."""

from __future__ import annotations

import html
from datetime import datetime

from .models import Concurso


def _esc(texto: str | None) -> str:
    return html.escape(texto) if texto else "—"


def gerar_html(concursos: list[Concurso], gerado_em: datetime | None = None) -> str:
    gerado_em = gerado_em or datetime.now()
    linhas = []
    for c in sorted(concursos, key=lambda x: (x.inscricao_ate or "9999", x.orgao)):
        linhas.append(
            "<tr>"
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">'
            f'<a href="{_esc(c.url)}" style="color:#0b5ed7;text-decoration:none;font-weight:600;">'
            f"{_esc(c.orgao)}</a><br>"
            f'<span style="color:#6b7280;font-size:12px;">{_esc(c.uf)}</span></td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{_esc(", ".join(c.cargos))}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{_esc(c.vagas)}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{_esc(c.salario_ate)}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{_esc(c.inscricao_texto)}</td>'
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Novos concursos de TI</title></head>
<body style="margin:0;padding:16px;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:760px;margin:0 auto;background:#ffffff;border-radius:8px;padding:24px;">
    <h1 style="font-size:18px;color:#111827;margin:0 0 4px;">🎯 {len(concursos)} novo(s) concurso(s) de tecnologia</h1>
    <p style="color:#6b7280;font-size:13px;margin:0 0 16px;">
      Encontrado(s) em {gerado_em.strftime("%d/%m/%Y às %H:%M")} · fonte: PCI Concursos
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:13px;color:#111827;">
      <thead>
        <tr style="background:#f9fafb;text-align:left;">
          <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;">Órgão</th>
          <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;">Cargos</th>
          <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;">Vagas</th>
          <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;">Salário até</th>
          <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;">Inscrição</th>
        </tr>
      </thead>
      <tbody>
        {''.join(linhas)}
      </tbody>
    </table>
    <p style="color:#9ca3af;font-size:11px;margin:16px 0 0;">
      Relatório automático do BotConcurso · você recebe este e-mail apenas quando há novidades
    </p>
  </div>
</body>
</html>"""
