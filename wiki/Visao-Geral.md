# Visão Geral do Sistema

---

## Objetivo

Ajudar pessoas a cadastrar seus medicamentos, receber lembretes automáticos no horário certo,
confirmar (ou não) que tomaram a dose e consultar o histórico — tudo pelo Telegram, com uma
API REST por trás e um portal web onde profissionais de saúde prescrevem os tratamentos.

## Público-alvo

- **Pacientes**: pessoas idosas, não alfabetizadas ou com dificuldade de leitura e visão.
- **Cuidadores**: familiares autorizados pelo próprio paciente.
- **Profissionais de saúde**: médicos, enfermeiros e outros profissionais.

## O que o sistema **não** é

- **Não é um prescritor.** O sistema não sugere medicamento, dose ou horário
  ([RN13](Regras-de-Negocio-Bot-e-API)).
- **Não mede adesão real.** Mede **adesão declarada**: só o que o paciente confirmou
  ([RN12](Regras-de-Negocio-Bot-e-API)).
- **Não é um prontuário.** Guarda o necessário para lembrar e registrar doses.

---

## Arquitetura

```
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│    Paciente   │          │   Cuidador    │          │ Profissional  │
│   (Telegram)  │          │  (Telegram)   │          │   (Navegador) │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └────────────┬─────────────┘                          │
                     ▼                                        ▼
            ┌─────────────────┐                      ┌─────────────────┐
            │  Processo BOT   │                      │  Portal React   │
            │ python-telegram │                      │   Vite + MUI    │
            │   -bot + APSch. │                      └────────┬────────┘
            └────────┬────────┘                               │ cookie httpOnly
                     │                                        ▼
                     │                               ┌─────────────────┐
                     │                               │  Processo API   │
                     │                               │    FastAPI      │
                     │                               └────────┬────────┘
                     │                                        │
                     └──────────────┬─────────────────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │   services/  (regras) │  ← fonte única de verdade
                        └───────────┬───────────┘
                                    ▼
                        ┌───────────────────────┐
                        │ SQLAlchemy + Alembic  │
                        └───────────────────────┘
```

**Dois processos, uma camada de regras.** O bot e a API compartilham `services/` — nenhuma
regra de negócio é duplicada.

**Só o bot roda o agendador.** O APScheduler vive no processo do bot, porque é ele que tem a
conexão com o Telegram para entregar o lembrete. Rodar o agendador também na API produziria
lembretes duplicados. Detalhes em
[`docs/architecture.md`](../blob/main/docs/architecture.md).

**O portal não reimplementou o agendador.** Ativar um tratamento materializa as entidades
`Medication`/`Schedule` que o agendador já sabia consumir — ver
[Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento).

---

## Tecnologias

### Backend
| Área | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| API | FastAPI, Pydantic v2 |
| Banco / migrações | SQLAlchemy 2.0, Alembic |
| Bot | python-telegram-bot v21 |
| Agendamento | APScheduler |
| Autenticação | PyJWT, passlib + bcrypt, pyotp (TOTP) |
| Proteção | slowapi (rate limiting) |
| OCR | pytesseract / Tesseract |
| Voz → texto | faster-whisper |
| Texto → voz | pyttsx3 |
| Testes | pytest, pytest-cov, httpx |

### Frontend (portal)
| Área | Tecnologia |
|---|---|
| Build | Vite |
| UI | React 19, TypeScript, MUI v9 |
| Rotas | React Router |
| HTTP | Axios (`withCredentials`) |
| Formulários | React Hook Form + Zod |
| QR Code | `qrcode.react` |

### Infra
Docker e Docker Compose. Lista completa e versões em
[`requirements.txt`](../blob/main/requirements.txt) e
[`frontend/package.json`](../blob/main/frontend/package.json).

> OCR, STT e TTS rodam **localmente** — foto da receita e áudio do paciente não são enviados a
> serviços de terceiros.

---

## Estado atual

| Entrega | Situação |
|---|---|
| Bot Telegram | ✅ Completo e validado em bot real |
| API REST + OpenAPI | ✅ Completa |
| Portal — backend | ✅ Completo |
| Portal — frontend | ✅ Telas completas e validadas no navegador |
| Testes de backend | ✅ 185 testes |
| Testes E2E / acessibilidade | ❌ Não implementados |
| Docker | ✅ Existe (não revalidado após o portal) |

Ver [Limitações Conhecidas](Limitacoes-Conhecidas) para o detalhamento do que falta.

---

## Próximo

- [Requisitos Funcionais](Requisitos-Funcionais)
- [Papéis e Permissões](Papeis-e-Permissoes)
