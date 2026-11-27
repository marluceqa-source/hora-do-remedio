# Testes automatizados — Hora do Remédio (WEB + API)

> **Este branch tem apenas os testes.** O código da aplicação está no `main`, não aqui.
> Aponte `APP_DIR` para um diretório onde a aplicação esteja — veja
> [como rodar](../README.md#como-rodar).

Automação de testes do **Hora do Remédio** com [Playwright](https://playwright.dev) em
**JavaScript**, cobrindo as duas interfaces da aplicação:

- **API REST** (FastAPI, `http://localhost:8000`) — testes de requisição/resposta com o
  [API testing do Playwright](https://playwright.dev/docs/api-testing).
- **Portal web de profissionais de saúde** (React + Vite, `http://localhost:5173`) —
  testes de interface no navegador.

A aplicação sob teste é apontada por `APP_DIR` e **não é modificada** por este
projeto: a automação sobe a API e o portal, usa um banco SQLite próprio e cria a própria
massa de teste.

---

## 1. Como os testes foram desenhados

Nada aqui foi inventado no improviso. Cada teste nasceu de uma heurística:

| Técnica | Onde está |
| --- | --- |
| **VADER** (Verbs, Authorization, Data, Errors, Responsiveness) — heurística para APIs REST | [docs/casos-de-teste-api-vader.md](docs/casos-de-teste-api-vader.md) |
| **Gherkin** (Dado / Quando / Então) para os cenários de interface | [docs/casos-de-teste-web-gherkin.md](docs/casos-de-teste-web-gherkin.md) |
| **Heurísticas de ataque a tipos de dados e strings** (Test Obsessed / Elisabeth Hendrickson) | [docs/heuristicas-aplicadas.md](docs/heuristicas-aplicadas.md) |
| **Caso de teste no template da ISO/IEC/IEEE 29119-3** | [docs/casos-de-teste-api-vader.md](docs/casos-de-teste-api-vader.md) (casos detalhados) |
| **Relatório de Sessão** (Session-Based Test Management) com os riscos encontrados | [docs/relatorio-de-sessao.md](docs/relatorio-de-sessao.md) |
| **Evidências** em vídeo e screenshot de cada item do relatório | `evidencias/` (gerado por `npm run evidencias`) |
| **Relatório de testes em HTML**, com execução, casos, riscos e evidências | `relatorio.html` (gerado por `npm run relatorio`) |
| **Heurísticas de Elisabeth Hendrickson** aplicadas ao bot do Telegram | [../testes-bot-telegram](../testes-bot-telegram/README.md) |

**Resumo da cobertura:** 85 testes — 58 casos de API (VADER, sendo 1 fora da execução
padrão), 26 cenários de web (Gherkin) e 1 preparação de sessão autenticada.

**Última execução:** 84 passaram, 1 ignorado (o de limite de requisições, por decisão —
veja o fim do documento de casos de API).

---

## 2. Como instalar

### Pré-requisitos

- **Node.js 18 ou superior** (`node -v`)
- Playwright **1.62.1** (fixado no `package.json`) e o Chromium correspondente
- A aplicação `hora-do-remedio` clonada ao lado desta pasta, com:
  - o ambiente virtual Python criado e as dependências instaladas (`.venv`);
  - as dependências do portal instaladas (`cd frontend && npm install`);
  - o arquivo `.env` configurado (basta copiar o `.env.example` da aplicação).

### Instalação

```bash
npm install
```

```bash
npx playwright install chromium
```

Se os endereços ou caminhos do seu ambiente forem diferentes, copie o arquivo de exemplo e
ajuste:

```bash
cp .env.example .env
```

---

## 3. Como executar

A automação **sobe a API e o portal sozinha** (`webServer` do Playwright) e aplica as
migrações em um banco SQLite exclusivo antes de começar.

```bash
npm test
```

| Comando | O que faz |
| --- | --- |
| `npm test` | Roda tudo: API e web |
| `npm run test:api` | Só os testes de API (não abre navegador) |
| `npm run test:web` | Só os testes de interface |
| `npm run test:headed` | Testes de interface com o navegador visível |
| `npm run test:ui` | Abre o modo UI do Playwright (ótimo para investigar um teste) |
| `npm run evidencias` | Grava vídeo e screenshots de cada item do relatório de sessão |
| `npm run relatorio` | Monta `relatorio.html` com execução, casos, riscos e evidências |
| `npm run test:all` | Roda tudo, inclusive as evidências |
| `npm run report` | Abre o último relatório HTML |
| `npm run db:reset` | Apaga o banco da automação e recria o schema |

### Gerar as evidências do relatório de sessão

```bash
npm test && npm run evidencias
```

Isso grava em `evidencias/` um vídeo (`.webm`) e uma sequência de screenshots numeradas
para cada item do relatório de sessão — 10 vídeos e 33 telas. O projeto `evidencias` roda
com `slowMo`, para o vídeo ficar assistível por uma pessoa, e por isso fica fora do
`npm test`. A ordem importa: o item **I4** fotografa o relatório HTML da execução
anterior, então rode `npm test` antes.

As evidências não são só imagens: cada teste **assegura** o comportamento descrito no
relatório. Se a aplicação for corrigida, a evidência falha e avisa que o relatório
envelheceu.

### Gerar o relatório em HTML

```bash
npm test && npm run evidencias && npm run relatorio
```

Produz `relatorio.html` na raiz deste projeto: uma página só, para leitura humana, com o
resumo da execução, a lista de casos por arquivo, os riscos encontrados com vídeo e telas
embutidos, os defeitos, as observações e as perguntas em aberto. Nada é escrito à mão —
o conteúdo vem de `resultados/*.json`, de `evidencias/_itens/*.json` e de
[docs/relatorio-de-sessao.md](docs/relatorio-de-sessao.md).

Para um arquivo único, que viaja sozinho por e-mail ou anexo (imagens embutidas em
base64; os vídeos continuam na pasta):

```bash
node scripts/gerar-relatorio.js --embutir
```

> Esse relatório e o do Playwright (`npm run report`) são complementares: o do Playwright
> é a ferramenta de quem investiga uma falha, com trace e linha do tempo; este é o
> documento de quem lê o trabalho de teste.

Para rodar um caso específico, use o ID dele:

```bash
npx playwright test -g "CT-API-A11"
```

### Se você preferir subir a aplicação na mão

```bash
START_SERVERS=0 npm test
```

Nesse modo, suba os dois serviços antes (de dentro da pasta da aplicação):

```bash
DATABASE_URL="sqlite:///./database/playwright_test.db" RATE_LIMIT_PER_MINUTE=1000 .venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

```bash
cd frontend && npm run dev -- --port 5173 --strictPort
```

---

## 4. Estrutura do projeto

```
testes-playwright/
├── playwright.config.js     # 3 projetos: api, setup-portal e web; sobe API e portal
├── global-setup.js          # aplica as migrações no banco exclusivo da automação
├── fixtures/
│   └── index.js             # contextos de API prontos: sem auth, paciente, profissional, admin
├── support/
│   ├── config.js            # endereços, caminhos e variáveis de ambiente
│   ├── dados.js             # massa de teste única + cargas das heurísticas de string
│   ├── portal.js            # ações de API reutilizáveis (cadastro, login com MFA, paciente)
│   └── totp.js              # geração do código TOTP de 6 dígitos (RFC 6238)
├── tests/
│   ├── setup/               # cria e guarda a sessão autenticada do portal
│   ├── api/                 # um arquivo por pilar do VADER
│   └── web/                 # um arquivo por fluxo de tela
├── tests/evidencias/        # grava vídeo e screenshot de cada item do relatório
├── docs/                    # casos de teste, heurísticas e relatório de sessão
├── evidencias/              # vídeos e screenshots gerados (não versionado)
├── resultados/              # resultado de cada execução em JSON (entrada do relatório)
├── relatorio.html           # relatório de testes para leitura humana (não versionado)
└── scripts/
    ├── gerar-relatorio.js   # monta o relatorio.html
    ├── indice-evidencias.js # monta o índice da pasta evidencias/
    └── reset-db.js
```

### Decisões que valem explicação

- **Massa única por execução.** Cada teste cria o próprio profissional, paciente ou usuário
  do app, com e-mail e identificador únicos. Nenhum teste depende da ordem de execução nem
  do que outro deixou para trás — é o que permite rodar em paralelo e repetidas vezes.
- **Banco exclusivo.** A API sobe apontando para `database/playwright_test.db`. O banco de
  desenvolvimento da aplicação não é tocado.
- **Login por API, não por tela.** O projeto `setup-portal` faz o login completo
  (senha + TOTP) por API e salva o `storageState`; o projeto `web` abre o navegador já
  autenticado. Quem testa a tela de login é `tests/web/login-portal.spec.js`, de propósito.
- **MFA automatizado.** O portal exige um código de 6 dígitos de aplicativo autenticador.
  `support/totp.js` calcula esse código com a biblioteca padrão do Node — mesmo algoritmo
  que o backend valida com `pyotp`. Não há dependência externa para isso.
- **Testes que registram o comportamento atual.** CT-API-A13 e CT-API-D08 documentam
  comportamentos que divergem do esperado (riscos R1 e R2 do relatório de sessão). Eles
  passam hoje; se a aplicação mudar, falham de propósito e levam a conversa de volta ao
  relatório.

---

## 5. Dados de teste

Nenhuma massa precisa ser preparada à mão. A automação gera, a cada execução:

| Dado | Como é criado | Observação |
| --- | --- | --- |
| Profissional de saúde | `POST /api/v1/professionals` + login com MFA | e-mail único em `@example.com` |
| Administrador | igual, com `role: "admin"` | usado nos testes de RBAC |
| Paciente | `POST /api/v1/patients` | identificador interno único, nunca CPF |
| Usuário do app (paciente/bot) | `POST /api/v1/auth/token` | `telegram_user_id` único |
| Medicamento e horários | `POST /api/v1/medications` | dados fictícios, sem valor clínico |

> Todos os dados são sintéticos e não representam orientação médica real.
> `@exemplo.test` **não** serve como e-mail: o validador da API recusa TLDs reservados
> (CT-API-E08). Use `@example.com`.

---

## 6. Problemas comuns

| Sintoma | Causa e solução |
| --- | --- |
| `bad interpreter` ao subir a API | O `.venv` da aplicação foi criado antes da pasta ser renomeada. A automação já contorna usando `python -m uvicorn`; para resolver de vez, recrie o venv. |
| `Executable doesn't exist ... chromium` | Falta baixar o navegador: `npx playwright install chromium`. |
| Erros 429 em vários testes | A API subiu com o limite padrão de 60 requisições/minuto. Use `npm test` (que já passa `RATE_LIMIT_PER_MINUTE=1000`) ou exporte esse valor ao subir a API na mão. |
| `409` inesperado em um teste de cadastro | Banco da automação com massa antiga de uma execução interrompida: `npm run db:reset`. |
| A porta 8000 ou 5173 já está em uso | A automação reaproveita um servidor que já esteja no ar naquela URL. Se for outro serviço, pare-o ou aponte outras portas no `.env`. |
| Teste de web falha sem motivo claro | `npm run report` e abra o trace do teste: há vídeo, screenshot e a linha do tempo da falha. |

---

## 7. O que este projeto não cobre

- **Bot do Telegram** (RF04, RF07): não é alcançável por Playwright — ele roda em polling,
  sem tela e sem porta HTTP. Tem suíte própria em [../testes-bot-telegram](../testes-bot-telegram/README.md)
  (pytest), que exercita os handlers de verdade com as heurísticas de Elisabeth Hendrickson.
- **OCR, reconhecimento de fala e voz** (RF11 a RF13): dependem de Tesseract,
  faster-whisper e pyttsx3 instalados, além de arquivos de mídia.
- **Teste de carga e performance**: o pilar Responsiveness do VADER aqui busca degradação
  grosseira (segundos), não medição de performance.
- **Acessibilidade**: a aplicação tem recursos de acessibilidade declarados que merecem uma
  sessão de teste própria, com ferramenta específica.
