"""Pré-condições montadas direto no banco, quando o caminho até elas não é o objeto do teste."""

from datetime import datetime, timedelta

from database.models import Medication, ReminderEvent, Schedule, User


def usuario(db, telegram_user_id: int, *, modo_acessivel: bool = False) -> User:
    existente = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if existente is not None:
        return existente
    novo = User(telegram_user_id=telegram_user_id, timezone='America/Sao_Paulo', accessibility_mode=modo_acessivel)
    db.add(novo)
    db.commit()
    return novo


def medicamento(db, dono: User, *, nome: str = 'Losartana Fictícia', hora: int = 8) -> Medication:
    registro = Medication(
        user_id=dono.id,
        name=nome,
        dosage='50mg',
        quantity='1 comprimido',
        start_date=datetime.now().date(),
        active=True,
    )
    registro.schedules = [
        Schedule(recurrence_type='daily', schedule_time=datetime.now().time().replace(hour=hora, minute=0), timezone=dono.timezone)
    ]
    db.add(registro)
    db.commit()
    return registro


def lembrete(db, remedio: Medication, *, status: str = 'delivered', minutos_atras: int = 30) -> ReminderEvent:
    evento = ReminderEvent(
        medication_id=remedio.id,
        scheduled_datetime=datetime.now().replace(microsecond=0) - timedelta(minutes=minutos_atras),
        status=status,
    )
    db.add(evento)
    db.commit()
    return evento
