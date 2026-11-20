# Requisitos Não Funcionais

Requisitos de **qualidade** e **restrições** do Hora do Remédio. Esta página foi escrita porque
eles existiam espalhados pelo prompt master (seções 8, 11, 12 e 13) e pelo `core/config.py`,
**sem identificador** — e sem ID não há como priorizar, rastrear nem verificar.

---

## Como esta página classifica

O Handbook de Gerenciamento de Requisitos usa a classificação do CPRE Foundation Level
(§2.1.1, p. 25):

| Tipo | Definição citada no handbook | Prefixo aqui |
|---|---|---|
| Requisito de qualidade | "Um requisito que diz respeito a uma preocupação de qualidade que não é coberta por requisitos funcionais." (Definição 2-4, p. 25) | `RNF` |
| Restrição | "Especificações organizacionais, legais ou técnicas (geralmente limitações) para a realização do sistema planejado." (§2.1.1, p. 25) | `RES` |

O glossário reforça a diferença: restrição é "um requisito que limita o espaço de solução além
do que é necessário para atender aos requisitos funcionais e de qualidade dados" (verbete
*Restrição (na ER)*, p. 28). Já "requisito não funcional" é, no glossário, simplesmente "um
requisito de qualidade **ou** uma restrição" (p. 27) — ou seja, o guarda-chuva dos dois.

**Coluna "Verificação"**: onde a afirmação pode ser conferida. **Coluna "Estado"**: `garantido`
(há código e/ou teste), `parcial`, `declarado` (está na especificação, sem garantia no código).

---

## Acessibilidade e idioma

