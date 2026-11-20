# Requisitos Funcionais

> ⚠️ **Atenção à numeração.** O bot/API e o portal vieram de **duas especificações
> independentes**, cada uma com sua própria numeração `RFxx`. Portanto **`RF02` do bot não é
> `RF02` do portal.** As duas tabelas abaixo são espaços de numeração separados.

---

## Bot e API (paciente)

| ID | Requisito | Onde está |
|---|---|---|
| **RF02** | Cadastro de medicamentos com horários; descrição opcional falada (TTS) no lembrete. | `api/routes/medications.py`, `api/schemas/medication.py` |
| **RF03** | Cadastro por **fotografia** da embalagem, com OCR local. | `bot/handlers/medications.py`, `api/schemas/medication.py` |
| **RF04** | Cadastro por **voz**, com transcrição local (STT). | `services/speech_to_text_service.py` |
| **RF07** | Confirmação da administração de uma dose. | `api/routes/reminders.py` |
| **RF08** | Adiamento do lembrete (5/10/15/30 min) e histórico de doses. | `api/routes/reminders.py`, `api/schemas/reminder.py` |
| **RF09** | Consulta dos lembretes do dia e do histórico com filtro por dia/semana/mês. | `api/routes/reminders.py`, `api/routes/history.py` |
| **RF10** | Relatórios de **adesão declarada** (JSON ou CSV). | `api/routes/reports.py` |
| **RF12** | Autorização e revogação de **cuidadores**, e consulta de dados do paciente pelo cuidador. | `api/routes/caregivers.py` |
| **RF14** | Documentação OpenAPI servida a partir de **fonte única de verdade**. | `api/main.py`, `docs/openapi.yaml` |

`docs/openapi.yaml` é exportado do mesmo schema que alimenta `/openapi.json`, `/docs` e
`/redoc` (via `scripts/export_openapi.py`) — não existe uma segunda descrição da API para
sair de sincronia.

---

## Portal de profissionais

| ID | Requisito | Onde está |
|---|---|---|
| **RF01** | Autenticação do profissional: cadastro, login em duas etapas, **MFA TOTP**, logout, recuperação de acesso, e verificação pelo administrador. | `api/routes/professional_auth.py`, `api/routes/admin.py` |
| **RF02** | **Painel operacional**: pacientes, tratamentos e confirmações declaradas. | `api/routes/dashboard.py` |
| **RF03** | Cadastro de paciente (quem cadastra fica automaticamente vinculado). | `api/routes/patients.py`, `services/patient_service.py` |
| **RF04** | Geração de **convite único e temporário** para vincular o paciente ao Telegram. | `api/routes/patients.py`, `services/patient_service.py` |
| **RF05** | Cadastro de medicamento/esquema terapêutico como **rascunho**. | `api/routes/patients.py` |
| **RF06** | **Ativação** do plano validado + notificação ao paciente no Telegram. | `api/routes/treatment_medications.py`, `services/notification_service.py` |
| **RF07** | Edição com **versionamento**, suspensão e consulta do histórico de versões. | `api/routes/treatment_medications.py`, `services/treatment_service.py` |
| **RF08** | Consulta do histórico de doses do paciente. | `api/routes/patients.py` |

Na RF06, a notificação ao paciente roda **após** a resposta HTTP: ela não trava nem derruba a
requisição do profissional se o Telegram estiver indisponível.

Na RF08, a resposta é explicitamente de **adesão declarada**
([RN12](Regras-de-Negocio-Bot-e-API)): silêncio do paciente não é registrado como "não tomou".

---

## Telas do portal

| Rota | Tela |
|---|---|
| `/login` | Login em duas etapas (senha → MFA), com QR Code no primeiro acesso. |
| `/signup` | Autocadastro do profissional (gera solicitação, não acesso). |
| `/password-reset` | Recuperação de acesso. |
| `/` | Painel (dashboard). |
| `/patients` · `/patients/new` · `/patients/:id` | Lista, cadastro e detalhe do paciente (com QR Code do convite). |
| `/patients/:id/medications/new` | Cadastro de tratamento (rascunho). |
| `/treatment-medications/:id` | Detalhe do tratamento, ativação/suspensão e versões anteriores. |
| `/profile` | Perfil do profissional. |
| `/admin` | Verificação de profissionais e trilha de auditoria. |

---

## Próximo

- [Regras de Negócio — Bot e API](Regras-de-Negocio-Bot-e-API)
- [Regras de Negócio — Portal](Regras-de-Negocio-Portal)
