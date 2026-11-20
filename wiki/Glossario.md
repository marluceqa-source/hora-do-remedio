# Glossário

> **Glossário:** "Uma coleção de definições de termos que são relevantes em algum domínio.
> Nota: frequentemente, um glossário também contém referências cruzadas, sinônimos, homônimos,
> acrônimos e abreviações." — Glossário IREB, verbete *Glossário*, p. 15

Esta página segue essa recomendação: define os termos do domínio, **nomeia os homônimos** que já
causaram confusão neste projeto e lista os termos de Engenharia de Requisitos usados na wiki com
a fonte de cada definição.

---

## 1. Homônimos — leia esta seção primeiro

São os termos que significam **coisas diferentes** em partes diferentes do sistema. Ignorá-los é
a causa mais provável de erro na leitura do código e da documentação.

| Termo | Significado A | Significado B |
|---|---|---|
| **Paciente** | `User` — a conta do Telegram que recebe lembretes (universo do bot). | `Patient` — o cadastro feito pelo profissional no portal, que pode existir **antes** de haver conta no Telegram. |
| **Medicamento** | `Medication` — entidade **operacional**, consumida pelo agendador. | `TreatmentMedication` — entidade **clínica**, versionada, criada pelo profissional. |
| **Horário / agendamento** | `Schedule` — operacional, o que o agendador lê. | `TreatmentMedicationSchedule` — clínico, a intenção do profissional. |
| **RF02** | Bot/API: cadastro de medicamentos. | Portal: painel operacional. **As duas numerações `RFxx` são espaços independentes.** |
| **Status** | `ReminderEvent.status` — estado de uma dose. | `TreatmentMedication.status` — estado de uma prescrição. |
| **Vínculo** | `telegram_link_status` — ligação do paciente ao Telegram. | `PatientProfessionalLink` — autorização entre paciente e profissional. |
| **Verificação** | Em ER: conferir se o requisito está bem especificado ([V&V](Validacao-e-Verificacao)). | No portal: `verification_status` — se um administrador confirmou que a pessoa é profissional de saúde. |

A relação entre `TreatmentMedication` e `Medication` está em
[Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento).

---

## 2. Termos do domínio

