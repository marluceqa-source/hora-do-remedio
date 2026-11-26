# Regras de Negócio — Bot e API (RN01–RN18)

Regras do produto voltado ao **paciente**. Cada regra aponta onde está implementada e onde é
testada, para que a wiki não vire uma promessa sem lastro no código.

> Fonte no repositório: [`docs/business_rules.md`](../blob/main/docs/business_rules.md)

---

## Cadastro de medicamentos

| ID | Regra | Onde está garantida | Teste |
|---|---|---|---|
| **RN01** | Um usuário pode cadastrar vários medicamentos. | `services/medication_service.py` — sem limite por `user_id`. | `test_medication_service.py` |
| **RN02** | Cada medicamento pode ter vários horários. | `MedicationCreate.schedules` exige `min_length=1` e aceita N horários. | CT04 |
| **RN16** | Exclusão exige confirmação explícita. | `DELETE /medications/{id}` exige `confirm=true`; sem isso retorna 400. | CT09 |

## Lembretes e agendamento

| ID | Regra | Onde está garantida | Teste |
|---|---|---|---|
| **RN03** | Lembrete não é enviado após o encerramento do tratamento. | `SchedulerService._fire` compara a data atual (no fuso do `Schedule`) com `medication.end_date`. | CT15 |
| **RN07** | Agendamentos respeitam o fuso do usuário/medicamento, nunca o do servidor. | `Schedule.timezone` é usado em `_build_trigger` e `_fire` via `ZoneInfo`. | CT14 |
| **RN08** | Agendamentos persistem após reinicialização. | `SchedulerService.reload_jobs()` reconstrói todos os jobs a partir do banco a cada início de processo. | CT11, CT39 |
| **RN15** | Medicamentos inativos não geram novos lembretes. | `reload_jobs()` filtra `Medication.active.is_(True)`. | CT11 |
| **RN18** | Falhas de envio são registradas sem gerar duplicidade. | Índice único `(medication_id, scheduled_datetime)` em `ReminderEvent` + captura de `IntegrityError`; falha de Telegram é logada sem marcar `delivered`. | CT13, CT18, CT42 |

**Recorrências suportadas:** diária, por dias específicos da semana, ou por intervalo em horas.

## Confirmação de doses

| ID | Regra | Onde está garantida | Teste |
|---|---|---|---|
| **RN04** | A administração só é registrada mediante confirmação explícita. | `reminder_service.confirm` só é alcançado pelo botão "✅ Tomei" ou por `POST /reminders/{id}/confirm`. | CT06 |
| **RN05** | Confirmação duplicada é impedida. | `reminder_service.confirm` levanta `ReminderAlreadyConfirmedError` se `status == "confirmed"`. | CT07 |
| **RN06** | O adiamento não altera o horário original. | `reminder_service.snooze` só incrementa `snooze_count`; `scheduled_datetime` nunca é reescrito. | CT08 |
| **RN12** | **Ausência de resposta não significa que o medicamento não foi tomado.** | Os status `pending` e `delivered` são distintos de `not_taken` em todo o modelo e nos relatórios. | `test_report_service.py` |

> **RN12 é a regra mais importante do sistema do ponto de vista clínico.** Todo relatório de
> adesão é explicitamente de **adesão declarada**, não de adesão real. Silêncio é silêncio.

**Status possíveis de um `ReminderEvent`:**
`pending` · `delivered` · `confirmed` · `not_taken` · `snoozed` · `expired`

`expired` é atribuído pelo job `expire-reminders` quando a janela de resposta
(`REMINDER_EXPIRE_HOURS`, padrão 24 h) fecha sem resposta. Conta como **sem confirmação**,
nunca como dose não tomada (RN12).

**Opções de adiamento permitidas:** 5, 10, 15 ou 30 minutos.

## Entrada de dados por foto e por voz

| ID | Regra | Onde está garantida | Teste |
|---|---|---|---|
| **RN10** | Fotografias e dados identificados por OCR exigem validação. | `receive_photo` nunca sobrescreve o nome digitado; o texto do OCR é só exibido para conferência (`photo_ocr:sim/nao`). | CT19, CT20 |
| **RN11** | Informações reconhecidas por voz exigem confirmação; valores ausentes ou ambíguos não são assumidos. | `receive_name_voice` só aceita a transcrição após confirmação explícita; transcrição vazia pede nova tentativa. | CT21, CT26 |

OCR (Tesseract) e STT (faster-whisper) rodam **localmente**, sem enviar imagem ou áudio do
paciente para serviços de terceiros.

## Acesso a dados

| ID | Regra | Onde está garantida | Teste |
|---|---|---|---|
| **RN09** | Cada usuário só acessa seus próprios dados. | Toda rota de `api/routes/` filtra por `Medication.user_id == user.id` (ou equivalente via `ReminderEvent` → `Medication`). | CT12, CT41 |
| **RN14** | O cuidador só acessa dados mediante autorização válida. | `caregiver_service.find_patient_access_for_caregiver` exige registro não revogado. | CT28 |

O cuidador é autorizado por **código de convite** digitado no bot (`/vincular CODIGO`) e pode
ser revogado pelo paciente a qualquer momento.

## Limites de escopo e retenção

| ID | Regra | Situação |
|---|---|---|
| **RN13** | O bot não prescreve nem recomenda alterações de dosagem. | Garantida por **ausência de funcionalidade** — ver [Limitações Conhecidas](Limitacoes-Conhecidas). |
| **RN17** | Registros seguem uma política de retenção configurável. | `DATA_RETENTION_DAYS` (padrão: **365 dias**) existe na configuração, mas **o expurgo automático não foi implementado** — ver [Limitações Conhecidas](Limitacoes-Conhecidas). |

---

## Próximo

- [Regras de Negócio — Portal](Regras-de-Negocio-Portal) (RN19–RN32)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
