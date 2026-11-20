"""Massa de teste para testar manualmente cada opção do menu principal do bot.

Diferente de `seed_test_data.py` (dados mínimos usados pelo teste automatizado CT40), este
script gera um usuário fictício separado com 5 itens de apoio para cada tela que exibe uma
lista:

- 💊 Meus Remédios  → 5 medicamentos ativos, cobrindo os 3 tipos de recorrência.
- 📅 Remédios de Hoje / 🔊 Ouvir Lembretes → 5 lembretes de hoje, um em cada status real
  usado pelo sistema (pending, delivered, confirmed, not_taken, snoozed).
- 📊 Histórico → mais 5 lembretes espalhados nos últimos dias, também variando o status.

➕ Adicionar Remédio, ⚙️ Configurações e ❓ Ajuda não entram aqui por serem fluxos interativos
(sem lista para popular).

ATENÇÃO: dados fictícios, só para testes manuais — não usar como orientação médica.

Uso:
    python scripts/seed_massa_teste_menu.py                  # usa o usuário fictício padrão
    python scripts/seed_massa_teste_menu.py 123456789          # usa um telegram_user_id real
"""

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import Base, SessionLocal, engine  # noqa: E402
from database.models import Medication, ReminderEvent, Schedule, User  # noqa: E402

FICTITIOUS_TELEGRAM_USER_ID = 444555666

# Os 5 status realmente usados pelo sistema (ver RF07/RF08 e database/models.py).
# "expired" existe no CHECK CONSTRAINT mas nenhum fluxo do código o utiliza hoje.
STATUSES = ["pending", "delivered", "confirmed", "not_taken", "snoozed"]


_NAME_SUFFIX = " (massa de teste)"


def _get_or_create_user(db, telegram_user_id: int) -> User:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if user is None:
        user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
        db.add(user)
        db.flush()
    return user


def _clear_previous_massa_de_teste(db, user: User) -> None:
    # Remove só os medicamentos desta própria massa de teste (reconhecidos pelo sufixo no
    # nome), preservando qualquer outro dado real que o usuário já tenha no sistema.
    previous = db.query(Medication).filter(
        Medication.user_id == user.id, Medication.name.like(f"%{_NAME_SUFFIX}")
    )
    for medication in previous:
        db.delete(medication)
    db.commit()


def _build_reminder(medication_id: int, scheduled_datetime: datetime, status: str) -> ReminderEvent:
    reminder = ReminderEvent(medication_id=medication_id, scheduled_datetime=scheduled_datetime, status=status)
    if status in ("delivered", "confirmed", "not_taken"):
        reminder.delivery_datetime = scheduled_datetime
    if status == "confirmed":
        reminder.confirmed_datetime = scheduled_datetime + timedelta(minutes=5)
    if status == "snoozed":
        reminder.snooze_count = 1
    return reminder


def seed(telegram_user_id: int = FICTITIOUS_TELEGRAM_USER_ID) -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = _get_or_create_user(db, telegram_user_id)
        _clear_previous_massa_de_teste(db, user)

        # --- 5 medicamentos (💊 Meus Remédios) ---
        medications_spec = [
            ("Losartana", "50mg", "1 comprimido", "daily", time(8, 0), None, None),
            ("Vitamina D", "2000UI", "1 cápsula", "weekly", time(12, 0), None, "mon,wed,fri"),
            ("Omeprazol", "20mg", "1 cápsula", "interval", None, 8, None),
            ("Metformina", "850mg", "1 comprimido", "daily", time(20, 0), None, None),
            ("Amoxicilina", "500mg", "1 comprimido", "daily", time(7, 0), None, None),
        ]

        medications = []
        for name, dosage, quantity, recurrence_type, schedule_time, interval_hours, weekdays in medications_spec:
            medication = Medication(
                user_id=user.id,
                name=f"{name}{_NAME_SUFFIX}",
                dosage=dosage,
                quantity=quantity,
                start_date=date.today() - timedelta(days=5),
                active=True,
            )
            medication.schedules = [
                Schedule(
                    recurrence_type=recurrence_type,
                    schedule_time=schedule_time,
                    interval_hours=interval_hours,
                    weekdays=weekdays,
                    timezone=user.timezone,
                )
            ]
            db.add(medication)
            db.flush()
            medications.append(medication)

        # --- 5 lembretes de hoje, um em cada status (📅 Remédios de Hoje / 🔊 Ouvir Lembretes) ---
        now = datetime.now().replace(second=0, microsecond=0)
        today_reminders = []
        for medication, status in zip(medications, STATUSES, strict=True):
            reminder = _build_reminder(medication.id, now, status)
            db.add(reminder)
            today_reminders.append(reminder)

        # --- mais 5 lembretes espalhados nos últimos dias (📊 Histórico) ---
        history_reminders = []
        for offset, (medication, status) in enumerate(zip(medications, STATUSES, strict=True), start=1):
            when = now - timedelta(days=offset)
            reminder = _build_reminder(medication.id, when, status)
            db.add(reminder)
            history_reminders.append(reminder)

        db.commit()

        return {
            "telegram_user_id": user.telegram_user_id,
            "medications": [m.id for m in medications],
            "today_reminders": [r.id for r in today_reminders],
            "history_reminders": [r.id for r in history_reminders],
        }
    finally:
        db.close()


if __name__ == "__main__":
    target_user_id = int(sys.argv[1]) if len(sys.argv) > 1 else FICTITIOUS_TELEGRAM_USER_ID
    summary = seed(target_user_id)
    print("Massa de teste do menu principal inserida (dados fictícios, só para testes manuais).")
    print(f"  Usuário (telegram_user_id): {summary['telegram_user_id']}")
    print(f"  💊 Medicamentos (Meus Remédios): {summary['medications']}")
    print(f"  📅 Lembretes de hoje (Remédios de Hoje / Ouvir Lembretes): {summary['today_reminders']}")
    print(f"     status, na ordem: {STATUSES}")
    print(f"  📊 Lembretes de dias anteriores (Histórico): {summary['history_reminders']}")
    print()
    print("Para testar pelo bot: fale com @hora_do_remedio_bot usando a conta do Telegram cujo")
    print(f"  user id seja {summary['telegram_user_id']}, OU autentique-se na API com:")
    print(f'  POST /api/v1/auth/token  {{"telegram_user_id": {summary["telegram_user_id"]}}}')
