# Casos de Teste — API REST (heurística VADER)

Os casos de API foram desenhados com a heurística **VADER** (Stuart Ashman), que organiza
o teste de uma API REST em cinco pilares:

| Pilar | O que investiga | Arquivo de automação |
| --- | --- | --- |
| **V**erbs | cada verbo HTTP faz o que promete; verbo não suportado responde 405 | `tests/api/vader-verbos.spec.js` |
| **A**uthorization | quem entra, o que alcança e o que o papel permite | `tests/api/vader-autorizacao.spec.js` |
| **D**ata | estrutura, tipos, valores padrão e limites dos dados | `tests/api/vader-dados.spec.js` |
| **E**rrors | código de status correto e causa legível, sem 500 | `tests/api/vader-erros.spec.js` |
| **R**esponsiveness | tempo de resposta, concorrência e carga | `tests/api/vader-responsividade.spec.js` |

A aplicação tem **duas autenticações independentes e propositalmente separadas (RN19)**:

- **App do paciente / bot**: `POST /api/v1/auth/token` troca o `telegram_user_id` por um JWT
  usado no cabeçalho `Authorization: Bearer`.
- **Portal do profissional**: login em duas etapas (senha + TOTP) que devolve um **cookie
  httpOnly** de sessão.

Os casos abaixo seguem o template de caso de teste baseado na **ISO/IEC/IEEE 29119-3**.
Três casos estão detalhados por extenso, como referência do template; os demais estão na
matriz de rastreabilidade, com o mesmo conjunto de informações em forma compacta.

---

## Casos detalhados (template completo)

### CT-API-V06 — Exclusão de medicamento exige confirmação explícita

| Campo | Conteúdo |
| --- | --- |
| **ID** | CT-API-V06 |
| **Título** | Garantir que a exclusão de um medicamento só acontece com confirmação explícita |
| **Prioridade** | Alta |
| **Rastreabilidade** | RN16 (exclusão requer confirmação), pilar Verbs |
| **Pré-Condições** | API no ar; usuário do app autenticado por token; um medicamento cadastrado para esse usuário |

| Passos | Ação | Resultados Esperados |
| --- | --- | --- |
| Passo 1 | `DELETE /api/v1/medications/{id}` sem o parâmetro `confirm` | HTTP 400 com `detail` contendo "confirm=true" |
| Passo 2 | `GET /api/v1/medications/{id}` | HTTP 200 — o medicamento continua cadastrado |
| Passo 3 | `DELETE /api/v1/medications/{id}?confirm=true` | HTTP 204 sem corpo |
| Passo 4 | `GET /api/v1/medications/{id}` | HTTP 404 com `detail` "Medicamento não encontrado" |

**Pós-Condições:** o medicamento deixa de existir para o usuário; nenhum outro usuário é afetado.

---

### CT-API-A11 — Profissional não alcança paciente de outro profissional

| Campo | Conteúdo |
| --- | --- |
| **ID** | CT-API-A11 |
| **Título** | Garantir o isolamento do vínculo profissional ↔ paciente |
| **Prioridade** | Alta |
| **Rastreabilidade** | RN22 (acesso somente a paciente com vínculo autorizado), pilar Authorization |
| **Pré-Condições** | Dois profissionais cadastrados e autenticados (A e B); um paciente cadastrado por A |

| Passos | Ação | Resultados Esperados |
| --- | --- | --- |
| Passo 1 | Com a sessão de B, `GET /api/v1/patients/{id do paciente de A}` | HTTP 404 com `detail` "Paciente não encontrado ou sem vínculo autorizado" |
| Passo 2 | Com a sessão de B, `GET /api/v1/patients/{id}/history` | HTTP 404 — nem o histórico é exposto |
| Passo 3 | Com a sessão de B, `GET /api/v1/patients` | HTTP 200, e o paciente de A **não** aparece na lista |

**Pós-Condições:** nenhum dado clínico do paciente de A é exposto a B; a resposta não
confirma nem nega a existência do registro.

---

### CT-API-E15 — Bloqueio temporário da conta após tentativas indevidas

| Campo | Conteúdo |
| --- | --- |
| **ID** | CT-API-E15 |
| **Título** | Garantir o bloqueio temporário do login após o limite de senhas erradas |
| **Prioridade** | Alta |
| **Rastreabilidade** | RF01 (login do portal), `PROFESSIONAL_MAX_FAILED_LOGINS`, pilar Errors |
| **Pré-Condições** | API no ar com `PROFESSIONAL_MAX_FAILED_LOGINS=5`; um profissional recém-cadastrado |

| Passos | Ação | Resultados Esperados |
| --- | --- | --- |
| Passo 1 | `POST /api/v1/auth/professional/login` com senha errada, 5 vezes | HTTP 401 em todas, com `detail` "E-mail ou senha inválidos" |
| Passo 2 | `POST /api/v1/auth/professional/login` com a senha **correta** | HTTP 423 com `detail` contendo "Conta temporariamente bloqueada" |

