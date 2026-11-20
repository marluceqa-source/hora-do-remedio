from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

MENU_MEUS_REMEDIOS = "💊 Meus Remédios"
MENU_ADICIONAR = "➕ Adicionar Remédio"
MENU_HOJE = "📅 Remédios de Hoje"
MENU_OUVIR = "🔊 Ouvir Lembretes"
MENU_HISTORICO = "📊 Histórico"
MENU_CONFIG = "⚙️ Configurações"
MENU_AJUDA = "❓ Ajuda"

_COMMON_TIMES = ["06:00", "08:00", "12:00", "18:00", "20:00", "22:00"]
_INTERVAL_OPTIONS = [4, 6, 8, 12]
_WEEKDAYS = [("mon", "Seg"), ("tue", "Ter"), ("wed", "Qua"), ("thu", "Qui"), ("fri", "Sex"), ("sat", "Sáb"), ("sun", "Dom")]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [MENU_MEUS_REMEDIOS, MENU_ADICIONAR],
            [MENU_HOJE, MENU_OUVIR],
            [MENU_HISTORICO, MENU_CONFIG],
            [MENU_AJUDA],
        ],
        resize_keyboard=True,
    )


def recurrence_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌞 Diariamente", callback_data="recurrence:daily")],
            [InlineKeyboardButton("📆 Dias da semana", callback_data="recurrence:weekly")],
            [InlineKeyboardButton("⏱️ Intervalo em horas", callback_data="recurrence:interval")],
        ]
    )


def time_choice_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(t, callback_data=f"time:{t}") for t in _COMMON_TIMES[i : i + 2]]
        for i in range(0, len(_COMMON_TIMES), 2)
    ]
    rows.append([InlineKeyboardButton("✏️ Outro horário", callback_data="time:custom")])
    return InlineKeyboardMarkup(rows)


def interval_choice_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{h}h", callback_data=f"interval:{h}") for h in _INTERVAL_OPTIONS]]
    rows.append([InlineKeyboardButton("✏️ Outro intervalo", callback_data="interval:custom")])
    return InlineKeyboardMarkup(rows)


def weekdays_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for code, label in _WEEKDAYS:
        mark = "✅ " if code in selected else ""
        row.append(InlineKeyboardButton(f"{mark}{label}", callback_data=f"weekday:{code}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("➡️ Concluir seleção", callback_data="weekday:done")])
    return InlineKeyboardMarkup(rows)


def yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Sim", callback_data=yes_data), InlineKeyboardButton("❌ Não", callback_data=no_data)]]
    )


def snooze_options_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("5 min", callback_data=f"snooze:{reminder_id}:5"),
                InlineKeyboardButton("10 min", callback_data=f"snooze:{reminder_id}:10"),
            ],
            [
                InlineKeyboardButton("15 min", callback_data=f"snooze:{reminder_id}:15"),
                InlineKeyboardButton("30 min", callback_data=f"snooze:{reminder_id}:30"),
            ],
        ]
    )


def confirm_cancel_keyboard(confirm_data: str, cancel_data: str = "cadastro:cancelar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirmar cadastro", callback_data=confirm_data),
                InlineKeyboardButton("❌ Cancelar", callback_data=cancel_data),
            ]
        ]
    )
