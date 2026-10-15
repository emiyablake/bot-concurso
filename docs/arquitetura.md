# BotConcurso — Arquitetura do Projeto

> Indexador de concursos públicos na área de tecnologia.
> Monitora fontes diariamente via GitHub Actions, filtra concursos de TI e envia um relatório por e-mail.

---

## 1. Objetivo

Coletar diariamente informações sobre novos concursos públicos brasileiros nas áreas de:

- Desenvolvedor de software / desenvolvedor de sistemas
- Analista de sistemas / analista de TI
- Engenheiro de software
- Cargos correlatos de tecnologia (suporte, infraestrutura, dados, segurança da informação)

...e enviar por e-mail um relatório apenas com o que for **novo desde a última execução**.

---

## 2. Visão geral da arquitetura

```
GitHub Actions (cron diário)
        │
        ▼
┌─────────────────────────────────┐
│  scrapers/                      │
│  ├── pci.py        (PCI Concursos)│
│  └── fgv.py        (FGV, fase 2) │
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│  normalizador                   │  padroniza campos:
│                                 │  órgão, cargo, vagas, salário,
│                                 │  escolaridade, prazo, link
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│  filtro de área (keywords TI)   │  mantém só concursos de tecnologia
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│  comparador com estado anterior │  estado.json (commits no repo)
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│  relatório (e-mail HTML)        │  enviado via SMTP
│  (só se houver novidades)       │  (Gmail app password / SendGrid)
└─────────────────────────────────┘
```

**Stack proposta:** Python 3.12 + `requests` + `beautifulsoup4` + `lxml`. Sem banco de dados — o estado (concursos já vistos) fica num arquivo `data/estado.json` versionado no próprio repositório, o que resolve de graça o armazenamento entre execuções do Actions.

---

## 3. Estrutura de diretórios proposta

```
botConcurso/
├── .github/
│   └── workflows/
│       └── bot.yml            # agendador diário (cron)
├── botconcurso/
│   ├── __init__.py
│   ├── config.py              # lê variáveis de ambiente / secrets
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py            # classe ScraperBase (contrato comum)
│   │   ├── pci.py             # PCI Concursos
│   │   └── fgv.py             # FGV (fase 2)
│   ├── normalizer.py          # padroniza registros entre fontes
│   ├── filter.py              # keywords de TI
│   ├── storage.py             # lê/grava data/estado.json
│   ├── report.py              # monta o HTML do e-mail
│   └── mailer.py              # envio via SMTP
├── data/
│   └── estado.json            # concursos já reportados (versionado)
├── tests/
│   ├── test_filter.py
│   ├── test_normalizer.py
│   └── fixtures/              # HTMLs de exemplo das fontes
├── scripts/
│   └── run_local.py           # executa o pipeline localmente
├── requirements.txt
├── .gitignore
├── README.md
└── docs/
    └── arquitetura.md         # este arquivo
```

**Contrato do scraper** (toda fonte retorna a mesma estrutura):

```python
@dataclass
class Concurso:
    fonte: str          # "pci", "fgv", ...
    orgao: str          # "Câmara dos Deputados"
    cargos: list[str]   # ["Analista Legislativo – Desenvolvedor"]
    vagas: str | None   # "184 vagas" / "Cadastro de reserva"
    salario_ate: str | None
    escolaridade: str | None
    inscricao_ate: str | None  # ISO date se possível
    url: str
    id_unico: str       # hash p/ deduplicar entre execuções
```

---

## 4. Fontes de dados pesquisadas

Resultado da pesquisa feita em 15/10/2026, com validação técnica da viabilidade de raspagem.

### ✅ PCI Concursos — **recomendada como fonte inicial**

| | |
|---|---|
| URL | `https://www.pciconcursos.com.br/concursos/` |
| Tipo | HTML estático, servido pronto no servidor |
| Dados por concurso | órgão, nº de vagas, salário até, cargos, escolaridade, prazo de inscrição, link |
| Cobertura | Nacional, por estado, com seção "NACIONAL" + atualização diária |
| Viabilidade | **Alta** — `requests` + BeautifulSoup resolve. Já existe scraper open-source de referência (`luiseduardobr1/PCIConcursos` no GitHub) |
| Observação | O filtro de área de TI será nosso: o PCI lista "Vários Cargos" genéricos, então o ideal é raspar também a página de detalhe de cada concurso para ver os cargos |

