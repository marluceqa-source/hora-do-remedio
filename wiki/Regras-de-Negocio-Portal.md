# Regras de Negócio — Portal de Profissionais (RN19–RN32)

Regras do portal web usado por **profissionais de saúde**. O portal prescreve; o bot executa.

> **Correção nesta versão** (card [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)).
> **RN29** e **RN31** estavam ausentes desta página e **existem** na especificação — as duas já
> implementadas, só não documentadas. E **RN30 estava com o texto errado**: a página descrevia
> sessão revogável e bloqueio por tentativas, mas a regra é *"o bot não deverá alterar
> prescrições por conta própria"*. As três estão corrigidas abaixo, com o texto da
> especificação.

---

## Identidade e sessão do profissional

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN19** | Apenas profissionais autorizados poderão registrar planos associados a pacientes. | `core/professional_security.require_roles` + `verification_status`; `services/professional_auth_service.py`. |

**Decisão de arquitetura associada (não é uma RN):** a autenticação do profissional é
independente da do paciente — `core/professional_security.py` usa segredo e mecanismo próprios
(`PROFESSIONAL_SESSION_SECRET_KEY`), separados de `core/security.py`, de modo que vazar uma não
compromete a outra. Isso atende à **seção 18** do prompt do portal (segurança), e esta página
já a apresentou como se fosse o texto de RN19.

**Parâmetros padrão:**

| Configuração | Padrão | Significado |
|---|---|---|
| `PROFESSIONAL_SESSION_EXPIRE_MINUTES` | 480 (8 h) | Validade da sessão. |
| `PROFESSIONAL_MFA_PRE_AUTH_EXPIRE_MINUTES` | 5 | Janela para concluir o MFA após a senha. |
| `PROFESSIONAL_MAX_FAILED_LOGINS` | 5 | Tentativas antes do bloqueio. |
| `PROFESSIONAL_LOCKOUT_MINUTES` | 15 | Duração do bloqueio. |
| `PROFESSIONAL_PASSWORD_RESET_EXPIRE_MINUTES` | 30 | Validade do token de recuperação. |

O **MFA (TOTP) é obrigatório**: no primeiro acesso o profissional é levado ao fluxo de
configuração do autenticador antes de obter qualquer sessão. A sessão é revogável no servidor
(só o hash do token é persistido) e o login bloqueia após tentativas sucessivas. Tudo isso vem
da **seção 18** do prompt do portal, não de uma RN própria — detalhes em
[Segurança e Privacidade](Seguranca-e-Privacidade).

> **O cadastro não concede permissão clínica.** Um profissional recém-cadastrado entra com
> `verification_status = pending` e precisa ser verificado por um administrador.

## Vínculo paciente ↔ profissional

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN21** | O vínculo entre paciente e profissional é explícito e controla quem vê o quê. | `PatientProfessionalLink` (`database/models.py`). |
| **RN22** | O profissional só acessa pacientes com vínculo ativo. | Toda rota de `api/routes/patients.py` filtra pelo vínculo; quem cadastra o paciente já fica vinculado (`services/patient_service.py`). |
| **RN31** | A revogação de vínculos deverá bloquear novos acessos aos dados protegidos. | Mesmo filtro de RN22: `authorization_status == "active"` em `list_authorized_patients` e `get_authorized_patient`. Marcar um vínculo como `revoked` corta o acesso **na consulta seguinte**, sem expurgo nem invalidação de sessão. |

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

## Limites do que o sistema conclui e do que o bot faz

| ID | Regra | Onde está garantida |
|---|---|---|
| **RN29** | A ausência de confirmação não deverá ser classificada automaticamente como ausência de administração. | `services/dashboard_service.py` — `_UNCONFIRMED_STATUSES` (`pending`, `delivered`, `snoozed`, `expired`) é contado **à parte** de `not_taken`, no painel e no histórico. |
| **RN30** | O bot não deverá alterar prescrições por conta própria. | Garantida por **ausência de funcionalidade**: `bot/` não importa `treatment_service` e não escreve em entidade de tratamento. Os fluxos de `bot/handlers/patients.py` são só de leitura — ouvir em áudio e ver detalhes. |

> **RN29 é a RN12 do bot, na numeração do portal.** As duas especificações enunciam a mesma
> garantia, e é a mais importante do sistema do ponto de vista clínico: silêncio é silêncio,
> nunca "não tomou". Ver [RN12](Regras-de-Negocio-Bot-e-API).
>
> **RN30 é a contraparte de [RN13](Regras-de-Negocio-Bot-e-API)** ("o bot não prescreve nem
> recomenda alterações de dosagem"), aplicada agora às prescrições que vêm do portal. Como
> RN13, ela é garantida pela ausência de código que faça isso — não por um bloqueio ativo.

A consulta da trilha de auditoria é **restrita a administradores**
(`GET` em `api/routes/admin.py`). Essa rota expõe auditoria, **nunca dados clínicos de
pacientes**.

---

## O que a conferência da especificação revelou

O card [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) existia porque
RN29 e RN31 não apareciam nem nesta página nem no código, e não se sabia se eram regras
perdidas ou números vagos. **Eram regras perdidas** — e a conferência achou mais do que isso:

| Regra | Situação antes | Situação agora |
|---|---|---|
| **RN29** | Ausente da documentação | Existe, e **já estava implementada** — como RN12, na outra numeração. |
| **RN31** | Ausente da documentação | Existe, e **já estava implementada** — pelo mesmo filtro de RN22. |
| **RN30** | Documentada como "sessão revogável e bloqueio por tentativas" | **Texto errado.** A regra é "o bot não deverá alterar prescrições por conta própria". O que a página descrevia vem da seção 18 (segurança), não de uma RN. |

Com isso, **31 das 32 regras estão marcadas no código** — só RN17 fica de fora, porque não há
expurgo implementado para marcar ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)).

### Divergências que permanecem

Conferindo o resto da lista contra a especificação, **outras quatro regras estão enunciadas
aqui com o texto da implementação, não com o da especificação**:

| ID | Texto da especificação | O que esta página diz |
|---|---|---|
| **RN19** | "Apenas profissionais autorizados poderão registrar planos associados a pacientes." | *(corrigida nesta versão)* |
| **RN21** | "Um paciente poderá estar vinculado a vários profissionais, conforme autorização." | Fala do vínculo controlar acesso — perde a **multiplicidade**. |
| **RN26** | "Apenas planos autorizados e ativos gerarão novos lembretes." | Descreve a materialização de `Medication`/`Schedule` — o *como*, não o *quê*. |
| **RN27** | "Mudanças deverão preservar registros anteriores **e trilhas de auditoria**." | Fala só do versionamento; omite a auditoria. |

Nenhuma delas é erro de implementação — o comportamento está certo. É a **redação** que
descreve a solução em vez da regra, o que torna difícil verificar se a regra foi cumprida sem
reler o código. Está em [#46](https://github.com/marluceqa-source/hora-do-remedio/issues/46).

---

## Próximo

- [Papéis e Permissões](Papeis-e-Permissoes)
- [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento)
- [Segurança e Privacidade](Seguranca-e-Privacidade)
