# Arquitetura — Hora do Remédio

## Visão geral

Dois processos compartilham a mesma camada de regras de negócio:

```
                    ┌──────────────────┐
                    │   services/      │  medication, reminder, report,
                    │  (regras únicas) │  caregiver, scheduler, notification,
                    └───┬──────────┬───┘  ocr, speech_to_text, text_to_speech
                        │          │
            ┌───────────▼──┐   ┌───▼────────────┐
            │  api/ (FastAPI)│   │  bot/ (python- │
            │  processo HTTP │   │  telegram-bot) │
            └───────────────┘   └────────────────┘
                        │          │
                        └────┬─────┘
                             ▼
                    database/ (SQLAlchemy + SQLite)
```

- **`api/`** expõe a API REST (FastAPI) — não inicia nenhum `SchedulerService`.
- **`bot/`** roda o bot do Telegram **e** o único `SchedulerService` (APScheduler) do sistema.
- **`services/`** contém toda a lógica de negócio, usada por ambos os processos — nem a API
  nem o bot duplicam regras; cada um só traduz sua interface (HTTP ou Telegram) para chamadas
  de função em `services/`.
- **`database/`** define os modelos SQLAlchemy e a conexão; migrações ficam em `alembic/`.

## Por que só um processo roda o agendador

RF05/RN08 exigem que os lembretes sejam agendados de forma persistente e não dupliquem
notificações. Rodar o `SchedulerService` em mais de um processo (duas réplicas do bot, ou
também na API) geraria o mesmo lembrete duas vezes. Por isso:

- `api/main.py` **nunca** instancia `SchedulerService`.
- `docker-compose.yml` mantém o serviço `bot` com exatamente 1 réplica (ver comentário no
  próprio arquivo).
- A persistência dos agendamentos (RF05, RN08) vem de reconstruir os jobs do APScheduler a
  partir das tabelas `medications`/`schedules` a cada início do processo
  (`SchedulerService.reload_jobs`), e não de um jobstore próprio do APScheduler — assim o
  banco de dados continua sendo a única fonte de verdade.

## Convenção de datas/horas

- `ReminderEvent.scheduled_datetime` é **naive** e representa o horário de parede (wall-clock)
  no fuso do próprio `Schedule` (RN07) — nunca um instante UTC.
- `ReminderEvent.delivery_datetime` e `confirmed_datetime`, além de `User.created_at` e
  `CaregiverAccess.authorized_at`, são instantes reais, armazenados como UTC naive.

Essa distinção evita o erro clássico de comparar "hoje" do servidor com "hoje" do usuário
quando estão em fusos diferentes (coberto por CT14).

## Autenticação

A API usa um JWT próprio (`core/security.py`), emitido por `POST /api/v1/auth/token` a partir
de um `telegram_user_id` — independente do token do bot do Telegram (seção 8 do prompt
master). O bot chama os `services/` diretamente (mesmo processo Python), então não precisa
desse token; ele existe para permitir que outros clientes (um app de cuidador, por exemplo)
consumam a API de forma autenticada.

## OCR, STT e TTS — escolhas e trade-offs

| Capacidade | Biblioteca | Por quê | Custo/privacidade | Alternativa considerada |
|---|---|---|---|---|
| OCR (RF03) | `pytesseract` + binário `tesseract` | Maduro, roda local, suporta `por`. | Zero custo por chamada; a imagem nunca sai da máquina. | Google Vision / AWS Textract — melhor acurácia, mas enviaria fotos de medicamentos a terceiros. |
| STT (RF04) | `faster-whisper` | Boa acurácia em pt-BR mesmo no modelo pequeno, roda em CPU. | Download do modelo uma vez (cache local); áudio nunca sai da máquina. | Google Speech-to-Text — menor latência de frio, mas envia áudio do usuário a terceiros. |
| TTS (RF01, RF06) | `pyttsx3` (voz nativa do SO) | Sem dependência de modelo/arquivo extra; usa a voz do próprio sistema operacional. | Zero custo; nada sai da máquina. | `piper-tts` — vozes neurais melhores, mas o pacote Python depende de `piper-phonemize`, sem wheel pré-compilada para macOS arm64 + Python 3.12 neste ambiente (falha de instalação registrada durante o desenvolvimento). |

### Limitação conhecida de áudio

Telegram só trata como "mensagem de voz" (bolha arredondada) arquivos `.ogg`/Opus. O bot
sempre envia o áudio via `send_audio` (bolha de arquivo de áudio comum) em vez de
`send_voice` — converter para Opus exigiria `ffmpeg` como dependência adicional, não incluída
neste projeto.

Além disso, o `.aiff` bruto gerado pelo `pyttsx3` no macOS **não é reproduzível pelos
clientes do Telegram** — a mensagem chega, mas o áudio não carrega (bug real encontrado e
corrigido durante o desenvolvimento). `services/text_to_speech_service.py` agora converte
automaticamente para `.m4a` (AAC) via `afconvert` (nativo do macOS, sem dependência extra)
antes de devolver o arquivo. Em outros sistemas (ex.: `espeak`/`.wav` no Linux, usado no
`Dockerfile`), a conversão é pulada — o áudio sai no formato bruto do driver, sem a mesma
garantia de compatibilidade; validar manualmente antes de depender disso em produção Linux.

## Desenvolvimento vs. produção

| Aspecto | Desenvolvimento | Produção |
|---|---|---|
| Banco de dados | SQLite (`database/hora_do_remedio.db`) | Avaliar PostgreSQL para concorrência e backups geridos — a camada SQLAlchemy já é portável, bastando trocar `DATABASE_URL` e gerar as migrações equivalentes. |
| TTS/OCR/STT | Local, sem custo, qualidade "suficiente para teste" | Mesma stack funciona, mas validar se a voz pt-BR do SO/imagem Docker atende ao padrão de qualidade desejado. |
| Scheduler | 1 processo do bot rodando localmente | 1 réplica do serviço `bot` (nunca mais que uma) — ver seção acima. |
| Segredos | `.env` local (nunca versionado) | Variáveis de ambiente/segredo geridas pela plataforma de deploy, nunca no `.env.example`. |

## Limitações

- Sem job de expurgo automático para `DATA_RETENTION_DAYS` (RN17) — a variável existe na
  configuração, mas nada apaga registros antigos sozinho hoje.
- Ilustrações de acessibilidade (RF11): apenas 4 das 11 do símbolo-tabela têm imagem própria
  (fornecidas pelo usuário em `Criacao/`); as demais usam o emoji Unicode do próprio símbolo
  como equivalente funcional.
- Nenhum teste de carga/concorrência foi realizado; o SQLite com `check_same_thread=False` é
  adequado para o volume de uso de desenvolvimento/demonstração, não para produção com muitos
  usuários simultâneos.
