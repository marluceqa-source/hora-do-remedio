# Relatório de Sessão

Inspirado no artigo de Jonathan Bach sobre Session-Based Test Management (2001).

| Data e Hora do Início | Nome do Testador | Módulo |
| --- | --- | --- |
| 26 de novembro de 2026, 21h30 | Marluce Vitor | Portal de profissionais (web), API REST e bot do Telegram do Hora do Remédio |

**Test Charter:** Explorar o portal web e a API REST do Hora do Remédio com Playwright em
JavaScript, usando a heurística VADER para a API e as heurísticas de ataque a tipos de
dados e strings para os formulários, para descobrir onde o comportamento observado difere
do que o contrato e as telas prometem — e deixar isso automatizado.

**Tamanho da Sessão:** 120 minutos

---

## Notas

Podem ser **(I)** informações ou **(R)** riscos.

- **(I) I1 — As duas autenticações da aplicação são independentes (RN19).** A aplicação separa de propósito: JWT no
  cabeçalho para o app do paciente/bot e cookie httpOnly de sessão para o portal. Testei as
  duas e confirmei que uma não vale pela outra (CT-API-A07).
- **(I) I2 — O login com MFA é automatizado pelo cálculo do código TOTP.** O portal exige MFA. Para automatizar de ponta a ponta, implementei
  o cálculo do código em `support/totp.js` (HMAC-SHA1, RFC 6238) e conferi que o resultado
  é idêntico ao do `pyotp`, que o backend usa para validar. No primeiro acesso o segredo
  vem na própria tela, em `provisioning_uri`.
- **(I) I3 — A sessão autenticada é reaproveitada do setup, sem passar pelo login.** O storageState capturado do `APIRequestContext` depois do login é aceito pelo
  navegador: o projeto `setup-portal` autentica por API e o projeto `web` abre o portal já
  logado. O cookie precisa ser emitido para o domínio `localhost` (e não `127.0.0.1`) para
  valer também na porta do portal.
- **(R) R1 — Profissional não verificado já tem acesso clínico.** A tela de cadastro informa
  que a conta "ainda precisa ser verificada por um administrador antes de ter acesso clínico
  pleno". Na prática, um profissional recém-cadastrado (`verification_status: "pending"`)
  cadastra paciente, gera convite de vínculo e abre o dashboard. O controle de acesso
  (`require_roles`) olha apenas o PAPEL; `verification_status` não é verificado em nenhum
  endpoint — só é lido e alterado pelos endpoints de administração. Ou a mensagem promete
  demais, ou falta o bloqueio. Registrado em CT-API-A13.
- **(R) R2 — Campo obrigatório aceita apenas espaços.** `name` do medicamento e `full_name`
  do paciente exigem no mínimo 1 caractere, e espaço conta como caractere: `"   "` é aceito
  com 201. O cadastro vazio (`""`) é corretamente recusado com 422. Registrado em CT-API-D08.
- **(R) R3 — A normalização de texto depende da porta de entrada.** Pela API e pelo portal,
  `"  Losartana  "` é gravado e devolvido com os espaços nas bordas; pelo bot do Telegram o
  mesmo nome entra como `"Losartana"`, porque os handlers fazem `strip()` antes de gravar.
  Dois cadastros que a pessoa lê como iguais convivem no sistema, a busca visual na lista
  fica confusa — e o resultado muda conforme o caminho usado. Registrado em CT-API-D08 e
  CT-BOT-S02.
- **(R) R4 — O limite de requisições é por IP, não por usuário.** `RATE_LIMIT_PER_MINUTE`
  padrão de 60 com `slowapi` e `get_remote_address`. Bot e portal atrás do mesmo IP (NAT,
  proxy, container) dividem a mesma cota, e um deles pode derrubar o outro. Também foi o que
  obrigou a automação a subir a API com limite alto.
- **(R) R5 — Ambiente: o venv da aplicação tem shebang quebrado.** O `.venv` foi criado
  quando a pasta se chamava `ProjetoFinalTURMA5` (hoje `0_ProjetoFinalTURMA5`), então
  `.venv/bin/uvicorn` e `.venv/bin/alembic` falham com `bad interpreter`. O contorno é
  `.venv/bin/python -m uvicorn` / `-m alembic`, que é o que a automação usa. Recriar o venv
  resolve de vez.
- **(R) R6 — O bot aceita dois medicamentos com o mesmo nome, sem aviso.** Cadastrar
  "Losartana" duas vezes cria dois registros e dois conjuntos de lembretes. Para alguém que
  usa vários remédios, dois lembretes idênticos no mesmo horário são exatamente o tipo de
  confusão que o aplicativo existe para evitar. Registrado em CT-BOT-D01.
- **(R) R7 — Um erro de validação no último passo do bot descarta o cadastro inteiro.** Com
  um nome acima de 200 caracteres, o bot explica o motivo e encerra a conversa: o rascunho
  some e a pessoa recomeça do primeiro campo. O tratamento do erro está correto; o custo é
  que, para o público-alvo (pessoas idosas), refazer 16 passos é caro. Validar o tamanho na
  hora da digitação resolveria. Registrado em CT-BOT-S06.
- **(I) I6 — O bot do Telegram pede outra ferramenta, e isso mudou o plano.** Ele roda em
  polling: não tem porta HTTP nem tela, então Playwright não alcança. Os handlers foram
  exercitados como funções, com `update` e `context` dublês, em um projeto pytest à parte
  (`../testes-bot-telegram`). O código exercitado é o mesmo que roda em produção; o que fica
  de fora é a entrega da mensagem pelo Telegram.

