# Regras de Negócio — Portal de Profissionais (RN19–RN32)

Regras do portal web usado por **profissionais de saúde**. O portal prescreve; o bot executa.

---

## Identidade e sessão do profissional

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN19** | A autenticação do profissional é independente da do paciente. Vazar uma não compromete a outra. | `core/professional_security.py` usa segredo e mecanismo próprios (`PROFESSIONAL_SESSION_SECRET_KEY`), separados de `core/security.py`. |
| **RN30** | A sessão é revogável no servidor e o login é bloqueado após tentativas sucessivas. | `services/professional_auth_service.py` — só o **hash** do token de sessão é persistido em `ProfessionalSession`; bloqueio após `PROFESSIONAL_MAX_FAILED_LOGINS` tentativas. |

**Parâmetros padrão:**

| Configuração | Padrão | Significado |
|---|---|---|
| `PROFESSIONAL_SESSION_EXPIRE_MINUTES` | 480 (8 h) | Validade da sessão. |
| `PROFESSIONAL_MFA_PRE_AUTH_EXPIRE_MINUTES` | 5 | Janela para concluir o MFA após a senha. |
| `PROFESSIONAL_MAX_FAILED_LOGINS` | 5 | Tentativas antes do bloqueio. |
| `PROFESSIONAL_LOCKOUT_MINUTES` | 15 | Duração do bloqueio. |
| `PROFESSIONAL_PASSWORD_RESET_EXPIRE_MINUTES` | 30 | Validade do token de recuperação. |

O **MFA (TOTP) é obrigatório**: no primeiro acesso o profissional é levado ao fluxo de
configuração do autenticador antes de obter qualquer sessão. Detalhes em
[Segurança e Privacidade](Seguranca-e-Privacidade).

> **O cadastro não concede permissão clínica.** Um profissional recém-cadastrado entra com
> `verification_status = pending` e precisa ser verificado por um administrador.

## Vínculo paciente ↔ profissional

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN21** | O vínculo entre paciente e profissional é explícito e controla quem vê o quê. | `PatientProfessionalLink` (`database/models.py`). |
| **RN22** | O profissional só acessa pacientes com vínculo ativo. | Toda rota de `api/routes/patients.py` filtra pelo vínculo; quem cadastra o paciente já fica vinculado (`services/patient_service.py`). |

**Status de autorização do vínculo:** `pending` · `active` · `revoked`

## Vínculo do paciente ao Telegram

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN23** | O convite de vínculo ao Telegram é único e temporário. | `PatientInvitation` — só o hash do token é persistido; expira em `PATIENT_INVITE_EXPIRE_MINUTES` (padrão: **30 min**). |
| **RN24** | Convite já consumido não pode ser reutilizado. | `services/patient_service.py`; teste em `test_patient_service.py`. |

O convite é entregue como **deep link nativo do Telegram** (`https://t.me/<bot>?start=<token>`),
apresentado no portal também como QR Code. A escolha é de acessibilidade: o paciente **toca
no link ou aponta a câmera**, sem digitar código nenhum.

**Status de vínculo do paciente:** `not_linked` · `invited` · `linked`

## Ciclo de vida do tratamento

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN25** | Um tratamento em rascunho **não gera lembrete nenhum**. | `api/routes/patients.py` cria sempre como `draft`; teste em `test_treatment_service.py`. |
| **RN26** | A ativação materializa as entidades reais (`Medication`/`Schedule`) consumidas pelo agendador. | `services/treatment_service.py` — não há lógica de agendamento duplicada no portal. |
| **RN27** | Editar um tratamento **ativo** cria uma nova versão, em vez de sobrescrever a anterior. | `services/treatment_service.py`; `previous_version_id` encadeia as versões. O histórico de `ReminderEvent` já emitido permanece intacto. |
| **RN28** | Suspender um tratamento interrompe os lembretes. | A suspensão marca o `Medication` como `active = False`; o agendador já respeita isso via [RN15](Regras-de-Negocio-Bot-e-API). |

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN20** | **A ativação clínica respeita as atribuições do profissional — só um médico pode ativar.** | `services/treatment_service.py`; `api/routes/treatment_medications.py` retorna **403** com mensagem explícita para outros papéis. O portal também desabilita o botão e explica o motivo. |

A ativação exige, além do papel correto, que **o paciente já esteja vinculado ao Telegram** —
sem isso não há para onde enviar o lembrete.

**Status de um tratamento:** `draft` · `pending_validation` · `active` · `suspended` · `closed`

Detalhes das transições em [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento).

## Auditoria

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN32** | Toda operação sensível do portal é auditável. | `services/audit_service.py` + tabela `AuditLog` (registra ator, papel do ator, ação e momento). |

A consulta da trilha de auditoria é **restrita a administradores**
(`GET` em `api/routes/admin.py`). Essa rota expõe auditoria, **nunca dados clínicos de
pacientes**.

---

## Lacunas de numeração

**RN29 e RN31 não têm marcação correspondente no código.** Elas podem existir na especificação
original do portal sem terem sido anotadas na implementação, ou podem simplesmente não existir.
Isso está registrado como pendência em [Limitações Conhecidas](Limitacoes-Conhecidas) — a wiki
não inventa o conteúdo delas.

---

## Próximo

- [Papéis e Permissões](Papeis-e-Permissoes)
- [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento)
- [Segurança e Privacidade](Seguranca-e-Privacidade)
