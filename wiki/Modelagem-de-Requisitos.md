# Modelagem de Requisitos

O mesmo sistema visto por modelos, em vez de por tabelas de requisitos. Cada modelo responde a
uma pergunta diferente — e nenhum substitui os requisitos textuais.

---

## 1. As visões usadas e por quê

O Syllabus de Modelagem organiza a modelagem de requisitos em visões (§1.2, p. 11) e dedica um
capítulo a cada uma: contexto (cap. 2, p. 13), estrutura de informações (cap. 3, p. 16), visões
dinâmicas — casos de uso, fluxo e estados (cap. 4, p. 18) — e cenários (cap. 5, p. 23).

| Visão | Diagrama aqui | Pergunta que responde |
|---|---|---|
| **Contexto** | [Diagrama de contexto](#2-visão-de-contexto) | O que está dentro do sistema e o que é externo a ele? |
| **Estrutura de informações** | [Modelo de classes](#3-visão-de-estrutura-de-informações) | Quais entidades existem e como se relacionam? |
| **Casos de uso** | [Casos de uso](#4-visão-de-casos-de-uso) | Que benefício cada ator obtém do sistema? |
| **Estados** | [Máquinas de estado](#5-visão-de-estados) | Que estados um objeto assume e o que provoca a transição? |
| **Cenários** | [Diagramas de sequência](#6-visão-de-cenários) | Em que ordem os participantes interagem? |

O syllabus também trata explicitamente a **integração entre modelos e requisitos textuais**
(§1.3, p. 11): os modelos abaixo não repetem as regras, eles **apontam** para elas (RN, RF).

---

## 2. Visão de contexto

Os termos do capítulo 2 são **limite de sistema**, **limite do contexto** e **diagrama de
contexto** (p. 13). O que interessa aqui é a fronteira: o Hora do Remédio não controla o
Telegram, não controla o aparelho do paciente e não controla o navegador do profissional.

```mermaid
flowchart LR
    P["Paciente"]
    C["Cuidador autorizado"]
    PR["Profissional de saude"]
    AD["Administrador"]
    TG["Telegram Bot API<br/>sistema externo"]
    NAV["Navegador<br/>portal web"]

    subgraph SIS["Hora do Remedio - limite do sistema"]
        BOT["Processo bot<br/>+ agendador"]
        API["API REST<br/>FastAPI"]
        SRV["Camada services<br/>regras de negocio"]
        DB[("Banco de dados")]
        LOC["OCR, STT e TTS locais"]
    end

    P -->|"mensagens, botoes, foto, audio"| TG
    C -->|"codigo de vinculo"| TG
    TG <-->|"lembretes e respostas"| BOT
    PR --> NAV
    AD --> NAV
    NAV <-->|"HTTPS, cookie de sessao"| API
    BOT --> SRV
    API --> SRV
    SRV --> DB
    BOT --> LOC
```

### O que a fronteira implica

| Fato do contexto | Requisito que nasce dele |
|---|---|
| A interface do paciente é renderizada **pelo Telegram**, não pelo sistema. | **RES02** — sem controle de tamanho, cor ou layout dos botões. |
| OCR, STT e TTS estão **dentro** do limite do sistema. | **RNF14** — imagem e áudio do paciente não saem do ambiente. |
| O Telegram pode estar indisponível no horário da dose. | **RNF08**, RN18 — falha registrada, sem duplicidade. |
| O agendador vive **dentro do processo do bot**. | **RNF23** — instância única; ver [`docs/architecture.md`](../blob/main/docs/architecture.md). |

---

## 3. Visão de estrutura de informações

O capítulo 3 do syllabus cobre classes, atributos e tipos de dados (§3.2), relacionamentos
simples, agregações e composições (§3.3) e generalização/especialização (§3.4) — p. 16–17.

O ponto central deste modelo é que existem **duas camadas**: a clínica (versionada, do portal) e
a operacional (executada pelo agendador). O elo é `linked_medication_id`, com restrição `UNIQUE`.

```mermaid
classDiagram
    class User {
        +int id
        +int telegram_user_id
        +str timezone
        +bool accessibility_mode
    }
    class Medication {
        +int id
        +str name
        +str dosage
        +str quantity
        +str photo_path
        +date start_date
        +date end_date
        +bool active
    }
    class Schedule {
        +str recurrence_type
        +time schedule_time
        +int interval_hours
        +str weekdays
        +str timezone
    }
    class ReminderEvent {
        +datetime scheduled_datetime
        +datetime delivery_datetime
        +datetime confirmed_datetime
        +str status
        +int snooze_count
    }
    class CaregiverAccess {
        +str permission
        +datetime authorized_at
        +datetime revoked_at
    }
    class Professional {
        +str full_name
        +str email
        +str role
        +str verification_status
        +bool mfa_enabled
    }
    class Patient {
        +str full_name
        +str internal_identifier
        +str telegram_link_status
    }
    class PatientProfessionalLink {
        +str relationship_type
        +str authorization_status
    }
    class TreatmentPlan {
        +str status
        +datetime activated_at
    }
    class TreatmentMedication {
        +str medication_name
        +str dosage
        +str quantity_per_administration
        +str status
        +int previous_version_id
    }
    class TreatmentMedicationSchedule {
        +str recurrence_type
        +time schedule_time
    }
    class PatientInvitation {
        +str token_hash
        +datetime expires_at
        +datetime consumed_at
    }
    class AuditLog {
        +str action
        +str actor_role
        +datetime created_at
    }

    User "1" *-- "0..*" Medication : RN01
    Medication "1" *-- "1..*" Schedule : RN02
    Medication "1" *-- "0..*" ReminderEvent
    User "1" -- "0..*" CaregiverAccess : RN14
    Professional "1" -- "0..*" PatientProfessionalLink
    Patient "1" -- "0..*" PatientProfessionalLink : RN21
    Patient "0..1" -- "0..1" User : vinculo Telegram
    Patient "1" -- "0..*" PatientInvitation : RN23
    Patient "1" *-- "0..*" TreatmentPlan
    TreatmentPlan "1" *-- "1..*" TreatmentMedication
    TreatmentMedication "1" *-- "1..*" TreatmentMedicationSchedule
    TreatmentMedication "0..1" --> "0..1" Medication : linked_medication_id UNIQUE - RN26
    TreatmentMedication --> TreatmentMedication : previous_version_id - RN27
```

### Leitura do modelo

- **Composição** (losango cheio) onde a vida do filho depende do pai: apagar o `Medication`
  apaga seus `Schedule` e `ReminderEvent` (`cascade="all, delete-orphan"`).
- `Patient` e `User` são **entidades distintas de propósito**: o paciente existe no portal antes
  de ter conta no Telegram (`telegram_link_status = not_linked`).
- O relacionamento reflexivo em `TreatmentMedication` é o que materializa o **versionamento**
  (RN27) — ele é a razão pela qual o histórico de doses sobrevive a uma mudança de dose.
- `AuditLog` não se relaciona a `Patient`: a auditoria registra **operação**, não dado clínico
  (RN32).

---

## 4. Visão de casos de uso

O syllabus pede casos de uso identificados e **especificados em forma textual** (§4.3, p. 20) e
estruturados em pacotes (§4.4, p. 20).

> **Caso de uso:** "Um conjunto de interações possíveis entre atores externos e um sistema que
> fornecem um benefício para o(s) ator(es) envolvido(s)."
> — Glossário, verbete *Caso de uso*, p. 4

| Pacote | ID | Caso de uso | Ator primário | História |
|---|---|---|---|---|
| Medicação | **UC01** | Cadastrar medicamento | Paciente | [HU01](Historias-de-Usuario#hu01--cadastrar-um-remédio-sem-precisar-ler) |
| Medicação | **UC02** | Cadastrar medicamento por fotografia | Paciente | [HU02](Historias-de-Usuario#hu02--cadastrar-fotografando-a-embalagem) |
| Medicação | **UC03** | Cadastrar medicamento por voz | Paciente | [HU03](Historias-de-Usuario#hu03--cadastrar-falando) |
| Medicação | **UC04** | Excluir medicamento | Paciente | RN16 |
| Lembretes | **UC05** | Receber lembrete da dose | Paciente | [HU04](Historias-de-Usuario#hu04--ser-lembrado-no-horário-certo) |
| Lembretes | **UC06** | Confirmar dose | Paciente | [HU05](Historias-de-Usuario#hu05--confirmar-que-tomei) |
| Lembretes | **UC07** | Adiar lembrete | Paciente | [HU06](Historias-de-Usuario#hu06--adiar-sem-desarrumar-a-rotina) |
| Lembretes | **UC08** | Registrar dose não tomada | Paciente | RN12 |
| Acompanhamento | **UC09** | Consultar histórico | Paciente, Cuidador | [HU07](Historias-de-Usuario#hu07--consultar-meu-histórico) |
| Acompanhamento | **UC10** | Gerar relatório de adesão declarada | Paciente, Cuidador | [HU08](Historias-de-Usuario#hu08--ter-um-relatório-que-não-me-acuse) |
| Cuidadores | **UC11** | Autorizar cuidador | Paciente | [HU09](Historias-de-Usuario#hu09--autorizar-e-revogar-um-cuidador) |
| Cuidadores | **UC12** | Revogar cuidador | Paciente | [HU09](Historias-de-Usuario#hu09--autorizar-e-revogar-um-cuidador) |
| Portal | **UC13** | Autenticar com MFA | Profissional | RN19, RN30 |
| Portal | **UC14** | Cadastrar paciente | Profissional | [HU11](Historias-de-Usuario#hu11--cadastrar-o-paciente-e-vinculá-lo-sem-digitação) |
| Portal | **UC15** | Vincular paciente ao Telegram | Profissional, Paciente | [HU11](Historias-de-Usuario#hu11--cadastrar-o-paciente-e-vinculá-lo-sem-digitação) |
| Portal | **UC16** | Prescrever tratamento como rascunho | Profissional | RN25 |
| Portal | **UC17** | Ativar tratamento | **Médico** | [HU12](Historias-de-Usuario#hu12--ativar-só-o-que-foi-validado) |
| Portal | **UC18** | Versionar tratamento ativo | Profissional | [HU13](Historias-de-Usuario#hu13--mudar-a-dose-sem-apagar-o-passado) |
| Portal | **UC19** | Suspender tratamento | Profissional | [HU14](Historias-de-Usuario#hu14--suspender-um-tratamento) |
| Portal | **UC20** | Acompanhar painel de adesão | Profissional | [HU15](Historias-de-Usuario#hu15--ver-o-painel-dos-meus-pacientes) |
| Governança | **UC21** | Verificar profissional | Administrador | [HU16](Historias-de-Usuario#hu16--verificar-quem-é-profissional-e-auditar) |
| Governança | **UC22** | Consultar trilha de auditoria | Administrador | RN32 |

**UC17 é o único caso de uso com restrição de papel no próprio nível do caso de uso** (RN20): o
ator não é "profissional", é **médico**.

---

## 5. Visão de estados

O syllabus trata modelagem orientada a estados em §4.9 e §4.10 (p. 22). Os dois objetos deste
sistema com ciclo de vida relevante são o **tratamento** e o **evento de lembrete**.

### 5.1 Tratamento (`TreatmentMedication.status`)

```mermaid
stateDiagram-v2
    [*] --> draft : prescrever - RN25
    draft --> pending_validation : enviar para validacao
    pending_validation --> draft : devolver
    draft --> active : ativar - so medico RN20 + paciente vinculado
    pending_validation --> active : ativar - RN20
    active --> suspended : suspender - RN28
    suspended --> active : reativar
    active --> closed : nova versao ativada - RN27
    draft --> closed : descartar
    closed --> [*]
```

Ao entrar em `active`, a ativação **materializa** `Medication` e `Schedule` (RN26). Ao sair para
`closed`, o `linked_medication_id` é liberado — a restrição `UNIQUE` não permitiria duas versões
apontando para a mesma linha de `Medication`. Detalhes em
[Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento).

### 5.2 Evento de lembrete (`ReminderEvent.status`)

```mermaid
stateDiagram-v2
    [*] --> pending : evento criado no horario agendado
    pending --> delivered : enviado ao Telegram
    pending --> pending : falha de envio registrada - RN18
    delivered --> confirmed : paciente toca Tomei - RN04
    delivered --> not_taken : paciente toca Nao tomei
    delivered --> snoozed : paciente adia - RN06
    snoozed --> confirmed : confirma depois
    snoozed --> not_taken : declara que nao tomou
    delivered --> expired : janela fecha sem resposta - CT17
    snoozed --> expired : janela fecha sem resposta - CT17
    expired --> expired : resposta recusada - CT17
    confirmed --> confirmed : nova confirmacao recusada - RN05
    confirmed --> [*]
    not_taken --> [*]
    expired --> [*]
```

> **A transição que não existe é a mais importante.** Não há caminho de `delivered` para
> `not_taken` **sem ação do paciente**. É a RN12 expressa como máquina de estado: a ausência de
> resposta deixa o evento em `delivered`, e os relatórios o contam como **sem confirmação**,
> nunca como "não tomou".

Os estados vêm da `CheckConstraint` em `ReminderEvent`:
`pending`, `delivered`, `confirmed`, `not_taken`, `snoozed`, `expired`.

> ✅ **`expired` deixou de ser inalcançável** no card [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35).
> Um job periódico (`expire-reminders`, a cada 15 min) move para `expired` todo lembrete que
> passou da janela de resposta sem ser respondido — `REMINDER_EXPIRE_HOURS`, padrão 24 h. Com
> isso o cenário **CT17** ("botões antigos ou expirados") passou a ter implementação e teste,
> e os 42 cenários do prompt master estão cobertos.
>
> **A transição respeita a regra mais importante do sistema.** `expired` significa *"a janela
> fechou sem resposta"*, e continua contado entre os **sem confirmação** em
> `report_service.py` e `dashboard_service.py` — nunca entre as doses não tomadas. Não existe,
> e não deve existir, caminho de `expired` para `not_taken`: a passagem do tempo não produz um
> fato clínico (RN12 / RN29).
>
> Um lembrete expirado **não aceita mais resposta**: tocar num botão antigo recebe um aviso e
> os botões somem, para que um toque acidental não vire registro.

---

## 6. Visão de cenários

O capítulo 5 do syllabus trata modelagem de cenários com diagramas de sequência (§5.2 e §5.3,
p. 24–25).

> **Cenário:** "Uma sequência ordenada de interações entre parceiros, em particular entre
> sistemas ou pessoas." — Glossário, verbete *Cenário*, p. 4

### 6.1 Da prescrição ao lembrete

```mermaid
sequenceDiagram
    actor M as Medico
    participant PT as Portal
    participant API as API REST
    participant TS as treatment_service
    participant DB as Banco
    participant SCH as Agendador
    participant TG as Telegram
    actor P as Paciente

    M->>PT: ativar tratamento
    PT->>API: POST ativacao
    API->>TS: ativar - verifica papel RN20 e vinculo
    TS->>DB: cria Medication e Schedule - RN26
    API-->>PT: 200 tratamento ativo
    API->>TG: notifica paciente - apos a resposta RNF09
    TG->>P: novo medicamento cadastrado
    SCH->>DB: reload_jobs - RN08
    Note over SCH: no horario, no fuso do Schedule - RN07
    SCH->>TG: lembrete com foto, nome e botoes
    TG->>P: esta na hora do seu remedio
    P->>TG: toca Tomei
    TG->>SCH: callback
    SCH->>DB: status confirmed - RN04 e RN05
```

### 6.2 Cadastro por fotografia

```mermaid
sequenceDiagram
    actor P as Paciente
    participant TG as Telegram
    participant BOT as Handler do bot
    participant OCR as ocr_service local
    participant DB as Banco

    P->>TG: envia foto da embalagem
    TG->>BOT: imagem recebida
    BOT->>OCR: extrair texto
    OCR-->>BOT: possivel nome reconhecido
    BOT->>TG: mostra o texto e pede confirmacao - RN10
    TG->>P: e este o nome?
    P->>TG: confirma
    BOT->>DB: salva nome confirmado e caminho da foto
    Note over BOT,DB: sem confirmacao, o nome digitado nao e sobrescrito
```

---

## 7. O que esta modelagem não cobre

| Lacuna | Consequência |
|---|---|
| **Sem decomposição funcional por DFD de nível 1+** | O syllabus prevê modelagem de fluxo de dados e de atividades (§4.5–§4.8, p. 20–21). Aqui só há o diagrama de contexto; o detalhamento interno está descrito em texto em [`docs/architecture.md`](../blob/main/docs/architecture.md). |
| **Sem diagramas de atividade** | Os fluxos conversacionais do bot (cadastro passo a passo) estão apenas nos handlers e nos testes. |
| **Sem diagramas de comunicação** | Previstos em §5.4 (p. 25); os cenários aqui usam só sequência. |
| **Casos de uso sem especificação textual completa** | A tabela nomeia os casos de uso; o detalhamento de pré-condições, fluxo principal e exceções está distribuído entre as [histórias](Historias-de-Usuario) e as regras de negócio, não em um gabarito de caso de uso. |

Esses itens são deliberadamente lacunas **declaradas**, não dívidas escondidas.

---

## Próximo

- [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade)
- [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento)
- [Histórias de Usuário](Historias-de-Usuario)
