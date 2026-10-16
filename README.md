# BotConcurso 🤖

Indexador de concursos públicos na área de **tecnologia** (desenvolvedor, analista de sistemas, engenheiro de software etc.).

Roda diariamente no **GitHub Actions**, coleta concursos do [PCI Concursos](https://www.pciconcursos.com.br/), filtra os de TI e envia um **e-mail só quando há novidades**.

📐 Arquitetura e decisões: [`docs/arquitetura.md`](docs/arquitetura.md) · 📋 Tarefas: [`docs/backlog.md`](docs/backlog.md)

## Como funciona

```
GitHub Actions (diário, 08:00 BRT)
  → scrapers/ coletam concursos (hoje: PCI Concursos)
  → normalizer padroniza os campos
  → filter mantém só concursos de TI (keywords configuráveis)
  → scraper abre a página de detalhe dos "Vários Cargos" (só as novas;
    as já vistas usam o cache do estado.json)
  → storage compara com data/estado.json (versionado no repo)
  → se houver novos: report gera HTML + mailer envia por e-mail
  → estado.json é commitado de volta
```

## Rodando localmente

```bash
pip install -r requirements.txt

# sem credenciais: coleta, filtra e imprime o relatório no console
python scripts/run_local.py

# com credenciais: envia o e-mail de verdade
export SMTP_USER="seu@gmail.com"
export SMTP_PASS="senha_de_app_16caracteres"
export EMAIL_PARA="seu@gmail.com"
python scripts/run_local.py
```

> ⚠️ O Gmail exige uma **senha de app** (não é a senha da conta):
> Conta Google → Segurança → Verificação em duas etapas → **Senhas de app**.

## Testes

```bash
python -m pytest -q
```

Os testes do scraper usam um HTML real do PCI em `tests/fixtures/pci_concursos.html`. Se o site mudar de layout, o teste quebra — é de propósito. Para atualizar a fixture:

```bash
curl -A "Mozilla/5.0" https://www.pciconcursos.com.br/concursos/ -o tests/fixtures/pci_concursos.html
```

## Configuração do GitHub

1. Crie o repositório no GitHub e faça push.
2. Em **Settings → Secrets and variables → Actions**, cadastre:

| Secret | Exemplo | Obrigatório |
|---|---|---|
| `SMTP_USER` | `seu@gmail.com` | sim |
| `SMTP_PASS` | senha de app de 16 caracteres | sim |
| `EMAIL_PARA` | `seu@gmail.com` | sim |
| `EMAIL_DE` | `seu@gmail.com` (quando diferente do remetente) | não |
| `SMTP_HOST` / `SMTP_PORT` | padrão `smtp.gmail.com:465` | não |

3. (Opcional) Em **Variables**, defina `KEYWORDS_TI` (separadas por vírgula) para personalizar o filtro e `REQUEST_DELAY` (segundos entre requisições de detalhe, padrão `1.0`).
4. Em **Actions → bot-concurso → Run workflow**, dispare uma execução manual de teste.

## Estrutura

```
src/
├── config.py         # variáveis de ambiente + keywords padrão
├── models.py         # dataclass Concurso (contrato entre fontes)
├── scrapers/
│   ├── base.py       # contrato ScraperBase
│   └── pci.py        # PCI Concursos
├── normalizer.py     # datas ISO, limpeza de campos
├── filter.py         # filtro de área por keywords
├── storage.py        # estado.json (já vistos)
├── report.py         # HTML do e-mail
└── mailer.py         # envio SMTP
```
