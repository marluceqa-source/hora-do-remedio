"""Execução do script de seed e persistência de dados após reinicialização (CT39, CT40)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import scripts.seed_test_data as seed_module
from database.models import User


def test_ct40_seed_script_runs_and_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "seed_test.db"
    test_engine = create_engine(f"sqlite:///{db_path}")
    test_session_local = sessionmaker(bind=test_engine)

    monkeypatch.setattr(seed_module, "engine", test_engine)
    monkeypatch.setattr(seed_module, "SessionLocal", test_session_local)

    summary1 = seed_module.seed()
    summary2 = seed_module.seed()  # executar de novo não deve duplicar dados (idempotente)

    assert summary1["telegram_user_id"] == summary2["telegram_user_id"]
    assert len(summary1["medications"]) == 2
    assert len(summary1["reminder_events"]) == 3

    db = test_session_local()
    try:
        total_users = db.query(User).filter(User.telegram_user_id == summary1["telegram_user_id"]).count()
        assert total_users == 1  # a segunda execução substituiu, não duplicou
    finally:
        db.close()


def test_ct39_data_persists_after_reopening_the_database_file(tmp_path, monkeypatch):
    db_path = tmp_path / "persistence_test.db"
    test_engine = create_engine(f"sqlite:///{db_path}")
    test_session_local = sessionmaker(bind=test_engine)
    monkeypatch.setattr(seed_module, "engine", test_engine)
    monkeypatch.setattr(seed_module, "SessionLocal", test_session_local)

    summary = seed_module.seed()
    test_engine.dispose()  # simula o encerramento do processo

    # "Reinicialização": abre uma conexão nova para o mesmo arquivo de banco.
    reopened_engine = create_engine(f"sqlite:///{db_path}")
    reopened_session_local = sessionmaker(bind=reopened_engine)
    db = reopened_session_local()
    try:
        user = db.query(User).filter(User.telegram_user_id == summary["telegram_user_id"]).one()
        assert len(user.medications) == 2
        assert sum(len(m.reminder_events) for m in user.medications) == 3
    finally:
        db.close()
        reopened_engine.dispose()
