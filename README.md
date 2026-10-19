# BotConcurso 🤖

Monitor de **concursos públicos** que roda de graça no **GitHub Actions**: coleta os concursos do [PCI Concursos](https://www.pciconcursos.com.br/) todos os dias, filtra os da **sua área de interesse** e te envia um **e-mail só quando há novidades**.

O filtro padrão é a área de **tecnologia** (desenvolvedor, analista de sistemas, engenheiro de software etc.), mas ele funciona para **qualquer área** — saúde, direito, engenharia, educação. Veja [Personalizando para a sua área](#personalizando-para-a-sua-área).

📐 Arquitetura e decisões: [`docs/arquitetura.md`](docs/arquitetura.md) · 📋 Tarefas: [`docs/backlog.md`](docs/backlog.md)

## Como funciona

```
GitHub Actions (diário, 07:23 BRT)
  → scrapers/ coletam concursos (hoje: PCI Concursos)
  → normalizer padroniza os campos
  → filter mantém só concursos da sua área (keywords configuráveis)
  → scraper abre a página de detalhe dos "Vários Cargos" (só as novas;
    as já vistas usam o cache do estado.json)
  → storage compara com data/estado.json (versionado no repo)
  → se houver novos: report gera HTML + mailer envia por e-mail
  → estado.json é commitado de volta
```

## Personalizando para a sua área

O bot decide o que te interessa por uma lista de **keywords** aplicada sobre o órgão + cargos de cada concurso. Existem três níveis de personalização:

### 1. Sem mexer no código (mesmo repositório)

Em **Settings → Secrets and variables → Actions → Variables**, crie a variável `KEYWORDS_TI` com suas palavras separadas por vírgula. Exemplos:

```
# Saúde
enfermeiro, médico, farmacêutico, técnico de enfermagem, fisioterapeuta

# Direito
advogado, analista jurídico, promotor, juiz, defensor

# Qualquer cargo específico
auditor fiscal, analista do seguro social
```

### 2. Forkando o projeto

1. Faça **fork** deste repositório
2. Edite a lista `KEYWORDS_TI_PADRAO` em [`src/config.py`](src/config.py) com as suas keywords
3. Siga a [Configuração do GitHub](#configuração-do-github) no seu fork

### 3. Dicas de filtro

- O match é **por substring, sem acento e case-insensitive**: `"enferm"` pega Enfermeiro, Técnico de Enfermagem, Enfermagem...
- Cuidado com palavras curtas demais: `"dados"` pega "banco de dados" mas também "endereço"… não, mas pega qualquer coisa com "dados" — avalie os resultados nos primeiros dias
- Quanto o PCI lista "Vários Cargos", o bot abre a página do concurso e lê os cargos reais antes de filtrar

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

3. (Opcional) Em **Variables**: `KEYWORDS_TI` (suas keywords) e `REQUEST_DELAY` (segundos entre requisições de detalhe, padrão `1.0`).
4. Em **Actions → bot-concurso → Run workflow**, dispare uma execução manual — marque **"Enviar e-mail de teste"** para receber um e-mail com tudo que está sendo acompanhado na sua área.

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
