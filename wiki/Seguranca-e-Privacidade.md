# Segurança e Privacidade

---

## Dois sistemas de autenticação, de propósito

[RN19](Regras-de-Negocio-Portal) — o paciente e o profissional autenticam por mecanismos
**totalmente separados**, com segredos diferentes:

| | Bot / API (paciente) | Portal (profissional) |
|---|---|---|
| Módulo | `core/security.py` | `core/professional_security.py` |
| Mecanismo | JWT em `Authorization: Bearer` | **Cookie `httpOnly`** de sessão |
| Segredo | `SECRET_KEY` | `PROFESSIONAL_SESSION_SECRET_KEY` |
| MFA | — | **Obrigatório (TOTP)** |
| Revogação | Expiração do token | **Revogável no servidor** |

O vazamento de um dos segredos não compromete o outro universo.

---

## Sessão do profissional

O token de sessão **não é um JWT** — é um token opaco aleatório, e **só o seu hash SHA-256 é
persistido** em `ProfessionalSession`. Consequências:

- Quem leia o banco **não consegue** reconstruir uma sessão válida.
- O logout é **revogação real** no servidor, não só o descarte do cookie no navegador.

O cookie é `httpOnly`, então JavaScript da página não o alcança — isso reduz o impacto de um
eventual XSS. Por isso o frontend usa `withCredentials: true` e o CORS da API declara
`allow_credentials=True` com **lista explícita de origens** (nunca `*`, que é incompatível
com credenciais).

| Configuração | Padrão |
|---|---|
| `PROFESSIONAL_SESSION_EXPIRE_MINUTES` | 480 (8 h) |
| `PROFESSIONAL_SESSION_COOKIE_NAME` | `hdr_professional_session` |

---

## MFA obrigatório (TOTP)

O login tem **duas etapas**:

1. **Senha** → `POST /auth/professional/login`. Não devolve sessão: devolve um
   `pre_auth_token` de vida curta (padrão **5 min**), carimbado com a finalidade
   (`mfa_setup` no primeiro acesso, `mfa_verify` nos seguintes).
2. **Código TOTP** → `/mfa/setup` + `/mfa/confirm` no primeiro acesso, ou `/mfa/verify` nos
   demais. **Só aqui** a sessão é emitida.

No primeiro acesso o portal exibe o segredo como **QR Code** para escanear no app autenticador
(Google Authenticator, Authy etc.), com o código em texto como alternativa para quem não
consegue escanear.

O `pre_auth_token` carrega a finalidade justamente para que um token de configuração de MFA
não possa ser usado como token de verificação, nem vice-versa.

---

## Senhas e bloqueio

- Hash com **bcrypt** (via `passlib`).
- [RN30](Regras-de-Negocio-Portal): após **5** tentativas falhas, a conta é bloqueada por
  **15 minutos**.
- **Recuperação de acesso não revela se o e-mail existe** — a resposta é a mesma para e-mail
  cadastrado ou não, para não transformar o formulário em um verificador de contas.
- O token de recuperação é opaco, válido por **30 minutos** e, ao ser consumido,
  **encerra todas as sessões anteriores** do profissional.

---

## Convite de vínculo do paciente

[RN23](Regras-de-Negocio-Portal)/[RN24](Regras-de-Negocio-Portal) — o convite que liga o
paciente ao Telegram é:

- **De uso único** — consumido, não serve mais.
- **Temporário** — expira em **30 minutos** (`PATIENT_INVITE_EXPIRE_MINUTES`).
- **Armazenado só como hash**, como as sessões.

Entregue como deep link do Telegram e como QR Code. A escolha é de
[acessibilidade](Acessibilidade): o paciente não digita nada.

---

## Auditoria

[RN32](Regras-de-Negocio-Portal) — `AuditLog` registra **quem** (ator e papel do ator),
**o que** e **quando**, para operações sensíveis do portal.

A leitura da trilha é **exclusiva de administradores**. A rota de auditoria expõe auditoria —
**nunca** dados clínicos de pacientes.

---

## Dados pessoais e minimização

| Decisão | Motivo |
|---|---|
| Paciente é identificado por **identificador interno**, não por CPF ou documento. | O formulário diz isso explicitamente: *"Único — nunca use CPF ou outro documento."* |
| Campo de contato é **opcional** e rotulado *"só se autorizado"*. | Não coletar o que não é necessário. |
| OCR e transcrição de voz rodam **localmente** (Tesseract, faster-whisper). | Foto da receita e áudio do paciente **não** são enviados a serviços de terceiros. |
| Mídia de runtime não é versionada (`assets/audio/tmp/`, `assets/uploads/` no `.gitignore`). | Mídia de usuário não entra no repositório. |
| `.env` ignorado pelo Git; `.env.example` versionado sem valores reais. | Segredos não vão para o controle de versão. |

---

## Mensagens de erro

Nenhuma mensagem crua de framework chega ao usuário. O tratamento central em
`frontend/src/api/client.ts` traduz os erros de validação do Pydantic para português **com o
rótulo do campo**, e substitui as mensagens do Axios (`"Network Error"`, timeouts) por texto
em português.

Isso também é uma decisão de segurança: a interface não expõe detalhe interno do backend ao
usuário final.

---

## Próximo

- [Papéis e Permissões](Papeis-e-Permissoes)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