**Pós-Condições:** a conta fica bloqueada por `PROFESSIONAL_LOCKOUT_MINUTES`; o contador de
tentativas é zerado no bloqueio; o evento fica registrado na trilha de auditoria.

---

## Matriz de rastreabilidade — todos os casos de API

Prioridade: **A**lta, **M**édia, **B**aixa.

### Pilar V — Verbs

| ID | Título | Pri. | Rastreabilidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| CT-API-V01 | Emissão de token de acesso do paciente | A | RF07, autenticação independente do bot | 200 com `access_token` JWT, `token_type=bearer` e `expires_in` numérico |
| CT-API-V02 | Cadastro de medicamento com horário | A | RF02, RN02 | 201 com o recurso criado, `active=true` e o horário persistido no fuso do usuário |
| CT-API-V03 | Listagem dos medicamentos do usuário | A | RF05, RN09 | 200 com exatamente os medicamentos do próprio usuário |
| CT-API-V04 | Consulta de um medicamento | M | RF05 | 200 com o recurso solicitado |
| CT-API-V05 | Atualização parcial (PATCH) | A | CT10 (atualização de medicamento) | 200; só o campo enviado muda, o restante é preservado |
| CT-API-V06 | Exclusão sem confirmação | A | RN16 | 400 pedindo `confirm=true`; recurso preservado |
| CT-API-V07 | Exclusão com confirmação | A | RN16 | 204 e, na consulta seguinte, 404 |
| CT-API-V08 | PUT em medicamento não é suportado | M | Contrato da API (só PATCH) | 405 Method Not Allowed |
| CT-API-V09 | DELETE em `/health` não é suportado | B | Contrato da API | 405 Method Not Allowed |
| CT-API-V10 | Consulta de agendamentos | M | RF02, RN02 | 200 com o horário semanal vinculado ao medicamento, incluindo `weekdays` |

### Pilar A — Authorization

| ID | Título | Pri. | Rastreabilidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| CT-API-A01 | Requisição sem token | A | Segurança da API | 401 "Credenciais ausentes, inválidas ou expiradas" |
| CT-API-A02 | Token malformado ou adulterado | A | Segurança da API | 401 para token sem formato JWT, com 3 partes falsas e com assinatura inválida |
| CT-API-A03 | Paciente não alcança medicamento de outro | A | RN09 | 404 na leitura e na alteração; nenhum dado de terceiro é exposto |
| CT-API-A04 | Perfil do profissional sem sessão | A | RF01 | 401 "Sessão inválida, expirada ou ausente" |
| CT-API-A05 | Endpoints de paciente sem sessão | A | RF03, RN22 | 401 em listagem, cadastro e dashboard |
| CT-API-A06 | Cookie de sessão inválido | A | RF01 | 401 |
| CT-API-A07 | Token do paciente usado no portal | A | RN19 (autenticações independentes) | 401 — o JWT do paciente não autentica no portal |
| CT-API-A08 | Papel médico em recurso de admin | A | RBAC (seção 3), RN32 | 403 "Seu papel não tem permissão para este recurso" |
| CT-API-A09 | Admin tentando cadastrar paciente | M | RBAC (seção 3) | 403 — cadastro é de profissional clínico |
| CT-API-A10 | Admin lista profissionais e auditoria | M | RF01, RN32 | 200 nas duas consultas |
| CT-API-A11 | Paciente de outro profissional | A | RN22 | 404 em consulta e histórico; ausente na listagem |
| CT-API-A12 | Sessão após logout | A | RF01 | 204 no logout e 401 na chamada seguinte |
| CT-API-A13 | Profissional `pending` cadastrando paciente | A | RF01, RF03 | **Comportamento atual:** 201 e dashboard em 200 — o acesso olha só o papel (risco R1) |

### Pilar D — Data

| ID | Título | Pri. | Rastreabilidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| CT-API-D01 | Contrato e tipos do medicamento | A | RF02, contrato OpenAPI | 12 campos esperados, com os tipos corretos, incluindo a lista de horários |
| CT-API-D02 | Valores padrão e campos opcionais | M | RF02 | opcionais nulos, `active=true`, fuso do usuário aplicado ao horário |
| CT-API-D03 | Nome no limite de 200 / acima de 200 | A | Heurística "nome longo" | 201 com 200 caracteres; 422 `string_too_long` com 201 |
| CT-API-D04 | Acentos, caracteres asiáticos, delimitadores | M | Heurísticas de strings | 201 e leitura idêntica ao gravado, sem perda de encoding |
| CT-API-D05 | Texto com injeção de SQL | A | Heurística "injeção de SQL" | 201 gravando literalmente; base segue íntegra nas chamadas seguintes |
| CT-API-D06 | Orientações no limite de 500 / 501 | M | Contrato de `instructions` | 201 com 500; 422 com 501 apontando o campo |
| CT-API-D07 | Intervalo entre doses de 1 a 24 horas | M | RN02, contrato de `interval_hours` | 201 para 1 e 24; 422 para 0 e 25 |
| CT-API-D08 | Nome somente com espaços | M | Heurística "em branco" | **Comportamento atual:** 201 (risco R2); nome vazio responde 422 |
| CT-API-D09 | Relatório em JSON e em CSV | M | RF10, RN12 | JSON com 5 métricas numéricas; CSV com `text/csv`, cabeçalho e uma linha de dados |
| CT-API-D10 | Contrato do paciente | A | RF03 | 8 campos esperados, `telegram_link_status=not_linked`, vínculo com quem cadastrou |
| CT-API-D11 | Histórico por período | M | RF08, RN12/RN29 | 200 para `day`/`week`/`month` (lista vazia sem vínculo); 422 para período inválido |
| CT-API-D12 | Especificação OpenAPI publicada | M | RF14 | `/openapi.yaml` em `application/yaml` e `/openapi.json` com os caminhos da API |