### 🟡 FGV (Fundação Getulio Vargas / FGV Projetos)

| | |
|---|---|
| URL | `https://conhecimento.fgv.br/concursos` |
| Tipo | Site em Drupal; a listagem de concursos ativos vem no HTML, mas **as páginas individuais renderizam os detalhes via JavaScript** |
| Dados | cada concurso tem página própria (`/concursos/<slug>`) com cargos, vagas, edital |
| Viabilidade | **Média** — exige fase 2: ou um parser de endpoints AJAX do Drupal, ou Playwright/Selenium (mais pesado pro Actions) |
| Observação | Como a FGV é banca de concursos grandes (Tribunais, Senado, Banco Central etc.), vale o esforço — mas deixar para depois do PCI funcionando |

### 🟡 Agregadores de notícias (bom para descoberta, ruim para dados)

| Fonte | URL | Observação |
|---|---|---|
| Folha Dirigida / Qconcursos | `folha.qconcursos.com` | Cobertura excelente de "previstos/autorizados", mas é portal de notícias com paywall parcial — scraping frágil |
| JC Concursos | `jcconcursos.com.br` | Mesmo perfil |
| Gran Cursos — blog TI | `blog.grancursosonline.com.br/concursos-ti/` | Página específica de concursos de TI; útil para validar se nosso filtro está pegando o que importa |
| Próximos Concursos | `proximosconcursos.com` | Lista os "melhores sites" e previstos |

### 🟢 Fontes oficiais (conceito — fase 3)

- **Diário Oficial da União (DOU)** — onde editais federais são publicados; tem API pública (`in.gov.br`), mas exige processamento de PDF, complexo demais para o MVP.
- **Sites das bancas**: Cebraspe, Vunesp, FCC, Cesgranrio — cada uma lista seus próprios certames; dá pra adicionar como scrapers independentes seguindo o mesmo contrato.
- **Portais de órgãos** (ex.: CSJT lista TRTs com datas de vencimento) — fontes pontuais de alto valor quando houver um alvo específico.

### Conclusão da pesquisa

**Não existe API pública consolidada de concursos.** O caminho é raspagem, e o PCI Concursos é o ponto de partida ideal: HTML estático, cobertura nacional, atualização diária e estrutura já validada. A FGV entra como segunda fonte numa fase posterior.

---

## 5. Filtro de área de tecnologia

Lista inicial de keywords (case-insensitive, com/sem acentos) aplicada ao órgão + cargos:

```python
KEYWORDS_TI = [
    "desenvolvedor", "desenvolvimento de sistemas", "desenvolvimento de software",
    "analista de sistemas", "analista de ti", "analista de tecnologia",
    "engenheiro de software", "programador",
    "técnico de informática", "técnico em informática",
    "técnico de tecnologia da informação",
    "suporte técnico", "infraestrutura", "redes",
    "segurança da informação", "dados", "ciência de dados",
    "sistemas de informação", "computação",
]
```

Cuidados:
- "Analista de Sistemas" aparece em contextos não-TI (ex.: "Analista de Sistemas Judiciários" em tribunais é cargo de TI mesmo, ok).
- "Vários Cargos" exige abrir a página de detalhe do concurso no PCI para listar os cargos reais.
- A lista deve ser fácil de editar no `config.py` / via variável de ambiente.

---

## 6. Agendamento (GitHub Actions)

```yaml
# .github/workflows/bot.yml (esqueleto)
name: bot-concurso
on:
  schedule:
    - cron: "0 11 * * *"   # 08:00 BRT (11:00 UTC) — TODO: confirmar fuso no Actions
  workflow_dispatch:        # permite rodar manualmente

permissions:
  contents: write           # p/ commitar o estado.json

jobs:
  rodar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python scripts/run_local.py
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          EMAIL_PARA: ${{ secrets.EMAIL_PARA }}
      - name: Commit do estado
        run: |
          git config user.name "bot-concurso"
          git config user.email "bot@users.noreply.github.com"
          git add data/estado.json
          git diff --cached --quiet || git commit -m "atualiza estado [skip ci]"
          git push
```

