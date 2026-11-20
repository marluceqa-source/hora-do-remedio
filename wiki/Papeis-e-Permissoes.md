# Papéis e Permissões

O sistema tem **dois universos de identidade separados de propósito**: quem usa o bot
(paciente, cuidador) e quem usa o portal (profissional). Eles não compartilham credencial,
segredo nem mecanismo de sessão ([RN19](Regras-de-Negocio-Portal)).

---

## Universo do bot/API

| Papel | Como se identifica | O que pode |
|---|---|---|
| **Paciente** | Conta Telegram + JWT na API. | Cadastrar e excluir seus medicamentos, confirmar/adiar doses, ver seu histórico e relatórios, autorizar e revogar cuidadores. |
| **Cuidador** | Conta Telegram, autorizada por código de convite (`/vincular CODIGO`). | **Somente leitura** dos medicamentos e do histórico do paciente que o autorizou, enquanto a autorização não for revogada ([RN14](Regras-de-Negocio-Bot-e-API)). |

O paciente pode revogar um cuidador a qualquer momento, sem depender de ninguém.

---

## Universo do portal

O papel enforçado é o campo **`role`**. O campo `profession` é texto livre e serve apenas
para exibição — **não** concede permissão.

| `role` | Rótulo no portal | Pode ativar tratamento? |
|---|---|---|
| `medico` | Médico(a) | ✅ **Sim** |
| `enfermeiro` | Enfermeiro(a) | ❌ Não |
| `outro_profissional` | Outro profissional de saúde | ❌ Não |
| `admin` | Administrador | ❌ Não (não é um papel clínico) |

> **[RN20](Regras-de-Negocio-Portal): só `medico` ativa um tratamento.** A API responde **403**
> e o portal desabilita o botão explicando o motivo em texto — a pessoa entende *por que* não
> pode, em vez de encontrar um botão morto.

### O que cada papel faz

| Ação | `medico` | `enfermeiro` | `outro_profissional` | `admin` |
|---|---|---|---|---|
| Cadastrar paciente | ✅ | ✅ | ✅ | — |
| Gerar convite de vínculo ao Telegram | ✅ | ✅ | ✅ | — |
| Cadastrar tratamento (rascunho) | ✅ | ✅ | ✅ | — |
| Editar tratamento / criar nova versão | ✅ | ✅ | ✅ | — |
| **Ativar tratamento** | ✅ | ❌ | ❌ | ❌ |
| Suspender tratamento | ✅ | ✅ | ✅ | — |
| Ver painel e histórico dos seus pacientes | ✅ | ✅ | ✅ | — |
| Verificar/rejeitar profissionais | ❌ | ❌ | ❌ | ✅ |
| Consultar trilha de auditoria | ❌ | ❌ | ❌ | ✅ |

O administrador é um papel **de governança, não clínico**: ele verifica profissionais e lê a
auditoria, mas não vê dados clínicos de pacientes.

---

## As duas camadas de autorização

Ter o papel certo **não é suficiente**. Todo acesso a dado de paciente passa por duas
verificações independentes:

1. **Papel** (`role`) — a dependência `require_roles(*roles)` em
   `core/professional_security.py` decide se aquele tipo de profissional pode executar a ação.
2. **Vínculo** (`PatientProfessionalLink`) — [RN22](Regras-de-Negocio-Portal): mesmo um médico
   verificado só vê pacientes com vínculo **ativo**. Quem cadastra o paciente já fica
   vinculado automaticamente.

Um médico verificado, com sessão válida e MFA em dia, continua sem acesso a um paciente com
quem não tem vínculo.

---

## Verificação do profissional

O autocadastro no portal é uma **solicitação**, não uma liberação.

| `verification_status` | Significado |
|---|---|
| `pending` | Padrão ao se cadastrar. Aguarda um administrador. |
| `verified` | Verificado por um administrador. |
| `rejected` | Rejeitado. |

A tela de cadastro diz isso explicitamente ao profissional, para não criar a expectativa de
acesso clínico imediato.

---

## Próximo

- [Segurança e Privacidade](Seguranca-e-Privacidade)
- [Regras de Negócio — Portal](Regras-de-Negocio-Portal)
