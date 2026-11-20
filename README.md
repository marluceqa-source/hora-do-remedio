# Hora do Remédio 💊

Aplicação integrada ao Telegram para ajudar pessoas a lembrar de tomar seus medicamentos,
com uma API REST documentada e foco forte em acessibilidade.

O prompt master completo que originou este projeto está em
[`Criacao/# PROMPT MASTER — HORA DO REMÉDIO 💊.md`](Criacao/%23%20PROMPT%20MASTER%20%E2%80%94%20HORA%20DO%20REM%C3%89DIO%20%F0%9F%92%8A.md).

---

## 1. O que é esta aplicação?

### Objetivo

Ajudar pessoas a cadastrar seus medicamentos, receber lembretes automáticos no horário certo,
confirmar (ou não) que tomaram a dose, e consultar o histórico — tudo pelo Telegram, com uma
API REST por trás para integrações (ex.: um app de cuidador).

### Público-alvo

Pessoas idosas, não alfabetizadas ou com dificuldade de leitura/visão, e seus
familiares/cuidadores autorizados.

### Recursos de acessibilidade

- Navegação principal 100% por botões (menu fixo do Telegram), sem exigir digitação.
- Mensagens de voz (TTS local) no `/start`, na ajuda e, opcionalmente, em toda confirmação de
  ação (ligado/desligado em ⚙️ Configurações).
- Cadastro do nome do medicamento por **voz** (STT local), com confirmação antes de aceitar.
- Cadastro por **fotografia** da embalagem, com OCR local e confirmação explícita — o texto
  reconhecido nunca substitui o que a pessoa digitou.
- Suporte a cuidadores autorizados, com convite por código e revogação a qualquer momento.

### Funcionalidades

Cadastro de medicamentos (nome, dosagem, quantidade, horários, datas, observações, foto),
lembretes automáticos recorrentes (diário, por dias da semana ou por intervalo de horas),
confirmação/adiamento/"não tomei", histórico filtrável por dia/semana/mês, relatórios de
adesão declarada (JSON ou CSV), e gestão de acesso de cuidadores.

### Arquitetura

Dois processos (API e bot) compartilham a mesma camada `services/` — nenhuma regra de negócio
é duplicada entre eles. Detalhes completos, incluindo por que só o bot roda o agendador, em
[`docs/architecture.md`](docs/architecture.md).

### Tecnologias

Python 3.12, FastAPI, python-telegram-bot, SQLAlchemy + Alembic, APScheduler, Tesseract OCR,
faster-whisper (STT), pyttsx3 (TTS), pytest. Lista completa e versões em
[`requirements.txt`](requirements.txt).

### Limitações

Ver a seção [Limitações conhecidas](#10-limitações-conhecidas) ao final deste documento.

---

## 2. Como instalar?

### Pré-requisitos

- Python 3.12+
- Git
- Tesseract OCR com o pacote de idioma português (`por`)
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

### Executar com Docker Compose

```bash
docker compose up --build
```

Isso sobe três serviços: `migrate` (roda as migrações e encerra), `api` (porta 8000) e `bot`
(polling do Telegram). Dados do SQLite, uploads e logs ficam em volumes nomeados, então
sobrevivem a `docker compose down` (sem `-v`).

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

RN01 a RN18, com onde cada uma é implementada e qual teste a cobre, estão documentadas em
[`docs/business_rules.md`](docs/business_rules.md).

---

## 6. Quais são as URLs importantes?

| Recurso | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| YAML | http://localhost:8000/openapi.yaml |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health Check | http://localhost:8000/health |
| BotFather | https://t.me/BotFather |

O endereço real do seu bot (`https://t.me/<nome_do_seu_bot>`) depende do nome escolhido ao
criá-lo pelo BotFather — não há uma URL fixa de produção para documentar aqui.

---

## 7. Estrutura do projeto

```text
hora-do-remedio/
├── api/            # FastAPI: rotas, schemas Pydantic, dependências
├── bot/            # python-telegram-bot: handlers, teclados, main.py
├── core/           # configuração, segurança (JWT), logging
├── services/       # regras de negócio compartilhadas entre api/ e bot/
├── database/       # modelos SQLAlchemy e conexão
├── alembic/         # migrações do banco
├── docs/           # openapi.yaml, architecture.md, business_rules.md
├── scripts/        # export_openapi.py, seed_test_data.py
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

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot não inicia: `RuntimeError: TELEGRAM_BOT_TOKEN não configurado` | `.env` sem token, ou não copiado de `.env.example` | `cp .env.example .env` e preencha o token do BotFather |
| OCR sempre retorna vazio | Tesseract não instalado ou sem o pacote `por` | Reinstale com o pacote de idioma (ver seção 2) |
| Transcrição de voz muito lenta na primeira vez | `faster-whisper` baixando o modelo do Hugging Face | Normal na primeira execução; fica em cache depois |
| TTS não produz áudio no Linux | Falta o `espeak` (driver usado pelo `pyttsx3` fora do macOS/Windows) | `sudo apt-get install espeak` (já incluso no `Dockerfile`) |
| `alembic upgrade head` falha dizendo que a tabela já existe | Banco criado fora do fluxo de migração | Apague `database/hora_do_remedio.db` (ambiente de desenvolvimento) e rode a migração de novo |
| Testes de contrato falham após mexer em rotas/schemas | `docs/openapi.yaml` ficou desatualizado | Rode `python scripts/export_openapi.py` antes de testar de novo |

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
- **Sem testes de carga:** a aplicação não foi avaliada sob concorrência real de múltiplos
  usuários; SQLite é adequado para desenvolvimento/demonstração, não para produção em escala
  (ver recomendação de PostgreSQL em [`docs/architecture.md`](docs/architecture.md)).
- **CT17** ("botões antigos ou expirados") do checklist de testes do prompt master não tem
  teste automatizado dedicado.