- **(I) I4 — Resultado da execução da suíte.** Ao fim da sessão: **161 testes, 160 aprovados
  e 1 ignorado** — 85 no portal e na API (Playwright, JavaScript) e 76 no bot do Telegram
  (pytest, Python). O ignorado é o de limite de requisições por minuto, que depende de a API
  subir com limite baixo. Nenhum teste ficou instável nas execuções repetidas.
- **(I) I5 — O que a aplicação faz bem.** Ficou registrado em teste: o isolamento entre usuários
  responde 404 em vez de 403 (não confirma a existência do recurso); login e recuperação de
  senha usam mensagem genérica, sem revelar se o e-mail existe; exclusão de medicamento
  exige `confirm=true`; erros de validação têm formato único (`code: validation_error`); e
  entrada hostil (injeção de SQL, JSON malformado, id com tipo errado) vira 422/201 literal,
  nunca 500.

## Defeitos

Nenhum defeito que impeça o uso foi encontrado nesta sessão. Os pontos acima são **riscos e
divergências de expectativa** (R1 a R5), que valem decisão do time antes de virarem bug:

1. **R1** — divergência entre a mensagem de cadastro e o controle de acesso real. É o
   candidato mais forte a bug: envolve acesso a dado clínico.
2. **R2 / R3** — validação e normalização de texto (um defeito de dados, de severidade baixa,
   mas que suja a base).

## Perguntas

1. `verification_status: "pending"` deveria bloquear o acesso clínico, ou a mensagem da tela
   de cadastro é que precisa ser corrigida?
2. Campos obrigatórios de texto deveriam passar por `strip()` antes da validação de tamanho?
3. O limite de requisições deveria ser por usuário/token autenticado, em vez de por IP?
4. Qual é o tempo de resposta aceitável acordado para a API? Os limites usados nos testes de
   responsividade (1,5 s / 3 s / 5 s) foram escolhidos por mim para pegar degradação
   grosseira, não combinados com o time.
5. Existe ambiente de testes com banco próprio e massa conhecida, ou a automação deve
   continuar criando a própria massa a cada execução (é o que ela faz hoje)?

---

## Onde cada achado foi registrado

Os sete riscos viraram issues no board do projeto, todos em **Backlog** e em aberto:

| Achado | Issue |
| --- | --- |
| **R1** | [#177](https://github.com/marluceqa-source/hora-do-remedio/issues/177) |
| **R2** | [#178](https://github.com/marluceqa-source/hora-do-remedio/issues/178) |
| **R3** | [#179](https://github.com/marluceqa-source/hora-do-remedio/issues/179) |
| **R4** | [#180](https://github.com/marluceqa-source/hora-do-remedio/issues/180) |
| **R5** | [#181](https://github.com/marluceqa-source/hora-do-remedio/issues/181) |
| **R6** | [#182](https://github.com/marluceqa-source/hora-do-remedio/issues/182) |
| **R7** | [#183](https://github.com/marluceqa-source/hora-do-remedio/issues/183) |

R1, R2, R3, R6 e R7 levam o rótulo `bug` — são divergências entre o que o sistema faz e o que
promete. R4 e R5 ficaram só como `pendência`: um é decisão de projeto, o outro é ambiente.

---

## Evidências

Cada item deste relatório tem vídeo e screenshots gravados pela automação, na pasta
`evidencias/`. **Esses arquivos não são versionados** — são artefatos, reproduzidos a
qualquer momento pelo comando abaixo, sempre pelo mesmo caminho. Os testes que geram as
evidências também
**asseguram o comportamento descrito**: se a aplicação for corrigida, a evidência falha e
avisa que este relatório ficou desatualizado.

```bash
npm test && npm run evidencias
```

| Item | Arquivo de vídeo | Telas | Onde foi gravado |
| --- | --- | --- | --- |
| **I1** | `I1-video.webm` | 3 screenshots | Navegador autenticado no portal consultando a API e o Swagger |
| **I2** | `I2-video.webm` | 5 screenshots | Tela de login, primeiro acesso com QR Code |
| **I3** | `I3-video.webm` | 4 screenshots | Arquivo de sessão em disco + portal aberto já logado |
| **I4** | `I4-video.webm` | 2 screenshots | Relatório HTML da execução anterior da suíte |
| **I5** | `I5-video.webm` | 4 screenshots | Tela de login, recuperação de acesso e contrato no Swagger |
| **R1** | `R1-video.webm` | 5 screenshots | Cadastro, login, ficha do paciente e convite de vínculo |
| **R2** | `R2-video.webm` | 3 screenshots | Formulário de cadastro de profissional |
| **R3** | `R3-video.webm` | 3 screenshots | Cadastro e lista de pacientes + resposta da API |
| **R4** | `R4-video.webm` | 3 screenshots | Segunda instância da API, subida com limite de 3 por minuto |
| **R5** | `R5-video.webm` | 1 screenshots | Saída real dos comandos do venv da aplicação |

> As questões em aberto no fim deste relatório não têm evidência de tela: são perguntas
> para o time, não observações sobre o comportamento da aplicação.
>
> **R6, R7 e I6** também não têm vídeo: vêm dos testes do bot do Telegram, que não tem tela
> para gravar. A evidência deles é o próprio teste automatizado, citado no texto de cada
> item — veja [os casos do bot](../../testes-bot-telegram/docs/casos-de-teste-bot-heuristicas.md).
