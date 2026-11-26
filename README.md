# Hora do Remédio 💊

Sistema de lembretes de medicamentos com foco forte em acessibilidade, composto por **três
entregas integradas**:

| Entrega | O que é | Para quem |
|---|---|---|
| **Bot do Telegram** | Interface de uso diário, navegável só por botões, com áudio, OCR e voz. | Pacientes e cuidadores |
| **API REST** | Camada documentada em OpenAPI, compartilhada pelo bot, pelo portal e por integrações externas. | Desenvolvedores |
| **Portal web** | Painel onde profissionais de saúde cadastram pacientes e prescrevem tratamentos. | Profissionais de saúde |

📖 **As regras de negócio completas (RN01–RN32), os requisitos funcionais e as decisões de
arquitetura estão na [Wiki do projeto](https://github.com/marluceqa-source/hora-do-remedio/wiki).**

O **prompt master** que originou este projeto é a especificação de origem dos requisitos
(RF01–RF14, RN01–RN18, CT01–CT42 e os critérios de aceite). Ele **não é versionado**: fica apenas
na máquina de quem desenvolve, em `Criacao/`. O conteúdo dele está refletido na
[Wiki do projeto](https://github.com/marluceqa-source/hora-do-remedio/wiki) — ver
[Engenharia de Requisitos](https://github.com/marluceqa-source/hora-do-remedio/wiki/Engenharia-de-Requisitos).

---

## 1. O que é esta aplicação?

### Objetivo

Ajudar pessoas a cadastrar seus medicamentos, receber lembretes automáticos no horário certo,
confirmar (ou não) que tomaram a dose, e consultar o histórico — tudo pelo Telegram, com uma
API REST por trás para integrações (ex.: um app de cuidador).

O **portal web** estende isso para o outro lado da relação: o profissional de saúde prescreve
o tratamento, e o paciente recebe os lembretes no Telegram sem precisar cadastrar nada.

### Público-alvo

- **Pacientes:** pessoas idosas, não alfabetizadas ou com dificuldade de leitura/visão.
- **Cuidadores:** familiares autorizados pelo próprio paciente.
- **Profissionais de saúde:** médicos, enfermeiros e outros profissionais, no portal web.

### O que o sistema **não** é

- **Não é um prescritor.** Não sugere medicamento, dose ou horário (RN13).
- **Não mede adesão real.** Mede **adesão declarada**: só o que o paciente confirmou (RN12).
  Silêncio nunca é registrado como "não tomou".

### Recursos de acessibilidade

- Navegação principal 100% por botões (menu fixo do Telegram), sem exigir digitação.
- Mensagens de voz (TTS local) no `/start`, na ajuda e, opcionalmente, em toda confirmação de
  ação (ligado/desligado em ⚙️ Configurações).
- Cadastro do nome do medicamento por **voz** (STT local), com confirmação antes de aceitar.
- Cadastro por **fotografia** da embalagem, com OCR local e confirmação explícita — o texto
  reconhecido nunca substitui o que a pessoa digitou.
- Suporte a cuidadores autorizados, com convite por código e revogação a qualquer momento.

### Funcionalidades

**No bot (paciente):** cadastro de medicamentos (nome, dosagem, quantidade, horários, datas,
observações, foto), lembretes automáticos recorrentes (diário, por dias da semana ou por
intervalo de horas), confirmação/adiamento/"não tomei", histórico filtrável por
dia/semana/mês, relatórios de adesão declarada (JSON ou CSV), e gestão de acesso de
cuidadores.

**No portal (profissional):** autenticação com MFA obrigatório, cadastro de pacientes, vínculo
do paciente ao Telegram por convite de uso único (QR Code), planos de tratamento versionados
com ciclo rascunho → ativo → suspenso, painel de adesão declarada e trilha de auditoria.

### Arquitetura

Dois processos (API e bot) compartilham a mesma camada `services/` — nenhuma regra de negócio
é duplicada entre eles. Detalhes completos, incluindo por que só o bot roda o agendador, em
[`docs/architecture.md`](docs/architecture.md).

O portal **não reimplementou o agendador**: ativar um tratamento *materializa* as entidades
`Medication`/`Schedule` que o agendador já consumia. Por isso bot, lembretes e histórico
continuaram funcionando sem alteração — ver
[Ciclo de Vida do Tratamento](https://github.com/marluceqa-source/hora-do-remedio/wiki/Ciclo-de-Vida-do-Tratamento).

### Tecnologias

**Backend:** Python 3.12, FastAPI, python-telegram-bot, SQLAlchemy + Alembic, APScheduler,
pyotp (TOTP), passlib + bcrypt, Tesseract OCR, faster-whisper (STT), pyttsx3 (TTS), pytest.
Lista completa e versões em [`requirements.txt`](requirements.txt).

**Portal:** Vite, React 19, TypeScript, MUI v9, React Router, Axios, React Hook Form + Zod,
`qrcode.react`. Versões em [`frontend/package.json`](frontend/package.json).

### Limitações

Ver a seção [Limitações conhecidas](#10-limitações-conhecidas) ao final deste documento.

---

## 2. Como instalar?

### Pré-requisitos

- Python 3.12+
- Git
- Tesseract OCR com o pacote de idioma português (`por`)
- **Node.js 20+ e npm** — só se for rodar o portal web
- (Opcional, só se for usar Docker) Docker e Docker Compose

### Clonar o repositório

```bash
git clone <url-do-seu-fork-ou-repositorio>
cd hora-do-remedio
```

### Configurar o ambiente Python

**macOS / Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Instalar as dependências do portal web

Só se for usar o portal:

```bash
cd frontend && npm ci && cd ..
```

### Instalar o Tesseract OCR (fora do pip)

- **macOS:** `brew install tesseract tesseract-lang`
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr tesseract-ocr-por`
- **Windows:** instalador em https://github.com/UB-Mannheim/tesseract/wiki — depois, aponte
  `TESSERACT_CMD` no `.env` para o caminho do executável.

### Configurar o `.env`

```bash
cp .env.example .env
```

Edite o `.env` e preencha ao menos `TELEGRAM_BOT_TOKEN` e `API_SECRET_KEY` (veja a seção
[Variáveis de ambiente](#variáveis-de-ambiente) abaixo).

Gere os dois segredos — **valores diferentes entre si** — com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> Com `APP_ENV` diferente de `development`/`dev`/`local`/`test`/`testing`, a aplicação
> **se recusa a iniciar** enquanto `API_SECRET_KEY` ou `PROFESSIONAL_SESSION_SECRET_KEY`
> estiver com valor de exemplo, vazio, com menos de 32 caracteres — ou se os dois forem
> iguais, o que anularia a separação entre as duas autenticações (RN19). Em
> desenvolvimento, os valores de exemplo continuam funcionando.

### Criar o bot pelo BotFather

1. Abra https://t.me/BotFather no Telegram.
2. Envie `/newbot` e siga as instruções (nome de exibição e `@usuario_bot`).
3. Copie o token gerado para `TELEGRAM_BOT_TOKEN` no `.env`.

### Inicializar o banco e rodar as migrações

```bash
alembic upgrade head
```

Isso cria `database/hora_do_remedio.db` (SQLite) com todas as tabelas.

---

## 3. Como executar?

### Inicializar a API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Inicializar o bot do Telegram

Em outro terminal (com a venv ativa):

```bash
python -m bot.main
```

> O agendador de lembretes (APScheduler) roda dentro deste processo — rode só **uma**
> instância do bot por vez (ver [`docs/architecture.md`](docs/architecture.md)).

### Inicializar o portal web

Em um terceiro terminal:

```bash
cd frontend && npm run dev
```

O portal sobe em http://localhost:5173 e fala com a API em http://localhost:8000.

> A sessão do profissional é um cookie `httpOnly`, então a API precisa autorizar a origem do
> portal: mantenha `CORS_ORIGINS` no `.env` incluindo `http://localhost:5173`. Para apontar o
> portal a outra API, use `VITE_API_BASE_URL`.

### Primeiro acesso ao portal (MFA obrigatório)

O MFA não é opcional — sem ele não há sessão. O fluxo completo na primeira vez:

1. Abra http://localhost:5173/signup e crie a conta do profissional.
   O cadastro é uma **solicitação**: a conta nasce com `verification_status = pending`.
2. Faça login com e-mail e senha. A senha **não** devolve sessão, e sim um desafio de MFA.
3. O portal exibe um **QR Code** — escaneie com um aplicativo autenticador (Google
   Authenticator, Authy etc.). Quem não puder escanear pode copiar o código exibido abaixo.
4. Digite o código de 6 dígitos. **Só agora** a sessão é criada.

Nos acessos seguintes, o passo 3 desaparece: senha → código de 6 dígitos.

> Para ativar tratamentos é preciso o papel `medico` (RN20) — veja
> [Papéis e Permissões](https://github.com/marluceqa-source/hora-do-remedio/wiki/Papeis-e-Permissoes).
> Para liberar a verificação de um profissional ou ler a auditoria, é preciso o papel `admin`.

### Vincular um paciente ao Telegram

1. No portal, cadastre o paciente (identificador interno — **nunca** CPF ou documento).
2. Na tela do paciente, gere o convite. O portal mostra um **QR Code** e um link
   `https://t.me/<seu_bot>?start=<token>`.
3. O paciente aponta a câmera ou toca no link — **sem digitar nada** — e confirma no bot.

O convite é de **uso único** e expira em 30 minutos (RN23/RN24). Ajuste
`TELEGRAM_BOT_USERNAME` no `.env` para que o link aponte para o seu bot.

### Executar com Docker Compose

```bash
docker compose up --build
```

Isso sobe três serviços: `migrate` (roda as migrações e encerra), `api` (porta 8000) e `bot`
(polling do Telegram). Dados do SQLite, uploads e logs ficam em volumes nomeados, então
sobrevivem a `docker compose down` (sem `-v`).

> ⚠️ **O Docker ainda não cobre o portal web.** `Dockerfile` e `docker-compose.yml` não têm
> nenhuma referência a Node ou `frontend/` — para usar o portal, rode-o localmente com
> `npm run dev` (ou `npm run build` e sirva os estáticos). Acompanhado em
> [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26).

**Reiniciar os serviços:**

```bash
docker compose restart api bot
```

**Reconstruir após mudar dependências:**

```bash
docker compose up --build
```

> **Nota:** o `Dockerfile`/`docker-compose.yml` foram escritos e validados sintaticamente
> (YAML), mas o build/execução real em Docker **não foi testado** neste ambiente de
> desenvolvimento, que não tem o Docker instalado. Antes de usar em produção, rode
> `docker compose up --build` uma vez e confira os logs dos três serviços.

### Consultar logs

- Execução local: logs vão para `./logs/hora_do_remedio.log` (rotativo) e para o terminal.
- Docker: `docker compose logs -f api` ou `docker compose logs -f bot`.

### Executar os testes

```bash
pytest
```

### Gerar cobertura

A cobertura já é gerada a cada `pytest` (configurado em [`pytest.ini`](pytest.ini)). Depois de
rodar, abra `htmlcov/index.html` no navegador. Um relatório HTML dos próprios testes também é
gerado em `reports/test_report.html`.

---

## 4. Quais dados de teste estão incluídos?

Dados **inteiramente sintéticos**, só para desenvolvimento — nunca usar como orientação
médica. O script [`scripts/seed_test_data.py`](scripts/seed_test_data.py) cria:

- Um usuário fictício (`telegram_user_id = 111222333`).
- 2 medicamentos de demonstração ("Losartana (fictício)" diária às 08:00, "Vitamina D
  (fictício)" às segundas/quartas/sextas às 12:00).
- 3 lembretes fictícios: um confirmado, um entregue mas ainda sem confirmação, e um marcado
  como não tomado.

### Como inserir os dados

```bash
python scripts/seed_test_data.py
```

O script é idempotente — rodar de novo substitui os dados do mesmo usuário fictício, sem
duplicar (coberto pelo teste `test_ct40_seed_script_runs_and_is_idempotent`).

> O seed cobre apenas o lado do paciente: **não cria profissionais, pacientes do portal nem
> planos de tratamento**. Para experimentar o portal, crie a conta pelo `/signup` e siga o
> [primeiro acesso](#primeiro-acesso-ao-portal-mfa-obrigatório).

### Exemplo de resposta da API usando esses dados

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 111222333}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 5. Quais são as regras de negócio?

| Escopo | Regras | Onde |
|---|---|---|
| Bot e API (paciente) | **RN01–RN18** | [`docs/business_rules.md`](docs/business_rules.md) · [Wiki](https://github.com/marluceqa-source/hora-do-remedio/wiki/Regras-de-Negocio-Bot-e-API) |
| Portal (profissional) | **RN19–RN32** | [Wiki](https://github.com/marluceqa-source/hora-do-remedio/wiki/Regras-de-Negocio-Portal) |

Cada regra aponta **onde está implementada e qual teste a cobre** — a documentação não promete
mais do que o código entrega.

As duas que mais condicionam o produto:

- **RN12** — ausência de resposta **não** significa que o medicamento não foi tomado. Todo
  relatório é de adesão **declarada**, nunca real.
- **RN20** — só um profissional com papel `medico` pode **ativar** um tratamento. A API
  responde 403 e o portal desabilita o botão explicando o motivo em texto.

> **RN29 e RN31 não têm marcação em nenhum arquivo do repositório.** A numeração do portal
> salta, e a documentação registra a lacuna em vez de inventar o conteúdo delas — acompanhado
> em [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23).

---

## 6. Quais são as URLs importantes?

| Recurso | URL |
|---|---|
| **Portal web** | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| YAML | http://localhost:8000/openapi.yaml |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health Check | http://localhost:8000/health |
| BotFather | https://t.me/BotFather |
| **Wiki** | https://github.com/marluceqa-source/hora-do-remedio/wiki |
| **Pendências** | [issues com rótulo `pendência`](https://github.com/marluceqa-source/hora-do-remedio/issues?q=is%3Aissue+is%3Aopen+label%3Apend%C3%AAncia) |

O endereço real do seu bot (`https://t.me/<nome_do_seu_bot>`) depende do nome escolhido ao
criá-lo pelo BotFather — não há uma URL fixa de produção para documentar aqui.

---

## 7. Estrutura do projeto

```text
hora-do-remedio/
├── api/            # FastAPI: rotas, schemas Pydantic, dependências
├── bot/            # python-telegram-bot: handlers, teclados, main.py
├── core/           # configuração, logging, segurança (JWT do paciente e sessão do portal)
├── services/       # regras de negócio compartilhadas entre api/ e bot/
├── database/       # modelos SQLAlchemy e conexão
├── frontend/       # portal web: React + TypeScript + MUI (Vite)
│   └── src/        #   api/ (cliente e tipos), pages/, components/, context/
├── alembic/        # migrações do banco
├── docs/           # openapi.yaml, architecture.md, business_rules.md
├── wiki/           # páginas publicadas na Wiki do GitHub (fonte versionada)
├── scripts/        # export_openapi.py, seed_test_data.py, criar_cards_github.sh
├── tests/          # unit/, integration/, api/, contract/, accessibility/
├── assets/         # illustrations/ (ilustrações de acessibilidade), uploads/ (fotos, não versionado)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Variáveis de ambiente

Todas documentadas com valores de exemplo em [`.env.example`](.env.example): nome/fuso/locale
da app, `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, segredo e algoritmo do JWT da API, limite de
requisições, política de retenção, configuração de OCR/STT/TTS, nível de log e host/porta da
API.

As específicas do portal:

| Variável | Padrão | O que faz |
|---|---|---|
| `PROFESSIONAL_SESSION_SECRET_KEY` | `change-me-...` | **Troque.** Segredo da sessão do profissional, independente do JWT do paciente (RN19) e diferente de `API_SECRET_KEY`. |
| `PROFESSIONAL_SESSION_COOKIE_NAME` | `hdr_professional_session` | Nome do cookie `httpOnly`. |
| `PROFESSIONAL_SESSION_EXPIRE_MINUTES` | `480` | Validade da sessão (8 h). |
| `PROFESSIONAL_MFA_PRE_AUTH_EXPIRE_MINUTES` | `5` | Janela para concluir o MFA depois da senha. |
| `PROFESSIONAL_MAX_FAILED_LOGINS` | `5` | Tentativas antes do bloqueio (RN30). |
| `PROFESSIONAL_LOCKOUT_MINUTES` | `15` | Duração do bloqueio. |
| `PROFESSIONAL_PASSWORD_RESET_EXPIRE_MINUTES` | `30` | Validade do token de recuperação. |
| `PATIENT_INVITE_EXPIRE_MINUTES` | `30` | Validade do convite de vínculo (RN23). |
| `TELEGRAM_BOT_USERNAME` | — | Usado para montar o deep link do convite. |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Origens autorizadas a enviar o cookie de sessão. |

No frontend, `VITE_API_BASE_URL` (padrão `http://localhost:8000`) aponta o portal à API.

## Exemplos de requisições

Cadastrar um medicamento (depois de obter um `access_token` como no exemplo da seção 4):

```bash
curl -X POST http://localhost:8000/api/v1/medications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
        "name": "Losartana",
        "dosage": "50mg",
        "quantity": "1 comprimido",
        "start_date": "2026-11-17",
        "schedules": [{"recurrence_type": "daily", "schedule_time": "08:00:00"}]
      }'
```

Consultar os lembretes de hoje:

```bash
curl http://localhost:8000/api/v1/reminders/today -H "Authorization: Bearer $TOKEN"
```

## Exemplos de mensagens do Telegram

- `/start` → texto de boas-vindas + áudio + menu fixo com os 7 botões (💊 📅 ➕ 🔊 📊 ⚙️ ❓).
- Lembrete (no horário programado) → foto do medicamento (se cadastrada) + texto + áudio +
  botões inline `✅ Tomei` / `⏰ Lembrar Depois` / `❌ Não Tomei`.
- Cadastro por voz do nome → bot transcreve e pergunta "Entendi: '...'. Está correto?" com
  botões `✅ Sim` / `❌ Não` antes de aceitar.

## Fluxos acessíveis

- Toda a navegação principal usa o teclado fixo do Telegram (sem digitação).
- Campos que precisam de texto (nome, dosagem, quantidade, datas, observações) aceitam
  digitação **ou** áudio, dependendo do campo (hoje, voz está implementada para o nome do
  medicamento — ver [limitações](#10-limitações-conhecidas)).
- Cada ação importante (dose confirmada, cadastro salvo, dose não tomada) pode vir acompanhada
  de confirmação sonora — ligar/desligar em ⚙️ Configurações.
- `/cancelar` interrompe e reinicia qualquer cadastro em andamento.

## Como executar testes

```bash
pytest                              # suíte completa, com cobertura e relatório HTML
pytest tests/unit                   # só os testes unitários (serviços)
pytest tests/api                    # só a API (FastAPI TestClient)
pytest tests/contract               # só o contrato OpenAPI
pytest -k ct30                      # um cenário específico (ex.: CT30, fluxo acessível completo)
```

Todas as integrações externas (Telegram, OCR, STT, TTS) são mockadas nos testes automatizados
— nada chama de verdade a API do Telegram, o binário do Tesseract ou os modelos de
voz/transcrição durante `pytest`.

Estado atual: **185 testes passando, 86% de cobertura.**

No portal, a verificação hoje é só de tipos:

```bash
cd frontend && npx tsc -b      # type-check
cd frontend && npm run build   # build de produção
```

**Não há testes automatizados no `frontend/`** — ver [limitações](#10-limitações-conhecidas).

## Como validar o contrato OpenAPI

```bash
python scripts/export_openapi.py   # regenera docs/openapi.yaml a partir das rotas atuais
pytest tests/contract               # falha se docs/openapi.yaml divergir do que a API serve
```

`/docs`, `/redoc`, `/openapi.json` e `/openapi.yaml` são todos gerados a partir do mesmo
`app.openapi()` — não há como divergirem entre si por construção.

## Segurança e privacidade

- Nenhuma credencial real deve ir para o `.env.example` ou para o repositório — só o `.env`
  local, que está no `.gitignore`.
- A API usa JWT próprio (RN09: cada usuário só vê seus dados), independente do token do bot.
- OCR, STT e TTS rodam 100% localmente — nenhuma foto, áudio ou texto de medicamento é
  enviado a serviços de terceiros.
- O bot nunca sugere ou altera dosagens (RN13); a confirmação de dose é uma declaração do
  usuário, não uma comprovação clínica (RN04, RN12).
- Ver também [Limitações conhecidas](#10-limitações-conhecidas) sobre retenção de dados.

No portal (detalhes em
[Segurança e Privacidade](https://github.com/marluceqa-source/hora-do-remedio/wiki/Seguranca-e-Privacidade)):

- **Autenticação separada da do paciente** (RN19), com segredo próprio: vazar uma não
  compromete a outra.
- **MFA TOTP obrigatório** — a senha sozinha nunca cria sessão.
- Token de sessão **opaco**, persistido **só como hash**: quem leia o banco não reconstrói uma
  sessão, e o logout é revogação real no servidor (RN30).
- Convites de vínculo também guardados só como hash, de **uso único** e temporários
  (RN23/RN24).
- Recuperação de acesso **não revela se o e-mail existe**; ao ser consumida, encerra todas as
  sessões anteriores.
- Paciente identificado por **identificador interno**, nunca CPF ou documento. Campo de
  contato é opcional e só deve ser preenchido se autorizado.
- Operações sensíveis são **auditáveis** (RN32); a trilha é restrita a `admin` e expõe
  auditoria, nunca dados clínicos.
- Nenhuma mensagem crua de framework chega ao usuário: erros do Pydantic são traduzidos com o
  rótulo do campo, e os do Axios substituídos por texto em português.

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot não inicia: `RuntimeError: TELEGRAM_BOT_TOKEN não configurado` | `.env` sem token, ou não copiado de `.env.example` | `cp .env.example .env` e preencha o token do BotFather |
| OCR sempre retorna vazio | Tesseract não instalado ou sem o pacote `por` | Reinstale com o pacote de idioma (ver seção 2) |
| Transcrição de voz muito lenta na primeira vez | `faster-whisper` baixando o modelo do Hugging Face | Normal na primeira execução; fica em cache depois |
| TTS não produz áudio no Linux | Falta o `espeak` (driver usado pelo `pyttsx3` fora do macOS/Windows) | `sudo apt-get install espeak` (já incluso no `Dockerfile`) |
| `alembic upgrade head` falha dizendo que a tabela já existe | Banco criado fora do fluxo de migração | Apague `database/hora_do_remedio.db` (ambiente de desenvolvimento) e rode a migração de novo |
| Testes de contrato falham após mexer em rotas/schemas | `docs/openapi.yaml` ficou desatualizado | Rode `python scripts/export_openapi.py` antes de testar de novo |
| Portal faz login mas a sessão "não cola" (volta para o login) | A API não está autorizando a origem do portal, então o cookie `httpOnly` não é aceito | Inclua `http://localhost:5173` em `CORS_ORIGINS` no `.env` e reinicie a API |
| Portal não consegue falar com a API | `VITE_API_BASE_URL` apontando para outro endereço | Ajuste a variável e reinicie o `npm run dev` (Vite só lê `VITE_*` no start) |
| Botão "Ativar tratamento" desabilitado | O profissional não tem papel `medico` (RN20) | Use uma conta com `role = medico`; o próprio portal explica isso em texto sob o botão |
| Não é possível ativar: pede paciente vinculado | O paciente ainda não concluiu o vínculo com o Telegram | Gere o convite na tela do paciente e peça que ele toque no link / leia o QR Code |
| Convite de vínculo "não funciona" | Convite é de uso único e expira em 30 min (RN23/RN24) | Gere um novo convite |
| Link do convite aponta para o bot errado | `TELEGRAM_BOT_USERNAME` não configurado ou desatualizado | Ajuste no `.env` e reinicie a API |
| Erro de login no portal: `AttributeError: __about__` | `bcrypt` incompatível com o `passlib` | Use `bcrypt==4.0.1`, como fixado em `requirements.txt` |

## 10. Limitações conhecidas

- **Ilustrações de acessibilidade (RF11):** só 4 das 11 do símbolo-tabela têm imagem própria
  (fornecidas pelo usuário); as demais usam o emoji Unicode do símbolo como equivalente.
- **Áudio como "mensagem de voz":** por causa do formato gerado pelo `pyttsx3`, o bot envia
  áudio via `send_audio` (bolha de arquivo), não `send_voice` (bolha de voz) — ver
  [`docs/architecture.md`](docs/architecture.md#limitação-conhecida-de-áudio).
- **Entrada por voz (RF04):** implementada para o campo "nome do medicamento"; os demais
  campos (dosagem, quantidade, observações) hoje só aceitam digitação.
- **Retenção de dados (RN17):** a configuração existe, mas não há job de expurgo automático.
- **Docker:** `Dockerfile`/`docker-compose.yml` foram escritos e validados apenas
  sintaticamente — o build/execução real não foi testado neste ambiente (sem Docker
  instalado). Rode `docker compose up --build` e confira os logs antes de usar em produção.
  **Além disso, o Docker não cobre o portal web** ([#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26)).
- **Portal sem testes automatizados:** não há nenhum teste em `frontend/`. Playwright (E2E) e
  axe-core (acessibilidade) não foram configurados, então as decisões de acessibilidade do
  portal **não foram auditadas automaticamente**
  ([#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24),
  [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25)).
- **Recuperação de acesso do portal:** o token é gerado corretamente, mas **o ambiente não
  envia e-mails reais** — a própria tela avisa que o token deve ser obtido com o administrador
  ([#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29)).
- **Segredos em desenvolvimento:** os valores de exemplo continuam aceitos quando `APP_ENV` é
  um ambiente de desenvolvimento — é só fora dele que a aplicação recusa iniciar. Ou seja, a
  proteção **não** impede que alguém rode com segredo fraco marcando o ambiente como `dev`.
- **RN29 e RN31:** sem correspondência no código; é preciso conferir a especificação do portal
  e então documentar ou descartar
  ([#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)).
- **Sem testes de carga:** a aplicação não foi avaliada sob concorrência real de múltiplos
  usuários; SQLite é adequado para desenvolvimento/demonstração, não para produção em escala
  (ver recomendação de PostgreSQL em [`docs/architecture.md`](docs/architecture.md)).
- **CT17** ("botões antigos ou expirados") do checklist de testes do prompt master não tem
  teste automatizado dedicado.
