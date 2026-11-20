from datetime import time
from unittest.mock import MagicMock

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database.models import Schedule
from services.scheduler_service import SchedulerService, _build_trigger


def _schedule(**overrides) -> Schedule:
    base = {
        "recurrence_type": "daily",
        "schedule_time": time(8, 0),
        "interval_hours": None,
        "weekdays": None,
        "timezone": "America/Sao_Paulo",
    }
    base.update(overrides)
    return Schedule(**base)


def test_build_trigger_daily_is_cron_at_the_right_time():
    trigger = _build_trigger(_schedule(recurrence_type="daily", schedule_time=time(8, 30)))
    assert isinstance(trigger, CronTrigger)
    assert str(trigger.fields[trigger.FIELD_NAMES.index("hour")]) == "8"
    assert str(trigger.fields[trigger.FIELD_NAMES.index("minute")]) == "30"


def test_build_trigger_weekly_uses_weekdays():
    trigger = _build_trigger(_schedule(recurrence_type="weekly", schedule_time=time(20, 0), weekdays="mon,wed,fri"))
    assert isinstance(trigger, CronTrigger)
    assert "mon" in str(trigger.fields[trigger.FIELD_NAMES.index("day_of_week")])


def test_build_trigger_interval_uses_hours():
    trigger = _build_trigger(_schedule(recurrence_type="interval", schedule_time=None, interval_hours=6))
    assert isinstance(trigger, IntervalTrigger)
    assert trigger.interval.total_seconds() == 6 * 3600


def test_build_trigger_unknown_type_returns_none():
    schedule = _schedule(recurrence_type="daily")
    schedule.recurrence_type = "outro"
    assert _build_trigger(schedule) is None


def test_scheduler_service_schedule_snooze_adds_one_off_job():
    notify = MagicMock()
    service = SchedulerService(notify_callback=notify)
    service._scheduler.start()
    try:
        service.schedule_snooze(reminder_id=1, minutes=10)
        job_ids = [job.id for job in service._scheduler.get_jobs()]
        assert any(job_id.startswith("snooze-1-") for job_id in job_ids)
    finally:
        service.shutdown()
