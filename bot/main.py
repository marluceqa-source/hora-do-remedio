import logging
import re

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers import accessibility, caregivers, patients, reminders, start
from bot.handlers.medications import build_cadastro_conversation, list_medications_handler
from bot.keyboards.menus import (
    MENU_AJUDA,
    MENU_CONFIG,
    MENU_HISTORICO,
    MENU_HOJE,
    MENU_MEUS_REMEDIOS,
    MENU_OUVIR,
)
from core.config import get_settings
from core.logging_config import configure_logging
from services.notification_service import send_reminder
from services.scheduler_service import SchedulerService

configure_logging()
logger = logging.getLogger(__name__)


def _menu_pattern(label: str) -> str:
    return f"^{re.escape(label)}$"


def build_application() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado. Preencha o .env (ver .env.example).")

    application = Application.builder().token(settings.telegram_bot_token).build()

    scheduler = SchedulerService(notify_callback=send_reminder)
    application.bot_data["scheduler_service"] = scheduler

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("ajuda", start.help_command))
    application.add_handler(CommandHandler("vincular", caregivers.link_command))
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_AJUDA)), start.help_command))

    application.add_handler(build_cadastro_conversation())
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_MEUS_REMEDIOS)), list_medications_handler))
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_HOJE)), reminders.today))
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_OUVIR)), reminders.listen_reminders))
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_HISTORICO)), reminders.history))
    application.add_handler(MessageHandler(filters.Regex(_menu_pattern(MENU_CONFIG)), accessibility.settings))

    application.add_handler(CallbackQueryHandler(reminders.confirm_callback, pattern=r"^confirm:"))
    application.add_handler(CallbackQueryHandler(reminders.snooze_menu_callback, pattern=r"^snooze_menu:"))
    application.add_handler(CallbackQueryHandler(reminders.snooze_callback, pattern=r"^snooze:\d"))
    application.add_handler(CallbackQueryHandler(reminders.not_taken_callback, pattern=r"^not_taken:"))
    application.add_handler(
        CallbackQueryHandler(accessibility.toggle_accessibility_callback, pattern=r"^config:toggle_accessibility$")
    )
    application.add_handler(CallbackQueryHandler(caregivers.menu_callback, pattern=r"^caregiver:menu$"))
    application.add_handler(CallbackQueryHandler(caregivers.invite_callback, pattern=r"^caregiver:invite$"))
    application.add_handler(CallbackQueryHandler(caregivers.list_callback, pattern=r"^caregiver:list$"))
    application.add_handler(CallbackQueryHandler(caregivers.revoke_callback, pattern=r"^caregiver:revoke:"))
    application.add_handler(CallbackQueryHandler(patients.confirm_callback, pattern=r"^patient_invite:confirm:"))
    application.add_handler(CallbackQueryHandler(patients.cancel_callback, pattern=r"^patient_invite:cancel:"))
    application.add_handler(CallbackQueryHandler(patients.treatment_listen_callback, pattern=r"^treatment_listen:"))
    application.add_handler(CallbackQueryHandler(patients.treatment_details_callback, pattern=r"^treatment_details:"))

    return application


def main() -> None:
    application = build_application()
    scheduler: SchedulerService = application.bot_data["scheduler_service"]
    scheduler.start()
    logger.info("Hora do Remédio bot iniciando (polling)...")
    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