| ID | Requisito | Origem | Verificação | Estado |
|---|---|---|---|---|
| **RNF01** | A interface do bot deve permitir executar as funções principais **sem digitar e sem ler**, com navegação por botões e explicação em áudio. | Prompt master, RF11 | `tests/unit/test_bot_menu_structure.py` (CT24); `tests/integration/test_cadastro_flow.py` (CT30), que nomeia os campos que ainda exigem digitação | parcial |
| **RNF02** | Toda mensagem ao usuário final deve estar em **português brasileiro**, sem texto cru de framework (Pydantic, Axios, navegador). | Prompt master §1; decisão do portal | [Acessibilidade](Acessibilidade); card [#20](https://github.com/marluceqa-source/hora-do-remedio/issues/20), concluído | garantido |
| **RNF03** | Ações sensíveis devem oferecer **confirmação sonora**, ativável nas configurações. | Prompt master, RF11 regra 5 | `tests/unit/test_accessibility_confirmation.py` (CT29) | garantido |
| **RNF04** | A identificação do medicamento deve poder se apoiar na **fotografia real cadastrada**, não só em texto. | Prompt master, RF11 regra 7 | `Medication.photo_path`; lembrete envia a foto | garantido |
| **RNF05** | O sistema **não deve depender exclusivamente de cor** para transmitir informação. | Prompt master, RF11 regra 8 | [Acessibilidade](Acessibilidade) — ícone + texto em todos os estados | declarado |

> **RNF01 é parcial por decisão explícita.** Nome, dosagem, quantidade e datas ainda podem
> exigir digitação quando voz e foto não resolvem. A tensão está documentada como
> [CF01](Stakeholders-e-Fontes-de-Requisitos#4-conflitos-entre-requisitos).

---

## Tempo, agendamento e confiabilidade

| ID | Requisito | Origem | Verificação | Estado |
|---|---|---|---|---|
| **RNF06** | Todo cálculo de horário deve usar o **fuso do agendamento**, nunca o do servidor. Fuso padrão: `America/Sao_Paulo`. | Prompt master §1 e RF05; RN07 | `services/scheduler_service.py`; `tests/unit/test_scheduler_firing.py` (CT14) | garantido |
| **RNF07** | Os agendamentos devem **sobreviver à reinicialização** do processo. | Prompt master RF05; RN08 | `SchedulerService.reload_jobs()`; CT11, CT39 | garantido |
| **RNF08** | Falha de entrega no Telegram **não pode** derrubar a requisição nem gerar lembrete duplicado. | Prompt master §11 (CT13, CT18, CT42); RN18 | Índice único `(medication_id, scheduled_datetime)` em `ReminderEvent`; `tests/unit/test_notification_service.py` | garantido |
| **RNF09** | A notificação ao paciente na ativação de um tratamento deve ocorrer **após** a resposta HTTP ao profissional. | Decisão de arquitetura do portal | `api/routes/treatment_medications.py`; [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento) | garantido |

---

## Segurança e privacidade

| ID | Requisito | Origem | Verificação | Estado |
|---|---|---|---|---|
| **RNF10** | A autenticação da API deve ser **independente** do token do bot, e a do portal independente da do paciente. | Prompt master §8; RN19 | `core/security.py` vs `core/professional_security.py` | garantido |
| **RNF11** | Cada usuário deve acessar **apenas os próprios dados**; cuidador e profissional apenas o que foi autorizado e não revogado. | Prompt master §8; RN09, RN14, RN22 | `tests/api/test_isolation.py` (CT41); `tests/api/test_medications.py` (CT12) | garantido |
| **RNF12** | O portal deve exigir **MFA (TOTP)**, manter sessão revogável no servidor e bloquear após tentativas sucessivas de login. | Especificação do portal; RN30 | `services/professional_auth_service.py`; `tests/api/test_professional_auth.py` | garantido |
| **RNF13** | Segredos e tokens devem vir de **variáveis de ambiente**; nada sensível no repositório. | Prompt master §8 | `core/config.py` + `.env.example`; `.gitignore` | parcial |
| **RNF14** | OCR, STT e TTS devem rodar **localmente**, sem enviar imagem ou áudio do paciente a terceiros. | Prompt master §2 (justificar privacidade) | `services/ocr_service.py`, `services/speech_to_text_service.py`, `services/text_to_speech_service.py` | garantido |
| **RNF15** | Os logs **não devem** registrar conteúdo médico sensível desnecessário. | Prompt master §12 | `core/logging_config.py` (declarado no próprio módulo) | declarado |
| **RNF16** | A API deve limitar requisições por origem. Padrão: **60 por minuto**. | Prompt master §8 | `api/main.py` (`slowapi`, `rate_limit_per_minute`) | garantido |
| **RNF17** | Os registros devem seguir uma **política de retenção configurável**. Padrão: **365 dias**. | Prompt master §8; RN17 | `data_retention_days` em `core/config.py` | **parcial — sem expurgo** |
| **RNF18** | Toda operação sensível do portal deve ser **auditável** (ator, papel, ação, momento). | Especificação do portal; RN32 | `services/audit_service.py`, tabela `AuditLog` | garantido |

> **RNF13 é parcial** porque `PROFESSIONAL_SESSION_SECRET_KEY` tem valor padrão
> (`change-me-professional-session`) e **precisa ser trocado** antes de qualquer uso real (card [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30)).
> **RNF17 é parcial** porque o parâmetro existe mas nenhum job apaga registros antigos (card [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)).
> Os dois estão em [Limitações Conhecidas](Limitacoes-Conhecidas).

---

## Operação e manutenção

| ID | Requisito | Origem | Verificação | Estado |
|---|---|---|---|---|
| **RNF19** | A API deve expor um **health check** verificável. | Prompt master §12 | `GET /health` em `api/main.py`; `tests/api/test_health.py` | garantido |
| **RNF20** | A documentação da API deve ter **fonte única de verdade** — YAML, JSON e rotas não podem divergir. | Prompt master RF14 | `scripts/export_openapi.py`; `tests/contract/test_openapi_contract.py` | garantido |
| **RNF21** | Nenhuma regra de negócio pode estar **duplicada** entre bot, API e portal. | Prompt master §9; decisão de arquitetura | Camada `services/` compartilhada; [`docs/architecture.md`](../blob/main/docs/architecture.md) | garantido |
| **RNF22** | A suíte de testes deve ser executável com **integrações externas mockadas** e **relógio controlado**. | Prompt master §11 | `tests/unit/test_scheduler_firing.py`; `tests/unit/test_notification_service.py` | garantido |
| **RNF23** | Os serviços devem reiniciar sozinhos e encerrar de forma graciosa; o agendador roda em **instância única**. | Prompt master §13 | `docker-compose.yml` (`restart: unless-stopped`, `replicas: 1` no serviço `bot`) | parcial |

> **RNF23 é parcial**: o Compose documenta e fixa uma réplica, mas **não há coordenação
> (lock distribuído)** que impeça duplicação se alguém subir uma segunda instância do bot (card [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33)).

---

## Restrições

| ID | Restrição | Origem |
|---|---|---|
| **RES01** | Stack obrigatória: Python 3.12+, FastAPI, python-telegram-bot, SQLAlchemy + Alembic, APScheduler, Pydantic, pytest. | Prompt master §2 |
| **RES02** | A interface do bot está limitada aos **recursos reais da Telegram Bot API** — sem controle sobre tamanho, cor ou layout dos botões nativos. | Prompt master, RF11 ("Limitação técnica") |
| **RES03** | OCR, STT e TTS devem ter suporte a **português brasileiro** e opção de execução local. | Prompt master §2 |
| **RES04** | Persistência padrão em **SQLite**; PostgreSQL deve ser avaliado para produção. | Prompt master §13 |
| **RES05** | Empacotamento e execução por **Docker / Docker Compose**, sem permitir múltiplos agendadores concorrentes. | Prompt master §13 |
| **RES06** | O tratamento de dados deve ser **compatível com a LGPD**, incluindo exportação e exclusão de dados. | Prompt master §8 |
| **RES07** | O sistema **não prescreve** e não recomenda alteração de dose (RN13); reconhecimento automático nunca autoriza mudança de prescrição. | Prompt master §7 e §8 |

> **RES06 está apenas declarada.** Não existe hoje rota de exportação nem de exclusão de dados
> do titular — card [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42).

---

## Ponto de atenção: mensurabilidade

O glossário define **critério de qualidade (na ER)** como "um conjunto de qualidades esperadas
de bons requisitos ou bons produtos de trabalho de ER" (p. 8), mas os documentos de referência
usados aqui **não fornecem um gabarito de requisito de qualidade** com valor-alvo e forma de
medição.

Vários RNF desta página são **verificáveis** (existe teste), porém **não quantificados**: RNF01
não define "quantos passos sem digitar", RNF15 não define o que conta como "conteúdo sensível",
RNF19 não define tempo de resposta aceitável do `/health`.

> **Complemento baseado em conhecimento externo aos arquivos fornecidos:** a prática usual é
> escrever requisitos de qualidade com grandeza, valor-alvo e método de medição (por exemplo,
> "p95 do tempo de resposta de `/health` abaixo de 300 ms sob 60 req/min"), para que possam ser
> verificados objetivamente. Essa recomendação **não** vem dos documentos do IREB listados
> nesta wiki.

Fechar isso é um item de backlog (card [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43)), não uma afirmação de conformidade.

---

## Próximo

- [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade)
- [Validação e Verificação](Validacao-e-Verificacao)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
