"""
Preparação dos testes do bot do Telegram.

Os handlers do bot são funções assíncronas que recebem `update` e `context` e falam
direto com o banco por `SessionLocal`. Aqui montamos:

  * o caminho da aplicação no `sys.path`, para importar `bot`, `services` e `database`;
  * um banco SQLite em memória, criado e destruído a cada teste;
  * a substituição do `SessionLocal` de cada handler pelo banco de teste;
  * o silenciamento da síntese de voz (pyttsx3), que abriria o sintetizador do sistema.

Nenhum teste fala com o Telegram de verdade: o que é exercitado é o comportamento do bot
diante de cada entrada — que é exatamente o que as heurísticas investigam.
"""

import os
import sys
from pathlib import Path

import pytest

# A aplicação sob teste. Pode ser sobrescrita por APP_DIR.
RAIZ_APP = Path(os.environ.get("APP_DIR") or Path(__file__).resolve().parents[2]).resolve()

# Conferir um arquivo da aplicação, e não só a existência da pasta: neste branch estão
# apenas os testes, então o caminho padrão existe mas não tem aplicação nenhuma dentro.
if not (RAIZ_APP / "bot" / "main.py").exists():  # pragma: no cover - erro de ambiente
    raise RuntimeError(
        f'Aplicação não encontrada em "{RAIZ_APP}".\n\n'
        "Este branch tem apenas os testes: o código da aplicação está no main.\n"
        "Aponte APP_DIR para um diretório onde a aplicação esteja, por exemplo:\n"
        "    APP_DIR=../../../aplicacao ../../../aplicacao/.venv/bin/python -m pytest"
    )

sys.path.insert(0, str(RAIZ_APP))

# Antes de qualquer import da aplicação: o engine do módulo `database.connection` é
# criado no import, e não queremos que ele aponte para o banco de desenvolvimento.
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('APP_ENV', 'test')

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from database import models  # noqa: E402,F401  registra todas as tabelas
from database.connection import Base  # noqa: E402

# Módulos de handler que abrem sessão própria e precisam ser redirecionados ao banco de teste.
MODULOS_COM_SESSAO = (
    'bot.handlers.start',
    'bot.handlers.medications',
    'bot.handlers.reminders',
    'bot.handlers.caregivers',
    'bot.handlers.patients',
    'bot.handlers.accessibility',
)


@pytest.fixture()
def fabrica_de_sessao():
    """Banco novo, vazio e em memória para cada teste."""
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(fabrica_de_sessao):
    """Sessão para o teste montar pré-condições e conferir o que ficou gravado."""
    sessao = fabrica_de_sessao()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture(autouse=True)
def _redirecionar_banco_dos_handlers(request, monkeypatch):
    """Todo handler passa a usar o banco do teste, nunca o banco de desenvolvimento."""
    if 'fabrica_de_sessao' not in request.fixturenames:
        return
    fabrica = request.getfixturevalue('fabrica_de_sessao')
    for modulo in MODULOS_COM_SESSAO:
        __import__(modulo)
        monkeypatch.setattr(f'{modulo}.SessionLocal', fabrica, raising=False)


@pytest.fixture(autouse=True)
def _silenciar_voz(monkeypatch):
    """pyttsx3 abriria o sintetizador do sistema operacional a cada mensagem."""
    for modulo in ('bot.handlers.common', 'bot.handlers.medications', 'bot.handlers.reminders'):
        __import__(modulo)
        monkeypatch.setattr(f'{modulo}.synthesize_to_file', lambda *_args, **_kwargs: None, raising=False)
