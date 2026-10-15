import os

from botconcurso.config import Config, KEYWORDS_TI_PADRAO


def test_variavel_vazia_cai_no_padrao(monkeypatch):
    # Actions injeta secrets nao criados como string vazia;
    # devem cair no padrao, nao quebrar o int()
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_PORT", "")
    monkeypatch.setenv("SMTP_USER", "user@gmail.com")
    monkeypatch.setenv("SMTP_PASS", "abcd efgh ijkl mnop")
    monkeypatch.setenv("EMAIL_PARA", "user@gmail.com")
    cfg = Config.do_ambiente()
    assert cfg.smtp_host == "smtp.gmail.com"
    assert cfg.smtp_port == 465
    assert cfg.email_configurado


def test_sem_env_usa_padrao(monkeypatch):
    for var in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "EMAIL_DE", "EMAIL_PARA", "KEYWORDS_TI", "ESTADO_PATH"]:
        monkeypatch.delenv(var, raising=False)
    cfg = Config.do_ambiente()
    assert cfg.smtp_host == "smtp.gmail.com"
    assert cfg.smtp_port == 465
    assert cfg.keywords_ti == KEYWORDS_TI_PADRAO
    assert not cfg.email_configurado


def test_email_de_padroniza_para_remetente(monkeypatch):
    monkeypatch.setenv("SMTP_USER", "user@gmail.com")
    monkeypatch.delenv("EMAIL_DE", raising=False)
    cfg = Config.do_ambiente()
    assert cfg.email_de == "user@gmail.com"


def test_keywords_customizadas(monkeypatch):
    monkeypatch.setenv("KEYWORDS_TI", "desenvolvedor, engenheiro de software")
    cfg = Config.do_ambiente()
    assert cfg.keywords_ti == ["desenvolvedor", "engenheiro de software"]
