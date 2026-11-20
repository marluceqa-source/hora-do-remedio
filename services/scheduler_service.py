"""Serviço de agendamento de lembretes (RF05).

Usa APScheduler para dispensar os horários configurados em cada Schedule. A persistência
exigida pelo RF05 é obtida reconstruindo os jobs, a cada início do processo, a partir dos
registros de Schedule/Medication já persistidos no banco (fonte única de verdade) — em vez
de depender de um jobstore próprio do APScheduler, o que evitaria duplicar o estado.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.connection import SessionLocal
from database.models import Medication, ReminderEvent, Schedule

logger = logging.getLogger(__name__)

NotifyCallback = Callable[[int], None]
_RESYNC_INTERVAL_MINUTES = 5


def _build_trigger(schedule: Schedule):
    tz = ZoneInfo(schedule.timezone)
    if schedule.recurrence_type == "daily":
        return CronTrigger(hour=schedule.schedule_time.hour, minute=schedule.schedule_time.minute, timezone=tz)
    if schedule.recurrence_type == "weekly":
        return CronTrigger(
            day_of_week=schedule.weekdays,
            hour=schedule.schedule_time.hour,
            minute=schedule.schedule_time.minute,
            timezone=tz,
        )
    if schedule.recurrence_type == "interval":
        return IntervalTrigger(hours=schedule.interval_hours, timezone=tz)
    logger.warning("Tipo de recorrência desconhecido para schedule_id=%s: %s", schedule.id, schedule.recurrence_type)
    return None


class SchedulerService:
    def __init__(self, notify_callback: NotifyCallback, session_factory: sessionmaker = SessionLocal) -> None:
        self._scheduler = BackgroundScheduler()
        self._notify_callback = notify_callback
        self._session_factory = session_factory

    def start(self) -> None:
        self._scheduler.start()
        self.reload_jobs()
        # Ressincroniza periodicamente com o banco, cobrindo medicamentos cadastrados
        # diretamente pela API REST (fora do fluxo de cadastro do bot).
        self._scheduler.add_job(
            self.reload_jobs,
            trigger=IntervalTrigger(minutes=_RESYNC_INTERVAL_MINUTES),
            id="resync-jobs",
            replace_existing=True,
        )
        logger.info("SchedulerService iniciado")

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("SchedulerService encerrado")

    def reload_jobs(self) -> None:
        """Reconstrói todos os jobs a partir dos Schedules de medicamentos ativos (RF05, RN15).

        Remove apenas os jobs recorrentes de medicamentos ("schedule-*"), preservando o job de
        ressincronização periódica e eventuais reenvios de adiamento ("snooze-*") já agendados.
        """
        for job in self._scheduler.get_jobs():
            if job.id.startswith("schedule-"):
                job.remove()
        db = self._session_factory()
        try:
            schedules = db.query(Schedule).join(Medication).filter(Medication.active.is_(True)).all()
            for schedule in schedules:
                self._add_job(schedule)
            logger.info("Jobs recarregados: %s", len(schedules))
        finally:
            db.close()

    def add_schedule(self, schedule: Schedule) -> None:
        self._add_job(schedule)

    def schedule_snooze(self, reminder_id: int, minutes: int) -> None:
        """Agenda um reenvio único do lembrete após o adiamento (RF08), sem alterar o horário original."""
        self._scheduler.add_job(
            self._notify_callback,
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=minutes),
            args=[reminder_id],
            id=f"snooze-{reminder_id}-{datetime.now().timestamp()}",
            misfire_grace_time=600,
        )

    def _add_job(self, schedule: Schedule) -> None:
        trigger = _build_trigger(schedule)
        if trigger is None:
            return
        self._scheduler.add_job(
            self._fire,
            trigger=trigger,
            args=[schedule.medication_id, schedule.id],
            id=f"schedule-{schedule.id}",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    def _fire(self, medication_id: int, schedule_id: int) -> None:
        db = self._session_factory()
        try:
            medication = db.get(Medication, medication_id)
            schedule = db.get(Schedule, schedule_id)
            if medication is None or schedule is None or not medication.active:
                return

            tz = ZoneInfo(schedule.timezone)
            today = datetime.now(tz).date()
            if today < medication.start_date:
                return
            if medication.end_date is not None and today > medication.end_date:
                # RN03: não enviar lembrete após o encerramento do tratamento.
                return

            scheduled_datetime = datetime.now(tz).replace(tzinfo=None, microsecond=0)
            reminder = ReminderEvent(medication_id=medication.id, scheduled_datetime=scheduled_datetime, status="pending")
            db.add(reminder)
            try:
                db.commit()
            except IntegrityError:
                # RN18: evita duplicidade caso o job dispare mais de uma vez para o mesmo minuto.
                db.rollback()
                logger.info("Lembrete já existente para medication_id=%s em %s", medication_id, scheduled_datetime)
                return
            db.refresh(reminder)
            self._notify_callback(reminder.id)
        except Exception:
            logger.exception("Falha ao disparar lembrete medication_id=%s schedule_id=%s", medication_id, schedule_id)
        finally:
            db.close()