**Secrets necessários** (Settings → Secrets and variables → Actions):
`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` (app password do Gmail ou credencial SendGrid), `EMAIL_PARA`.

---

## 7. Fluxo de execução

1. Action dispara (diário) ou `python scripts/run_local.py` (manual).
2. Cada scraper retorna a lista de `Concurso` da sua fonte.
3. `normalizer` padroniza e gera `id_unico` (hash de fonte + órgão + cargos + url).
4. `filter` mantém só concursos com keywords de TI.
5. `storage` compara com `data/estado.json`:
   - novos → entram no relatório e são gravados;
   - já vistos → ignorados;
   - sumiram da fonte → podem ser removidos do estado (ou mantidos com flag).
6. `report` gera HTML; `mailer` envia **somente se houver novos concursos** (evita e-mail vazio todo dia).
7. Action commita o `estado.json` atualizado.

---

## 8. Roadmap

| Fase | Entrega |
|---|---|
| **1 — MVP** | Scraper do PCI + filtro TI + estado + e-mail + Actions rodando diário |
| **2** | Scraper da FGV (página de detalhe por concurso), deduplicação cruzada de fontes |
| **3** | Fontes oficiais (DOU API, bancas), categorias de interesse configuráveis por e-mail |
| **4** | Opcional: relatório semanal resumindo tudo aberto, alertas imediatos de concursos "quentes" |

---

## 9. Riscos e cuidados

- **Respeitar os sites**: intervalo entre requisições (delay), User-Agent identificável, volume baixo (1 execução/dia com poucas páginas) — pouco provável de bloqueio, mas manter o scraping enxuto.
- **Mudança de layout**: os scrapers vão quebrar quando o site mudar; os testes com fixtures HTML detectam isso cedo.
- **E-mail**: provedor a definir — ver comparativo na seção 10.
- **Fuso horário**: definir o horário do e-mail em BRT e conferir como o Actions trata o cron (UTC).

---

## 10. Decisão pendente: provedor de e-mail

O bot vai enviar **1 e-mail por dia, só quando houver novidade**. Qualquer opção abaixo cobre isso de sobra — a diferença está na simplicidade de configuração. Pesquisa de mercado feita em out/2026.

| Opção | Custo | Limite gratuito | Esforço de configuração | Observação |
|---|---|---|---|---|
| **Gmail SMTP + senha de app** | R$ 0 | ~500 e-mails/dia | Baixo: gerar "senha de app" na conta Google | **Recomendada para o MVP** — usa a conta que você já tem; só funciona bem para enviar para você mesmo |
| **Brevo** | R$ 0 | 300 e-mails/dia (~9 mil/mês), sem expiração | Médio: criar conta + chave API | Maior cota gratuita atual; bom se um dia quiser enviar para várias pessoas |
| **Resend** | R$ 0 | 3.000/mês (100/dia) | Médio: API moderna, exige verificar domínio para enviar "de" um endereço próprio | Favorita entre devs; sem domínio próprio, só envia para o seu próprio e-mail |
| **Mailgun** | R$ 0 | 100/dia | Médio | Foco em API para desenvolvedores |
| **SendGrid** | trial 60 dias | 100/dia **só durante o trial** | Médio | ⚠️ Aboliu o plano gratuito fixo em 2025 — não recomendada aqui |
| **Amazon SES** | ~US$ 0,10 por 1.000 | 3 mil/mês só nos primeiros 12 meses | Alto: conta AWS + verificação de domínio | Só vale a pena em volume alto |

**Recomendação**: começar com **Gmail SMTP** — zero serviços novos, configuração de 5 minutos (ativa verificação em 2 etapas → gera "senha de app" → salva nos secrets do GitHub). O `mailer.py` será genérico via SMTP, então trocar para Brevo/Resend depois é só trocar host/credenciais nas variáveis de ambiente, sem mudar código.

Se um dia o relatório for para mais pessoas ou deixar de ser "pessoal", migrar para **Brevo** (maior cota gratuita permanente).

> ⚠️ Importante: nunca commitar senha real do Gmail — sempre a "senha de app" (16 caracteres, específica para esse uso), guardada só nos secrets do GitHub.
