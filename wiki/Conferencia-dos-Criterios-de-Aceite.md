# Conferência dos Critérios de Aceite (§15)

Os **19 critérios de aceite** da seção 15 do prompt master são a definição de "pronto" do
escopo original — bot, API e documentação. Esta página é o registro da conferência **item a
item**, com a evidência de cada verdito.

> Card: [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39)
> **Data da conferência:** 26 de novembro de 2026
> **Commit conferido:** `3d34dcc` · **Baseline:** [1.0.0](Home#baseline-da-especificação)

---

## 1. Resultado

| | Critérios |
|---|---|
| ✅ **Atendidos** | **17** |
| ⚠️ **Atendido com ressalva** | **1** — nº 19 (configurações sensíveis) |
| ❌ **Não verificado** | **1** — nº 18 (Docker) |

**Nenhum critério foi reprovado por comportamento errado do sistema.** As duas exceções são de
natureza diferente entre si e nenhuma delas é um defeito de funcionalidade:

- o **nº 18** não pôde ser verificado porque **não há Docker instalado na máquina** onde a
  conferência foi feita — é uma verificação pendente, não uma falha conhecida;
- o **nº 19** está atendido no que diz respeito ao versionamento, mas a conferência
  **descobriu um vazamento novo**: o token do bot é gravado em texto claro no arquivo de log
  (ver [achado A](#5-achados-da-conferência)).

---

## 2. Como cada verdito foi obtido

A conferência não aceita "o teste existe" como evidência suficiente para um critério que fala
de comportamento em execução. Cada linha diz **de onde** vem a prova, em uma destas três
formas:

| Tipo de evidência | O que significa |
|---|---|
| **Execução ao vivo** | Um comando rodado nesta conferência, com a saída observada. |
| **Log de execução real** | O sistema foi usado de verdade contra o Telegram entre 17 e 21 de novembro de 2026; `logs/hora_do_remedio.log*` registra as chamadas efetivamente feitas à API do Telegram. |
| **Teste automatizado** | Cenário CT coberto pela suíte, com as integrações externas mockadas. |

Onde um critério fala de comportamento com o Telegram, a evidência preferida é o **log de
execução real** — o teste mockado prova a lógica, não a integração.

### O que o log de execução mostra

Contagem de chamadas à API do Telegram efetivamente registradas (os dois arquivos de log
somados):

| Método | Chamadas | O que prova |
|---|---|---|
| `getMe` | 40 | O bot autenticou e iniciou. |
| `getUpdates` | 26.274 | O *long polling* rodou de forma contínua. |
| `sendMessage` | 86 | Mensagens entregues ao paciente. |
| `sendAudio` | 39 | Mensagens de áudio entregues. |
| `sendPhoto` | 4 | Ilustrações entregues. |
| `answerCallbackQuery` | 17 | **Botões inline foram realmente pressionados por uma pessoa.** |
| `getFile` | 2 | Foto/áudio enviados pelo usuário foram baixados. |

---

## 3. A conferência item a item

| # | Critério (§15) | Verdito | Evidência |
|---|---|---|---|
| 1 | A aplicação utilizar o nome **Hora do Remédio**. | ✅ | `APP_NAME` em `core/config.py`; `GET /health` responde `{"service":"Hora do Remédio"}` (execução ao vivo); título do `README.md` e do `openapi.yaml` (`Hora do Remédio API`). |
| 2 | O bot Telegram iniciar corretamente. | ✅ | Log de execução real: **40 chamadas `getMe` bem-sucedidas** e 26.274 `getUpdates`. O bot não só inicia — ficou em polling contínuo. |
| 3 | O usuário conseguir cadastrar medicamentos. | ✅ | CT01–CT04, CT10 (`tests/api/test_medications.py`); `tests/integration/test_cadastro_flow.py` (CT30) cobre o cadastro pelo bot; rotas presentes no `openapi.yaml` conferido ao vivo. |
| 4 | Os lembretes forem agendados **e enviados**. | ✅ | Agendamento: CT05, CT11, CT14, CT15 (`tests/unit/test_scheduler_firing.py`). Envio: log de execução real com `SchedulerService._fire` registrando disparos e 86 `sendMessage` entregues. |
| 5 | Os botões de confirmação funcionarem. | ✅ | CT06, CT07 (`tests/api/test_reminders.py`), CT23, CT25 (`tests/unit/test_bot_reminders_handler.py`). **Log de execução real: 17 `answerCallbackQuery`** — botões pressionados de verdade, não simulados. |
| 6 | O histórico permanecer persistido. | ✅ | CT39, CT40 (`tests/integration/test_seed_and_persistence.py`); CT11 cobre a reconstrução dos jobs a partir do banco. O seed roda duas vezes seguidas e devolve os mesmos ids (ver nº 15). |
| 7 | O cadastro por fotografia exigir confirmação. | ✅ | RN10 — CT19, CT20 (`tests/unit/test_bot_photo_voice.py`): `receive_photo` **nunca** sobrescreve o nome; o OCR só é exibido para conferência (`photo_ocr:sim/nao`). Log real: 4 `sendPhoto` e 2 `getFile`. |
| 8 | As mensagens por áudio funcionarem. | ✅ | CT22, CT27 (`tests/unit/test_notification_service.py`). **Log de execução real: 39 `sendAudio`**, incluindo o aviso de conversão para `.m4a` quando o TTS gera outro formato. |
| 9 | Os fluxos acessíveis puderem ser utilizados **sem digitação obrigatória**. | ✅ | CT24 (`tests/unit/test_bot_menu_structure.py` — navegação só por botões), CT29 (`tests/unit/test_accessibility_confirmation.py`), CT30 (fluxo acessível completo de ponta a ponta). RN11: o nome pode entrar por voz, com confirmação explícita. |
| 10 | A API REST estiver implementada. | ✅ | Execução ao vivo: **34 rotas** servidas, com `/health`, `/docs`, `/redoc`, `/openapi.json` e `/openapi.yaml` todos em HTTP 200. |
| 11 | O arquivo `docs/openapi.yaml` existir e for válido. | ✅ | Execução ao vivo: carrega em `yaml.safe_load`, declara `openapi: 3.1.0`, 34 *paths* e 32 *schemas*. CT33 valida o OpenAPI 3.1 na suíte. |
| 12 | O endpoint `/openapi.yaml` renderizar o YAML. | ✅ | Execução ao vivo: **HTTP 200**, `content-type: application/yaml`, 67.818 bytes, começando em `openapi: 3.1.0`. CT31 e CT32 cobrem o código e o *Content-Type*. |
| 13 | O Swagger estiver disponível em `/docs`. | ✅ | Execução ao vivo: **HTTP 200**, `text/html`. CT34 cobre a acessibilidade da Swagger UI. |
| 14 | O README possuir todas as seções obrigatórias. | ✅ | As 7 seções de §10.1–10.6 existem e as **10 seções adicionais de §10.7** também (estrutura, variáveis, exemplos de requisição, exemplos de mensagens, fluxos acessíveis, testes, validação do contrato, segurança, solução de problemas, limitações). §10.2 traz comandos para **Windows, macOS e Linux**; a tabela de §10.6 tem as 7 URLs exigidas. Ver [achado C](#5-achados-da-conferência). |
| 15 | Os dados de teste forem **fictícios e reproduzíveis**. | ✅ | `scripts/seed_test_data.py` executado **duas vezes seguidas** nesta conferência: mesmo usuário (`111222333`), mesmos medicamentos (ids 10, 11) e mesmos lembretes (ids 47–49) — é idempotente, não acumulativo. Cobre os 7 itens de §10.4, inclusive registro `confirmed`, `delivered` e `not_taken`. Imprime "não usar como orientação médica". CT40. |
| 16 | As regras de negócio estiverem documentadas. | ✅ | `docs/business_rules.md` (RN01–RN18) e esta wiki: [Bot e API](Regras-de-Negocio-Bot-e-API) e [Portal](Regras-de-Negocio-Portal) (RN19–RN32). **29 das 32 regras têm marcador no código** — ver [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade). |
| 17 | Os testes automatizados forem executáveis. | ✅ | Execução ao vivo nesta conferência: **201 testes, 201 aprovados, 86% de cobertura**, 34,3 s. Relatório HTML e `htmlcov/` gerados pelo `pytest-cov`, como pede §11. |
| 18 | A solução puder ser iniciada com Docker. | ❌ **Não verificado** | `Dockerfile` (17 linhas) e `docker-compose.yml` (43 linhas) existem e cobrem os 7 itens de §13. **Mas não há Docker instalado nesta máquina** (`which docker` → não encontrado), então `docker compose up` nunca foi executado. Permanece como validação sintática apenas, exatamente como o README já declara. Card: [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26). |
| 19 | As configurações sensíveis estiverem protegidas. | ⚠️ **Com ressalva** | **Atendido no versionamento:** `.env` está no `.gitignore`, não está rastreado, e `git log -S` confirma que o token **nunca entrou no histórico**; `.env.example` só tem *placeholders*; `core/config.py` se recusa a iniciar fora de desenvolvimento com segredo fraco ou com os dois segredos iguais ([#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30), 25 testes). **Ressalva:** o token do bot é gravado em texto claro no log — ver [achado A](#5-achados-da-conferência). |

---

## 4. O que esta conferência **não** cobre

Os 19 critérios de §15 são os do **escopo original** (bot, API e documentação). O portal web
de profissionais tem os seus próprios **16 critérios de aceite**, na seção 22 da especificação
do portal, e eles **não foram conferidos aqui** — nem estavam no escopo do
[#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39), que fala de §15.

Isso significa que, mesmo com esta página publicada, **a definição de "pronto" do portal
continua sem registro de conferência**. Ver [achado B](#5-achados-da-conferência).

Também fica fora o que nenhuma conferência de critérios pode resolver: os critérios dizem se o
sistema faz o que a especificação pediu, não se a especificação pediu a coisa certa. Isso
depende de contato com o público-alvo real —
[#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) e o
[Roteiro de Validação com Usuários](Roteiro-de-Validacao-com-Usuarios).

---

## 5. Achados da conferência

### Achado A — o token do bot é gravado em texto claro no log

**Severidade: alta.** `core/logging_config.py` ajusta o nível do logger **raiz**, então o
logger do `httpx` (usado internamente pelo `python-telegram-bot`) passa a emitir em `INFO` uma
linha `HTTP Request: POST https://api.telegram.org/bot<TOKEN>/sendMessage` para **cada**
chamada. O token aparece na URL.

| | |
|---|---|
| Linhas de log com o token | **26.482** (8.922 + 17.560 nos dois arquivos) |
| Onde | `logs/hora_do_remedio.log` e `.log.1`, ~7,2 MB em texto claro |
| No Git? | **Não.** `logs/` está no `.gitignore` e o token nunca entrou no histórico. |

Por que isso importa mesmo com o `logs/` ignorado: §12 do prompt master manda implementar logs
estruturados e **não registrar o que não é necessário**; um segredo de longa duração em texto
claro em disco é exatamente o tipo de dado que não deveria estar ali. Quem tiver acesso de
leitura ao arquivo — backup, log shipper, suporte — controla o bot por completo.

**Duas ações, não uma:** filtrar o log *e* **revogar o token atual pelo BotFather**, porque ele
já está exposto nesses arquivos. Filtrar sem revogar não desfaz a exposição.

Card: [#47](https://github.com/marluceqa-source/hora-do-remedio/issues/47).

### Achado B — o portal tem 16 critérios de aceite e nenhum registro de conferência

A especificação do portal (§22) define 16 critérios próprios, do acesso do profissional até a
execução por Docker Compose. Eles existem, estão recuperados no card e **nunca foram
conferidos item a item** — a mesma dívida que o [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39)
fechou para §15, ainda aberta para o portal.

Card: [#48](https://github.com/marluceqa-source/hora-do-remedio/issues/48).

### Achado C — numeração das seções do README

Cosmético, sem efeito sobre o critério nº 14: os títulos vão de `## 7. Estrutura do projeto`
direto para seções sem número e depois para `## 10. Limitações conhecidas` — 8 e 9 não
existem. Corrigido nesta conferência retirando o número de "Limitações conhecidas", de modo que
**1–7 são as seções obrigatórias de §10.1–10.6 e as sem número são as adicionais de §10.7** —
o que reflete a especificação em vez de contrariá-la. As 4 âncoras internas foram atualizadas.

---

## 6. O que muda na baseline

A baseline **1.0.0** declarava "42 dos 42 CT rastreáveis" e "201 testes" — ambos continuam
verdadeiros e agora têm esta página como registro de conferência dos critérios. O que muda:

- a lacuna "**critérios de aceite sem conferência registrada**" sai de
  [Limitações Conhecidas](Limitacoes-Conhecidas) e de
  [Validação e Verificação](Validacao-e-Verificacao) — ela foi fechada por esta página;
- entra uma lacuna nova e mais séria no lugar: o **achado A** (token em log);
- entra a lacuna do **achado B** (critérios do portal).

Fechar uma dívida de verificação e descobrir uma de segurança no mesmo trabalho é o resultado
esperado de uma conferência que não se limita a reler a documentação. Se os 19 critérios
tivessem sido marcados a partir do que o README afirma, o nº 19 teria passado liso.

---

## Próximo

- [Validação e Verificação](Validacao-e-Verificacao) — o que está verificado e o que não está validado.
- [Limitações Conhecidas](Limitacoes-Conhecidas) — a lista completa de lacunas.
- [Priorização e Backlog](Priorizacao-e-Backlog) — a ordem de atacar o que sobrou.
