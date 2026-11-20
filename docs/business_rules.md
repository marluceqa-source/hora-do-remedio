# Regras de negócio — Hora do Remédio

Cada regra lista o comportamento esperado, onde é aplicada no código e, quando houver, o
teste automatizado que a cobre.

| Regra | Comportamento esperado | Implementação | Teste |
|---|---|---|---|
| **RN01** | Um usuário pode cadastrar vários medicamentos. | [`services/medication_service.py`](../services/medication_service.py) — sem limite de quantidade por `user_id`. | `test_medication_service.py` |
| **RN02** | Cada medicamento pode ter vários horários. | `MedicationCreate.schedules` exige `min_length=1`; aceita N horários. | CT04 (`test_medications.py`) |
| **RN03** | Um lembrete não é enviado após o encerramento do tratamento. | `SchedulerService._fire` compara a data atual (no fuso do `Schedule`) com `medication.end_date`. | CT15 (`test_scheduler_firing.py`) |
| **RN04** | A administração só é registrada mediante confirmação explícita. | `reminder_service.confirm` só é chamado a partir do botão "✅ Tomei" ou de `POST /reminders/{id}/confirm`. | CT06 |
| **RN05** | Confirmação duplicada é impedida. | `reminder_service.confirm` levanta `ReminderAlreadyConfirmedError` se `status == "confirmed"`. | CT07 |
| **RN06** | O adiamento não altera o horário original. | `reminder_service.snooze` só incrementa `snooze_count`; `scheduled_datetime` nunca é reescrito. | CT08 |
| **RN07** | Os agendamentos respeitam o fuso horário do usuário/medicamento. | `Schedule.timezone` é usado em `_build_trigger` e em `_fire` (via `ZoneInfo`), nunca o fuso do servidor. | CT14 |
| **RN08** | Os agendamentos persistem após reinicialização. | `SchedulerService.reload_jobs()` reconstrói todos os jobs a partir do banco a cada início de processo. | CT11, CT39 |
| **RN09** | Cada usuário só acessa seus próprios dados. | Toda rota de `api/routes/` filtra por `Medication.user_id == user.id` (ou equivalente via `ReminderEvent`→`Medication`). | CT12, CT41 |
| **RN10** | Fotografias e dados identificados por OCR exigem validação. | `receive_photo` nunca sobrescreve o nome digitado; o texto do OCR é só exibido para conferência (`photo_ocr:sim/nao`). | CT19, CT20 |
| **RN11** | Informações reconhecidas por voz exigem confirmação; valores ausentes/ambíguos não são assumidos. | `receive_name_voice` só aceita a transcrição após confirmação explícita; transcrição vazia pede nova tentativa. | CT21, CT26 |
| **RN12** | Ausência de resposta não significa necessariamente que o medicamento não foi tomado. | Status `"pending"`/`"delivered"` é distinto de `"not_taken"` em todo o modelo e nos relatórios. | `test_report_service.py` |
| **RN13** | O bot não prescreve nem recomenda alterações de dosagem. | Nenhum fluxo do bot sugere dosagem; `dosage`/`quantity` são sempre informados pelo próprio usuário. | Revisão manual dos textos em `bot/handlers/` |
| **RN14** | O cuidador só acessa dados mediante autorização válida. | `caregiver_service.find_patient_access_for_caregiver` exige registro não revogado. | CT28 |
| **RN15** | Medicamentos inativos não geram novos lembretes. | `SchedulerService.reload_jobs()` filtra `Medication.active.is_(True))`. | CT11 (`test_ct11_reload_jobs_ignores_inactive_medications`) |
| **RN16** | Exclusão exige confirmação explícita. | `DELETE /medications/{id}` exige `confirm=true`, senão retorna 400. | CT09 |
| **RN17** | Registros seguem uma política de retenção configurável. | `DATA_RETENTION_DAYS` em `.env`/`core/config.py` — **ver limitação abaixo**. | — |
| **RN18** | Falhas de envio são registradas sem gerar duplicidade. | Índice único `(medication_id, scheduled_datetime)` em `ReminderEvent` + captura de `IntegrityError` em `_fire`; falhas de Telegram são logadas sem marcar `"delivered"`. | CT13, CT18, CT42 |

## Limitações conhecidas

- **RN17**: a variável `DATA_RETENTION_DAYS` existe na configuração, mas **nenhum job de expurgo automático foi implementado** — a aplicação não apaga registros antigos sozinha. Ver [architecture.md](architecture.md#limitações) para o que seria necessário para fechar essa lacuna.
- **RN13**: a garantia é por **ausência de funcionalidade** (não existe código que sugira dosagem), não por um filtro ativo de conteúdo — não há validação automática que impeça um texto de observação digitado pelo próprio usuário de conter esse tipo de informação.
