# BotConcurso — Backlog de Tarefas

> Derivado do doc de arquitetura (`docs/arquitetura.md`). Atualizado em 15/10/2026.
> Convenção: **P1** = bloqueia o MVP, **P2** = importante, **P3** = nice-to-have.

---

## Fase 0 — Setup do repositório

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F0-1 | Inicializar repo Git no diretório do projeto (`.gitignore` para Python, `data/estado.json` **não** ignorado) | P1 | `git init` + commit inicial com estrutura de pastas vazia |
| F0-2 | Criar `requirements.txt` (`requests`, `beautifulsoup4`, `lxml`, `pytest`) | P1 | `pip install -r requirements.txt` instala sem erro |
| F0-3 | Criar `README.md` com: objetivo, como rodar local, como configurar secrets, como rodar testes | P2 | README reflete o estado real do código |

---

## Fase 1 — MVP (PCI + e-mail + Actions)

### Scrapers

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F1-1 | Implementar `src/scrapers/base.py`: classe `ScraperBase` com método `coletar() -> list[Concurso]` e dataclass `Concurso` com `id_unico` (hash de fonte+órgão+cargos+url) | P1 | Contrato importável e testável |
| F1-2 | Implementar `src/scrapers/pci.py`: raspar listagem nacional + estados de `https://www.pciconcursos.com.br/concursos/` (com delay entre requests e User-Agent identificável) | P1 | Retorna lista de `Concurso` com órgão, vagas, salário, escolaridade, prazo e link |
| F1-3 | Raspar **página de detalhe** dos concursos com "Vários Cargos" no PCI, para listar cargos reais (com cache no `estado.json` — só consulta páginas novas) | P1 | Concursos genéricos passam a ter `cargos` preenchidos; SETEC Campinas "Analista Técnico (Informática)" é capturado |
| F1-4 | Gravar fixture HTML do PCI em `tests/fixtures/` e teste que valida o parser contra ela | P1 | Teste passa; quebra se o PCI mudar o layout |

### Pipeline

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F1-5 | `src/normalizer.py`: padronizar campos (datas em ISO, salário como texto normalizado) | P1 | Unidade coberta por teste |
| F1-6 | `src/filter.py`: filtrar por `KEYWORDS_TI` (lista em `config.py`, sobrescrevível por env var) | P1 | Teste com casos positivos/negativos (ex.: "Professor de Informática" vs "Analista de Sistemas") |
| F1-7 | `src/storage.py`: ler/gravar `data/estado.json`; API `novos(registros) -> list[Concurso]` | P1 | Segunda execução com mesmos dados retorna lista vazia |
| F1-8 | `src/report.py`: gerar relatório HTML (tabela: órgão, cargos, vagas, salário, prazo, link) | P1 | HTML válido, legível em cliente de e-mail |
| F1-9 | `src/mailer.py`: envio via SMTP genérico (host/porta/usuário/senha por env var) — ver decisão de provedor em `docs/arquitetura.md` §10 | P1 | Envia e-mail real numa conta de teste |
| F1-10 | `scripts/run_local.py`: orquestra tudo (coletar → normalizar → filtrar → comparar → [se houver novos] reportar+e-mail → gravar estado) | P1 | Roda de ponta a ponta localmente |

### Infra

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F1-11 | `.github/workflows/bot.yml`: cron diário + `workflow_dispatch`, setup Python, execução, commit automático do `estado.json` | P1 | Action roda manualmente com sucesso |
| F1-12 | Configurar secrets no GitHub (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_PARA`) | P1 | — (depende da decisão de provedor) |
| F1-13 | Definir horário do e-mail em BRT e ajustar o cron (Actions roda em UTC) | P2 | E-mail chega no horário combinado |
| F1-14 | Testes automatizados no Actions (`pytest`) como etapa do workflow | P2 | PR/commit quebra o pipeline se teste falhar |

---

## Fase 2 — Fonte FGV

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F2-1 | Spike: descobrir como obter os dados do site da FGV (endpoint AJAX do Drupal, JSON embutido, ou necessidade de Playwright) | P2 | Doc curto com opção escolhida e protótipo |
| F2-2 | Implementar `src/scrapers/fgv.py` seguindo o contrato `ScraperBase` | P2 | Mesma saída normalizada do PCI |
| F2-3 | Deduplicação cruzada (mesmo concurso visto no PCI e na FGV aparece uma vez só) | P3 | Teste com par de registros duplicados |

---

## Fase 3 — Fontes oficiais e extras

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F3-1 | Scraper de banca(s) prioritária(s): Cebraspe, Vunesp, FCC ou Cesgranrio | P3 | Contrato `ScraperBase` respeitado |
| F3-2 | API do DOU (`in.gov.br`) para avisos de editais federais | P3 | Spike primeiro — PDF é complexo |
| F3-3 | Configuração de interesses por e-mail (áreas/estados diferentes para destinatários diferentes) | P3 | — |

---

## Fase 4 — Melhorias

| ID | Tarefa | Prioridade | Critérios de aceite |
|---|---|---|---|
| F4-1 | Resumo semanal ("tudo que está aberto agora", mesmo sem novidades) | P3 | — |
| F4-2 | Retry com backoff + alerta quando uma fonte falhar (e-mail de "fonte fora do ar") | P2 | Falha simulada dispara o aviso |
| F4-3 | Log estruturado da execução (visível nos logs do Actions) | P2 | — |
| F4-4 | Guard contra mudança de layout: se o parser retornar 0 concursos, abortar e alertar em vez de enviar e-mail vazio | P2 | Teste com fixture quebrada |

---

## Pendências de decisão (não são código)

| ID | Decisão | Onde está detalhado | Status |
|---|---|---|---|
| D-1 | **Provedor de e-mail** — Gmail SMTP (mais simples) vs Brevo/Resend (API) — comparativo em `docs/arquitetura.md` §10 | arquitetura.md §10 | ⏳ aguardando você |
| D-2 | Horário desejado para receber o e-mail | — | ⏳ aguardando você |
| D-3 | Para qual e-mail vai o relatório (pode ser o mesmo Gmail) | — | ⏳ aguardando você |