| Termo | Definição neste projeto | Onde aparece |
|---|---|---|
| **Adesão declarada** | Medida que considera **apenas** o que o paciente confirmou explicitamente. Não é adesão clínica real: silêncio não é "não tomou" (RN12). | `services/report_service.py`, `api/schemas/report.py` |
| **Dose** | Uma administração prevista de um medicamento em um horário específico. Materializa-se como um `ReminderEvent`. | `database/models.py` |
| **Lembrete** | A mensagem enviada ao paciente no horário da dose, com foto, nome, dosagem, áudio e botões. | `services/notification_service.py` |
| **Evento de lembrete** | O registro da dose e do seu desfecho: `pending`, `delivered`, `confirmed`, `not_taken`, `snoozed`, `expired`. | `ReminderEvent` |
| **Adiamento** | Reenvio do lembrete em 5, 10, 15 ou 30 minutos, **sem alterar** o horário programado (RN06). | `services/reminder_service.py` |
| **Recorrência** | Como a dose se repete: `daily`, `weekly` (dias da semana) ou `interval` (intervalo em horas). | `Schedule.recurrence_type` |
| **Tratamento / plano de tratamento** | Prescrição feita por um profissional, com ciclo de vida próprio e versionamento. | `TreatmentPlan`, `TreatmentMedication` |
| **Materialização** | Ato de, ao ativar um tratamento, criar as entidades operacionais (`Medication`, `Schedule`) que o agendador já consumia (RN26). | `services/treatment_service.py` |
| **Versão de tratamento** | Nova linha de `TreatmentMedication` encadeada por `previous_version_id`, criada ao editar um tratamento ativo (RN27). | `services/treatment_service.py` |
| **Convite de vínculo** | Token de uso único e temporário que liga o paciente do portal a uma conta do Telegram; entregue como deep link e QR Code (RN23, RN24). | `PatientInvitation` |
| **Cuidador autorizado** | Pessoa autorizada pelo **próprio paciente**, por código, com acesso somente leitura e revogável (RN14). | `CaregiverAccess` |
| **Profissional verificado** | Profissional cujo cadastro foi confirmado por um administrador (`verification_status = verified`). Cadastro **não** concede acesso clínico. | `Professional` |
| **Papel (`role`)** | O que de fato concede permissão no portal: `medico`, `enfermeiro`, `outro_profissional`, `admin`. O campo `profession` é texto livre e **não** concede nada. | [Papéis e Permissões](Papeis-e-Permissoes) |
| **Modo acessível** | Preferência do paciente que liga a confirmação sonora após ações. | `User.accessibility_mode` |
| **OCR** | Reconhecimento de texto em imagem, executado **localmente** (Tesseract). Resultado é sugestão, nunca substitui o que a pessoa informou (RN10). | `services/ocr_service.py` |
| **STT** | Transcrição de voz em texto, **local** (faster-whisper). Exige confirmação explícita (RN11). | `services/speech_to_text_service.py` |
| **TTS** | Geração de áudio a partir de texto, **local** (pyttsx3). | `services/text_to_speech_service.py` |
| **Trilha de auditoria** | Registro de ator, papel, ação e momento das operações sensíveis do portal. Não contém dado clínico (RN32). | `AuditLog`, `services/audit_service.py` |
| **Fuso do agendamento** | O fuso gravado no `Schedule`, usado em todo cálculo de horário — nunca o fuso do servidor (RN07). | `Schedule.timezone` |
| **Horário de parede** | Convenção de `scheduled_datetime`: é o horário local no fuso do agendamento, **não** um instante UTC. | `database/models.py` |

---

## 3. Termos de Engenharia de Requisitos

Todas as definições abaixo são do *Glossary of Requirements Engineering Terminology* (IREB CPRE
2.2), traduzidas direto do verbete. A página indicada é a do próprio documento.

