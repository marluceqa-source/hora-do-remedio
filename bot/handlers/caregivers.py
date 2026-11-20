"""Suporte a cuidadores autorizados no bot (RF12).

Vínculo por código de convite: o paciente gera um código válido por 10 minutos e o cuidador
o envia via `/vincular CODIGO`. Os códigos pendentes vivem em `bot_data` (em memória) — se o
bot reiniciar, convites não resgatados expiram e precisam ser gerados novamente.
"""

import logging
import secrets
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.connection import SessionLocal
from services import caregiver_service, medication_service

logger = logging.getLogger(__name__)

_INVITE_TTL_SECONDS = 600


def _invites(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.bot_data.setdefault("caregiver_invites", {})


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Convidar cuidador", callback_data="caregiver:invite")],
            [InlineKeyboardButton("📋 Meus cuidadores", callback_data="caregiver:list")],
        ]
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 Cuidadores autorizados podem acompanhar seus medicamentos (RF12).",
        reply_markup=_menu_keyboard(),
    )


async def invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    code = secrets.token_hex(3).upper()
    _invites(context)[code] = {
        "owner_telegram_id": update.effective_user.id,
        "expires_at": time.time() + _INVITE_TTL_SECONDS,
    }
    await query.edit_message_text(
        "Peça para o seu cuidador enviar esta mensagem para este bot, em até 10 minutos:\n\n"
        f"/vincular {code}",
        reply_markup=_menu_keyboard(),
    )


async def list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = SessionLocal()
    try:
        owner = medication_service.get_or_create_user(db, update.effective_user.id)
        accesses = caregiver_service.list_active_access(db, owner)
        if not accesses:
            await query.edit_message_text(
                "Você ainda não tem cuidadores autorizados.", reply_markup=_menu_keyboard()
            )
            return

        lines = [f"- cuidador #{access.caregiver_id} ({access.permission})" for access in accesses]
        keyboard_rows = [
            [InlineKeyboardButton(f"❌ Revogar #{access.id}", callback_data=f"caregiver:revoke:{access.id}")]
            for access in accesses
        ]
        keyboard_rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data="caregiver:menu")])
        await query.edit_message_text(
            "📋 Seus cuidadores:\n\n" + "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard_rows)
        )
    finally:
        db.close()


async def revoke_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    access_id = int(query.data.split(":")[2])
    db = SessionLocal()
    try:
        owner = medication_service.get_or_create_user(db, update.effective_user.id)
        access = caregiver_service.get_owned_access(db, access_id, owner)
        if access is None:
            await query.answer("Autorização não encontrada.", show_alert=True)
            return
        caregiver_service.revoke_access(db, access)
    finally:
        db.close()
    await query.edit_message_text("✅ Acesso revogado.", reply_markup=_menu_keyboard())


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Use: /vincular CODIGO (peça o código a quem vai cuidar de você acompanhar).")
        return

    code = context.args[0].strip().upper()
    invite = _invites(context).get(code)
    if invite is None or invite["expires_at"] < time.time():
        await update.message.reply_text("Código inválido ou expirado. Peça um novo convite em ⚙️ Configurações.")
        return

    db = SessionLocal()
    try:
        owner = medication_service.get_or_create_user(db, invite["owner_telegram_id"])
        if owner.telegram_user_id == update.effective_user.id:
            await update.message.reply_text("Você não pode se vincular como seu próprio cuidador.")
            return
        try:
            caregiver_service.grant_access(db, owner, update.effective_user.id, permission="view")
        except caregiver_service.CaregiverAccessError as exc:
            await update.message.reply_text(str(exc))
            return
    finally:
        db.close()

    del _invites(context)[code]
    await update.message.reply_text("✅ Vínculo confirmado! Agora você pode acompanhar os medicamentos dessa pessoa.")
