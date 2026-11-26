# Matriz de Rastreabilidade

Quem veio de onde, onde está implementado, onde é verificado e qual card acompanha. Esta é a
página que impede a documentação de virar promessa.

---

## 1. Por que rastrear

> **Rastreabilidade:** "1. Em geral: a capacidade de estabelecer relações explícitas entre
> produtos de trabalho relacionados ou itens dentro de produtos de trabalho. 2. Em ER: a
> capacidade de rastrear um requisito **de volta às suas origens**, **para frente, até sua
> implementação** no projeto e no código e seus testes associados, e **até os requisitos dos
> quais ele depende** (e vice-versa)."
> — Glossário, verbete *Rastreabilidade*, p. 26

O Handbook de Gerenciamento de Requisitos cita como razões, entre outras, a **análise de
cobertura** — "verificar se todos os requisitos e artefatos de desenvolvimento subsequentes
foram considerados para que o produto desejado possa ser completamente registrado, desenvolvido
e testado" — e a análise de valor agregado (§6.1, p. 113). A análise de cobertura é o uso
principal desta página; a análise de impacto aparece na [seção 6](#6-análise-de-impacto).

---

## 2. Dimensões e tipos de relação adotados

O handbook diferencia cinco dimensões de rastreabilidade (§6.2, p. 115). O que este projeto
cobre:

| Dimensão (§6.2) | Coberta aqui? | Como |
|---|---|---|
| Entre requisitos **no mesmo nível** | Sim | RF ↔ RN nas tabelas abaixo |
| Entre requisitos em **níveis diferentes** | Sim | Prompt master → RF/RN → HU → critérios de aceitação |
| Entre **versões** de um requisito | Parcial | Histórico do Git da wiki e do repositório; não há atributo de versão por requisito — ver [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos) |
| **Para frente**, até código e testes | Sim | Colunas "Implementação" e "Verificação" |
| **Para trás**, até a origem | Sim | Coluna "Origem" |

O handbook adverte que uma única relação genérica do tipo `dependent_on` esconde o motivo da
dependência (§6.3, p. 115–116) e, ao mesmo tempo, recomenda **manter poucos tipos**
(dica, p. 118). Os tipos usados aqui são cinco:

| Tipo de relação | Significado neste projeto |
|---|---|
| `origina-se_de` | O requisito vem do prompt master, da especificação do portal ou de uma decisão de arquitetura. |
| `é_implementado_por` | Arquivo/módulo onde a regra é garantida. |
| `é_verificado_por` | Teste automatizado que falha se a regra for violada. |
| `refina` | Um requisito detalha outro (por exemplo, RN20 refina RF06 do portal). |
| `formaliza` | Um modelo formaliza um requisito textual — ver [Modelagem de Requisitos](Modelagem-de-Requisitos). |

### Rastreabilidade implícita e explícita

O handbook distingue documentação **implícita** (convenções de nomenclatura, estrutura de
documentos, glossários, referências) de **explícita** (relações deliberadamente estabelecidas)
— §6.4.1, p. 120. Este projeto usa as duas:

- **Implícita:** comentários `RNxx` no código e nomes de teste no padrão `test_ctNN_...`. É o que
  permitiu reconstruir as tabelas abaixo com `grep`, e não de memória.
- **Explícita:** esta página e as colunas "Onde está garantida" das páginas de regras de negócio.

---

## 3. Matriz principal — regras de negócio

`Marcação`: existe comentário `RNxx` no código (rastreabilidade implícita). `—` significa
ausente, não "não implementado".

| RN | Origem | Implementação | Marcação | Verificação | Card |
|---|---|---|---|---|---|
| **RN01** | Prompt §7 | `services/medication_service.py` | ✅ | `tests/api/test_medications.py` (CT01) | [#2](https://github.com/marluceqa-source/hora-do-remedio/issues/2) |
| **RN02** | Prompt §7 | `api/schemas/medication.py` | ✅ | CT04 | [#2](https://github.com/marluceqa-source/hora-do-remedio/issues/2) |
| **RN03** | Prompt §7 | `services/scheduler_service.py` | ✅ | CT15 | [#5](https://github.com/marluceqa-source/hora-do-remedio/issues/5) |
| **RN04** | Prompt §7 | `api/routes/reminders.py` | ✅ | CT06 | [#6](https://github.com/marluceqa-source/hora-do-remedio/issues/6) |
| **RN05** | Prompt §7 | `api/routes/reminders.py`, `services/reminder_service.py` | ✅ | CT07 | [#6](https://github.com/marluceqa-source/hora-do-remedio/issues/6) |
| **RN06** | Prompt §7 | `api/routes/reminders.py` | ✅ | CT08 | [#6](https://github.com/marluceqa-source/hora-do-remedio/issues/6) |
| **RN07** | Prompt §7 | `database/models.py`, `services/scheduler_service.py` | ✅ | CT14 | [#5](https://github.com/marluceqa-source/hora-do-remedio/issues/5) |
| **RN08** | Prompt §7 | `SchedulerService.reload_jobs()` | ✅ | CT11, CT39 | [#5](https://github.com/marluceqa-source/hora-do-remedio/issues/5) |
| **RN09** | Prompt §7 | `api/routes/*`, `services/professional_auth_service.py` | ✅ | CT12, CT41 | [#11](https://github.com/marluceqa-source/hora-do-remedio/issues/11) |
| **RN10** | Prompt §7 | `bot/handlers/medications.py` | ✅ | CT19, CT20 | [#3](https://github.com/marluceqa-source/hora-do-remedio/issues/3) |
| **RN11** | Prompt §7 | `bot/handlers/medications.py` | ✅ | CT21, CT26 | [#4](https://github.com/marluceqa-source/hora-do-remedio/issues/4) |
| **RN12** | Prompt §7 | `api/main.py`, `api/routes/reports.py`, `services/dashboard_service.py` | ✅ | `tests/unit/test_report_service.py` | [#7](https://github.com/marluceqa-source/hora-do-remedio/issues/7) |
| **RN13** | Prompt §7 | `api/main.py`, `database/models.py` (declaração) | ✅ | **nenhum** — garantida por ausência de funcionalidade | [#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) |
| **RN14** | Prompt §7 | `services/caregiver_service.py` | ✅ | `tests/unit/test_caregiver_service.py`, `tests/api/test_caregivers.py` | [#8](https://github.com/marluceqa-source/hora-do-remedio/issues/8) |
| **RN15** | Prompt §7 | `services/scheduler_service.py` | ✅ | CT11 | [#5](https://github.com/marluceqa-source/hora-do-remedio/issues/5) |
| **RN16** | Prompt §7 | `api/routes/medications.py` | ✅ | CT09 | — |
| **RN17** | Prompt §7 | `core/config.py` (só o parâmetro) | — | **nenhum** | [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22) |
| **RN18** | Prompt §7 | `services/notification_service.py`, `services/scheduler_service.py` | ✅ | CT13, CT18, CT42 | [#5](https://github.com/marluceqa-source/hora-do-remedio/issues/5), [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33) |
| **RN19** | Espec. do portal | `core/professional_security.py`, `services/professional_auth_service.py` | ✅ | `tests/unit/test_professional_auth_service.py` | [#12](https://github.com/marluceqa-source/hora-do-remedio/issues/12) |
| **RN20** | Espec. do portal | `api/routes/treatment_medications.py`, `services/treatment_service.py` | ✅ | `tests/unit/test_professional_rbac.py` | [#13](https://github.com/marluceqa-source/hora-do-remedio/issues/13) |
| **RN21** | Espec. do portal | `database/models.py` (`PatientProfessionalLink`) | ✅ | `tests/api/test_patients.py` | [#14](https://github.com/marluceqa-source/hora-do-remedio/issues/14) |
| **RN22** | Espec. do portal | `api/routes/patients.py`, `services/patient_service.py` | ✅ | `tests/api/test_patients.py` | [#14](https://github.com/marluceqa-source/hora-do-remedio/issues/14) |
| **RN23** | Espec. do portal | `database/models.py`, `services/patient_service.py` | ✅ | `tests/unit/test_patient_service.py` | [#14](https://github.com/marluceqa-source/hora-do-remedio/issues/14) |
| **RN24** | Espec. do portal | `services/patient_service.py` | ✅ | `tests/unit/test_patient_service.py` | [#14](https://github.com/marluceqa-source/hora-do-remedio/issues/14) |
| **RN25** | Espec. do portal | `api/routes/patients.py` | ✅ | `tests/unit/test_treatment_service.py` | [#15](https://github.com/marluceqa-source/hora-do-remedio/issues/15) |
| **RN26** | Espec. do portal | `api/routes/treatment_medications.py`, `database/models.py` | ✅ | `tests/unit/test_treatment_service.py` | [#15](https://github.com/marluceqa-source/hora-do-remedio/issues/15) |
| **RN27** | Espec. do portal | `services/treatment_service.py` | ✅ | `tests/unit/test_treatment_service.py` | [#15](https://github.com/marluceqa-source/hora-do-remedio/issues/15) |
| **RN28** | Espec. do portal | `services/treatment_service.py` | ✅ | `tests/unit/test_treatment_service.py` | [#15](https://github.com/marluceqa-source/hora-do-remedio/issues/15) |
| **RN29** | Espec. do portal §16 | `services/dashboard_service.py` | ✅ | `tests/unit/test_dashboard_service.py` | [#16](https://github.com/marluceqa-source/hora-do-remedio/issues/16) |
| **RN30** | Espec. do portal §16 | `bot/handlers/patients.py` (por ausência de escrita) | ✅ | — | [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) |
| **RN31** | Espec. do portal §16 | `services/patient_service.py` | ✅ | `tests/unit/test_patient_service.py` | [#14](https://github.com/marluceqa-source/hora-do-remedio/issues/14) |
| **RN32** | Espec. do portal | `api/routes/admin.py`, `services/audit_service.py` | ✅ | `tests/api/test_dashboard_and_admin.py` | [#17](https://github.com/marluceqa-source/hora-do-remedio/issues/17) |

**Resumo:** 31 das 32 RN têm implementação identificada e marcação `RNxx` no código. RN17 é a
única sem implementação ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)).
RN13 e RN30 são garantidas por **ausência de funcionalidade**, então não têm teste dedicado —
não há o que executar para provar que um código inexistente não roda.

---

## 4. Análise de cobertura — cenários de teste

Os 42 cenários CT do prompt master (§11) rastreados até o arquivo de teste. A convenção
`test_ctNN_...` é o que torna essa rastreabilidade verificável por `grep`.

| Arquivo | Cenários cobertos |
|---|---|
| `tests/api/test_medications.py` | CT01, CT02, CT03, CT04, CT09, CT10, CT12 |
| `tests/api/test_reminders.py` | CT05, CT06, CT07, CT08 |
| `tests/api/test_history_reports.py` | CT16 |
| `tests/api/test_isolation.py` | CT41 |
| `tests/unit/test_scheduler_firing.py` | CT05, CT11, CT14, CT15, CT18, CT42 |
| `tests/unit/test_notification_service.py` | CT13, CT22, CT27 |
| `tests/unit/test_bot_photo_voice.py` | CT19, CT20, CT21, CT26 |
| `tests/unit/test_bot_reminders_handler.py` | CT23, CT25 |
| `tests/unit/test_bot_menu_structure.py` | CT24 |
| `tests/unit/test_accessibility_confirmation.py` | CT29 |
| `tests/integration/test_cadastro_flow.py` | CT30 |
| `tests/integration/test_seed_and_persistence.py` | CT39, CT40 |
| `tests/contract/test_openapi_contract.py` | CT31, CT32, CT33, CT34, CT35, CT36, CT37, CT38 |

### Os buracos, fechados

| Cenário | Situação |
|---|---|
| **CT17** — "Botões antigos ou expirados" ([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35)) | ✅ **Coberto.** `tests/unit/test_ct17_expired_reminders.py` — 16 testes sobre a transição para `expired`, a recusa de resposta em botão antigo e a garantia de que expirado nunca vira `not_taken`. |

> ✅ **CT28** — "Acesso autorizado de cuidador" ([#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36))
> era o segundo buraco e foi fechado: `test_ct28_caregiver_can_view_authorized_patient_medications`
> em `tests/api/test_caregivers.py` leva o identificador e cobre o caminho ponta a ponta, do
> convite à leitura dos medicamentos.

> **Cobertura rastreável: 42 de 42 cenários (100%).** A suíte tem 201 testes e 86% de cobertura
> de linhas — número que vem da execução registrada no card
> [#21](https://github.com/marluceqa-source/hora-do-remedio/issues/21), não desta página.
>
> **Não falta nenhum.** CT17 era o último, e foi implementado e testado em
> [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35).

---

## 5. Matriz requisito funcional × regra × história × caso de uso

### Bot e API

| RF (prompt master) | RN relacionadas | História | Caso de uso |
|---|---|---|---|
| RF01 — Inicialização e menu | — | [HU01](Historias-de-Usuario#hu01--cadastrar-um-remédio-sem-precisar-ler) | UC01 |
| RF02 — Cadastro de medicamentos | RN01, RN02, RN13 | HU01 | UC01 |
| RF03 — Cadastro por fotografia | RN10 | HU02 | UC02 |
| RF04 — Cadastro por voz | RN11 | HU03 | UC03 |
| RF05 — Agendamento | RN03, RN07, RN08, RN15 | HU04 | UC05 |
| RF06 — Envio de lembretes | RN18 | HU04 | UC05 |
| RF07 — Confirmação | RN04, RN05, RN12 | HU05 | UC06 |
| RF08 — Adiamento | RN06 | HU06 | UC07 |
| RF09 — Histórico | RN09 | HU07 | UC09 |
| RF10 — Relatórios | RN12 | HU08 | UC10 |
| RF11 — Modo acessível | — | HU01, HU02, HU03 | UC01–UC03 |
| RF12 — Cuidadores | RN14 | HU09, HU10 | UC11, UC12 |
| RF13 — Endpoints REST | RN09 | — | — |
| RF14 — Swagger e OpenAPI YAML | — | — | — |

### Portal de profissionais

| RF (portal) | RN relacionadas | História | Caso de uso |
|---|---|---|---|
| RF01 — Autenticação com MFA | RN19, RN30 | — | UC13, UC21 |
| RF02 — Painel operacional | RN12, RN22 | HU15 | UC20 |
| RF03 — Cadastro de paciente | RN21, RN22 | HU11 | UC14 |
| RF04 — Convite de vínculo | RN23, RN24 | HU11 | UC15 |
| RF05 — Tratamento como rascunho | RN25 | HU12 | UC16 |
| RF06 — Ativação | RN20, RN26 | HU12 | UC17 |
| RF07 — Versionamento e suspensão | RN27, RN28 | HU13, HU14 | UC18, UC19 |
| RF08 — Histórico do paciente | RN12 | HU15 | UC20 |

### Requisitos não funcionais

A verificação de cada RNF está na própria página
[Requisitos Não Funcionais](Requisitos-Nao-Funcionais), coluna "Verificação". Os que **não têm**
verificação automatizada hoje: RNF05, RNF15, RNF17 ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)) e RES06 ([#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42)).

---

## 6. Análise de impacto

Exemplo de uso real da matriz: **o que seria afetado se RN12 mudasse** (se o produto passasse a
tratar silêncio como "não tomou").

| Artefato afetado | Impacto |
|---|---|
| `services/report_service.py`, `services/dashboard_service.py` | Reclassificação de `pending`, `delivered`, `snoozed`, `expired` |
| `api/schemas/report.py`, `api/schemas/dashboard.py` | Semântica dos campos de adesão muda |
| `tests/unit/test_report_service.py` | Quebra por projeto |
| Máquina de estado de `ReminderEvent` | Nova transição automática para `not_taken` |
| HU08, RF10, RF08 do portal | Critérios de aceitação reescritos |
| [Acessibilidade](Acessibilidade), [Limitações Conhecidas](Limitacoes-Conhecidas) | Páginas que afirmam o contrário |
| Conflito [CF02](Stakeholders-e-Fontes-de-Requisitos#4-conflitos-entre-requisitos) | Reaberto — a decisão de compromisso seria revertida |

Essa é exatamente a análise que o handbook aponta como benefício central de tipos de relação
explícitos (§6.3, p. 115). **RN12 não deve mudar** sem passar por isso — ela é a regra mais
sensível do sistema do ponto de vista clínico.

---

## 7. Lacunas desta rastreabilidade

| Lacuna | Efeito |
|---|---|
| **RN17 sem marcação no código** ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)) | Única regra implementável ainda sem marcação — e por um motivo real: não há expurgo implementado para marcar. RN01, RN08 e RN14 foram marcadas em [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37). |
| **Sem atributo de versão por requisito** ([#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38)) | A dimensão "entre versões de requisitos" (§6.2) é coberta só pelo histórico do Git. |
| **RNF sem marcação no código** | Os RNF foram criados nesta documentação e ainda não têm referência nos arquivos. |
| **Rastreabilidade mantida à mão** ([#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44)) | Nenhuma ferramenta de ER é usada (§11 do handbook de gerenciamento, p. 219): a matriz pode envelhecer sem aviso. |

---

## Próximo

- [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos)
- [Validação e Verificação](Validacao-e-Verificacao)
- [Priorização e Backlog](Priorizacao-e-Backlog)