| Termo | Definição | Página |
|---|---|---|
| **Engenharia de Requisitos** | Abordagem sistemática e disciplinada para a especificação e o gerenciamento de requisitos, com o objetivo de entender os desejos e necessidades dos stakeholders e minimizar o risco de entregar um sistema que não os atenda. | 11 |
| **Requisito** | 1. Uma necessidade percebida por um stakeholder. 2. Uma capacidade ou propriedade que um sistema deve ter. 3. Uma representação documentada de uma necessidade, capacidade ou propriedade. | 26 |
| **Requisito funcional** | Requisito relativo a um resultado ou comportamento que deve ser fornecido por uma função do sistema. | 27 |
| **Requisito de qualidade** | Requisito que diz respeito a uma preocupação de qualidade não coberta por requisitos funcionais. | 27 |
| **Requisito não funcional** | Um requisito de qualidade **ou** uma restrição. | 27 |
| **Restrição (na ER)** | Requisito que limita o espaço de solução além do necessário para atender aos requisitos funcionais e de qualidade. | 28 |
| **Stakeholder** | Pessoa ou organização que influencia os requisitos de um sistema ou que é impactada por ele. A influência pode ser indireta. | 31 |
| **Fonte de requisitos** | A fonte da qual um requisito foi derivado — tipicamente stakeholders, documentos, sistemas existentes e observações. | 14 |
| **Elicitação de requisitos** | Processo de buscar, capturar e consolidar requisitos a partir das fontes disponíveis, podendo incluir a reconstrução ou criação de requisitos. | 11 |
| **Especificação de requisitos** | Coleção representada sistematicamente de requisitos, tipicamente para um sistema, que satisfaz critérios dados. | 13 |
| **Especificação de requisitos do cliente** | Descrição grosseira das capacidades requeridas de um sistema a partir da perspectiva do cliente. | 14 |
| **Documento de requisitos** | Documento que consiste em uma especificação de requisitos. | 10 |
| **Gerenciamento de requisitos** | Processo de gerenciar os requisitos existentes e os produtos de trabalho relacionados, incluindo armazenamento, alteração e rastreamento. | 15 |
| **Gerenciamento de mudanças** | Maneira controlada de efetuar ou negar uma mudança solicitada em um produto de trabalho. | 14 |
| **Rastreabilidade** | Capacidade de rastrear um requisito até suas origens, até sua implementação e testes, e até os requisitos dos quais depende. | 26 |
| **Baseline (linha de base)** | Configuração estável, com mudança controlada, de produtos de trabalho. | 3 |
| **Versão** | Estado de conteúdo específico de um artefato, entre várias ocorrências ordenadas no tempo. | 34 |
| **Validação** | Processo de confirmar que um item corresponde às necessidades dos stakeholders — "os requisitos certos". | 33 |
| **Verificação** | Processo de confirmar que um item cumpre sua especificação — "os requisitos especificados corretamente". | 34 |
| **Revisão** | Avaliação de um produto de trabalho por um indivíduo ou grupo, para encontrar problemas ou sugerir melhorias. | 28 |
| **Critério de qualidade (na ER)** | Conjunto de qualidades esperadas de bons requisitos ou bons produtos de trabalho de ER. | 8 |
| **Critério de aceitação** | Critérios que um produto de trabalho deve satisfazer para ser aceito pelos stakeholders. | 8 |
| **História de Usuário** | Narrativa curta descrevendo uma necessidade da perspectiva do usuário, com o benefício esperado. | 16 |
| **Backlog do produto** | Coleção ordenada, tipicamente priorizada, de itens de trabalho. | 2 |
| **Priorização** | Processo de atribuir prioridades a um conjunto de itens. | 24 |
| **Caso de uso** | Conjunto de interações possíveis entre atores externos e um sistema que fornecem benefício aos atores envolvidos. | 4 |
| **Cenário** | Sequência ordenada de interações entre parceiros, em particular entre sistemas ou pessoas. | 4 |
| **Especificação por exemplo** | Técnica que especifica casos de teste e requisitos fornecendo exemplos de como o sistema deve se comportar. | 14 |
| **Atributo** | Propriedade característica de uma entidade ou objeto. | 2 |
| **Risco** | Evento possível que ameaça o sucesso de um empreendimento. | 28 |

### Termos que esta wiki usa e o glossário do IREB **não** define

| Termo | Situação |
|---|---|
| **Regra de negócio (`RNxx`)** | Não há verbete correspondente no glossário IREB 2.2 consultado. Neste projeto, as RN funcionam como um conjunto nomeado de restrições de domínio e de comportamento — convenção herdada do prompt master (§7). Ver [Engenharia de Requisitos §4](Engenharia-de-Requisitos#4-classificação-dos-requisitos-adotada). |
| **Gherkin / BDD** | Notação não definida nos documentos de referência. O conceito próximo que existe é *especificação por exemplo* (p. 14). |
| **MoSCoW** | **Não aparece** no Handbook de Gerenciamento de Requisitos consultado. As técnicas de priorização que ele apresenta estão em [Priorização e Backlog §2](Priorizacao-e-Backlog#2-qual-técnica-foi-escolhida-e-por-quê) — e MoSCoW não é uma delas. |
| **Definition of Done** | Não definida nos documentos consultados. O papel equivalente aqui é desempenhado pelos critérios de aceite do prompt master (§15). |

---

## Próximo

- [Engenharia de Requisitos](Engenharia-de-Requisitos)
- [Modelagem de Requisitos](Modelagem-de-Requisitos)
- [Papéis e Permissões](Papeis-e-Permissoes)
