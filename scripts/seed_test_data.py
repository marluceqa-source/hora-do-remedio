"""Popula o banco com dados fictícios para desenvolvimento e testes manuais (CT40).

ATENÇÃO: os dados aqui são inteiramente sintéticos e não representam orientação médica
real — servem apenas para exercitar a aplicação localmente.

Uso:
    python scripts/seed_test_data.py
"""

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import Base, SessionLocal, engine  # noqa: E402
from database.models import Medication, ReminderEvent, Schedule, User  # noqa: E402

FICTITIOUS_TELEGRAM_USER_ID = 111222333


def _reset_fictitious_user(db) -> None:
    existing = db.query(User).filter(User.telegram_user_id == FICTITIOUS_TELEGRAM_USER_ID).first()
    if existing is not None:
        db.delete(existing)  # cascata remove medicamentos, horários e lembretes associados
        db.commit()


def seed() -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _reset_fictitious_user(db)

        user = User(telegram_user_id=FICTITIOUS_TELEGRAM_USER_ID, timezone="America/Sao_Paulo")
        db.add(user)
        db.flush()

        losartana = Medication(
            user_id=user.id,
            name="Losartana (fictício)",
            dosage="50mg",
            quantity="1 comprimido",
            instructions="Exemplo de observação — dado sintético, sem valor clínico.",
            start_date=date.today() - timedelta(days=10),
            active=True,
        )
        losartana.schedules = [Schedule(recurrence_type="daily", schedule_time=time(8, 0), timezone=user.timezone)]
        db.add(losartana)
        db.flush()

        vitamina_d = Medication(
            user_id=user.id,
            name="Vitamina D (fictício)",
            dosage="2000UI",
            quantity="1 cápsula",
            start_date=date.today() - timedelta(days=3),
            active=True,
        )
        vitamina_d.schedules = [
            Schedule(recurrence_type="weekly", schedule_time=time(12, 0), weekdays="mon,wed,fri", timezone=user.timezone)
        ]
        db.add(vitamina_d)
        db.flush()

        now = datetime.now().replace(second=0, microsecond=0)
        reminders = [
            ReminderEvent(
                medication_id=losartana.id,
                scheduled_datetime=now - timedelta(days=1),
                delivery_datetime=now - timedelta(days=1),
                confirmed_datetime=now - timedelta(days=1) + timedelta(minutes=5),
                status="confirmed",
            ),
            ReminderEvent(
                medication_id=losartana.id,
                scheduled_datetime=now,
                delivery_datetime=now,
                status="delivered",  # ainda sem confirmação do usuário
            ),
            ReminderEvent(
                medication_id=vitamina_d.id,
                scheduled_datetime=now - timedelta(days=2),
                delivery_datetime=now - timedelta(days=2),
                status="not_taken",
            ),
        ]
        db.add_all(reminders)
        db.commit()

        return {
            "telegram_user_id": user.telegram_user_id,
            "medications": [losartana.id, vitamina_d.id],
            "reminder_events": [r.id for r in reminders],
        }
    finally:
        db.close()


if __name__ == "__main__":
    summary = seed()
    print("Dados fictícios inseridos com sucesso (não usar como orientação médica).")
    print(f"  Usuário (telegram_user_id): {summary['telegram_user_id']}")
    print(f"  Medicamentos criados (ids): {summary['medications']}")
    print(f"  Lembretes criados (ids): {summary['reminder_events']}")
    print()
    print("Para autenticar na API com este usuário fictício:")
    print(f'  POST /api/v1/auth/token  {{"telegram_user_id": {summary["telegram_user_id"]}}}')