### Pilar E — Errors

| ID | Título | Pri. | Rastreabilidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| CT-API-E01 | Formato padrão do erro de validação | A | Tratamento de erros da API | 422 com `code=validation_error` e itens contendo `type`, `loc` e `msg` |
| CT-API-E02 | Campo obrigatório ausente | A | RF02 | 422 do tipo `missing` apontando `body.start_date` |
| CT-API-E03 | Data de término antes do início | A | Regra de negócio do medicamento | 422 com "end_date não pode ser anterior a start_date" |
| CT-API-E04 | Medicamento sem nenhum horário | A | RN02 | 422 do tipo `too_short` em `body.schedules` |
| CT-API-E05 | Recorrência incompleta | M | RN02 | 422 indicando `schedule_time` (diária) e `weekdays` (semanal) obrigatórios |
| CT-API-E06 | Identificador de rota com tipo errado | M | Robustez da API | 422 em `path.medication_id` — nunca 500 |
| CT-API-E07 | Senha curta no cadastro | A | RF01 | 422 `string_too_short` em `body.password` |
| CT-API-E08 | E-mail com domínio reservado (`.test`) | B | Heurística "nome inexistente/reservado" | 422 apontando `body.email` |
| CT-API-E09 | Medicamento inexistente | A | RF05 | 404 "Medicamento não encontrado" |
| CT-API-E10 | E-mail de profissional duplicado | A | RF01 | 409 "E-mail já cadastrado" |
| CT-API-E11 | Identificador interno de paciente duplicado | A | RF03 | 409 "Já existe um paciente com este identificador interno" |
| CT-API-E12 | Senha errada e e-mail inexistente | A | RF01, privacidade | 401 com a **mesma** mensagem nos dois casos |
| CT-API-E13 | Código MFA inválido e token de reset inválido | A | RF01 | 401 "Código de verificação inválido"; 422 para código fora de 6 dígitos; 400 "Token inválido ou expirado" |
| CT-API-E14 | Recuperação de acesso não revela o e-mail | A | RF01, privacidade | 202 com resposta idêntica para e-mail existente e inexistente |
| CT-API-E15 | Bloqueio após 5 senhas erradas | A | RF01 | 401 nas 5 tentativas e 423 na seguinte, mesmo com a senha correta |

### Pilar R — Responsiveness

| ID | Título | Pri. | Rastreabilidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| CT-API-R01 | Tempo do health check | M | Observabilidade | 200 com `status=ok` em menos de 1,5 s (após aquecimento) |
| CT-API-R02 | Listagem com 20 medicamentos | M | RF05 | 200 com 20 registros em menos de 3 s |
| CT-API-R03 | 10 emissões de token simultâneas | M | Concorrência | 200 em todas, com 10 tokens distintos |
| CT-API-R04 | 10 cadastros simultâneos do mesmo usuário | A | Concorrência, integridade | 201 em todos, ids distintos, listagem com exatamente 10 |
| CT-API-R05 | Carga máxima permitida pelo contrato | M | Limites do contrato | 201 com nome de 200, orientações de 500 e 24 horários, em menos de 5 s |
| CT-API-R06 | Corpo JSON malformado | A | Robustez da API | 422 `validation_error`; a API continua atendendo |
| CT-API-R07 | Tempo da especificação OpenAPI | B | RF14 | 200 em menos de 3 s |
| CT-API-R08 | Limite de requisições por minuto | M | `RATE_LIMIT_PER_MINUTE` (slowapi) | 429 ao passar do limite. **Fora da execução padrão** — ver instruções no próprio teste |

---

## Por que CT-API-R08 não roda por padrão

A API limita requisições por IP (`slowapi`). Com o limite padrão de 60/minuto, uma suíte
rodando em paralelo esbarraria no limite e geraria 429 em testes que investigam outra
coisa — falha de ambiente disfarçada de defeito. Por isso a automação sobe a API com
`RATE_LIMIT_PER_MINUTE=1000` e o caso de limite fica isolado, com instruções de execução
no comentário acima do teste em `tests/api/vader-responsividade.spec.js`.
