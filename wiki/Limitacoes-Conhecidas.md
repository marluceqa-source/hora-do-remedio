# Limitações Conhecidas

Esta página existe para que a wiki **não prometa mais do que o código entrega**. Cada item
abaixo é uma lacuna real, verificada no repositório.

---

## Regras de negócio com garantia parcial

### RN17 — Política de retenção de dados
`DATA_RETENTION_DAYS` existe na configuração (padrão **365 dias**), mas **nenhum job de
expurgo automático foi implementado**. A aplicação **não apaga** registros antigos sozinha.

A regra está documentada e configurável, mas não está em vigor.

### RN13 — O sistema não prescreve
A garantia é por **ausência de funcionalidade**: não existe código que sugira medicamento ou
dosagem. **Não** há filtro ativo de conteúdo — nada impede que o próprio usuário digite esse
tipo de informação no campo livre de observações.

### RN29 e RN31 — Sem correspondência no código
A numeração das regras do portal salta: **RN29 e RN31 não têm marcação em nenhum arquivo**.
Elas podem existir na especificação original sem terem sido anotadas na implementação, ou
podem não existir. **A wiki não inventou o conteúdo delas** — é preciso conferir a
especificação do portal e então documentar ou descartar.

---

## Qualidade e testes

| Lacuna | Situação |
|---|---|
| **Testes E2E do portal** | Não implementados. Playwright não foi configurado. |
| **Testes automatizados de acessibilidade** | Não implementados. axe-core não foi configurado. As decisões de [acessibilidade](Acessibilidade) do portal não foram auditadas automaticamente. |
| **Testes do frontend** | Não existem. Não há nenhum teste em `frontend/`. |
| **Validação ao vivo de dois formulários** | O cadastro de paciente e o cadastro de medicamento usam o mesmo padrão de validação já validado no navegador nas outras telas, mas **não foram testados ao vivo** porque exigem login com MFA. |

A suíte de backend está verde: **160 testes passando**, 86% de cobertura.

---

## Empacotamento e documentação

| Lacuna | Situação |
|---|---|
| **Docker não cobre o portal** | `Dockerfile` e `docker-compose.yml` não têm nenhuma referência a Node, npm ou `frontend/`. O portal web **não é empacotado nem servido** pela infraestrutura Docker atual. |
| **Seed não cobre o portal** | `scripts/seed_test_data.py` cria apenas dados do lado do paciente — **não cria profissionais, pacientes do portal nem planos de tratamento**. Para experimentar o portal é preciso criar a conta pelo `/signup` e passar pelo MFA. |

---

## Operação

| Lacuna | Situação |
|---|---|
| **Envio de e-mail** | A recuperação de acesso do profissional **gera** o token, mas o ambiente **não envia e-mails reais**. A própria tela avisa que o token deve ser obtido com o administrador. |
| **Agendador em instância única** | O APScheduler roda no processo do bot. Rodar mais de uma instância do bot produziria lembretes duplicados — não há coordenação (lock distribuído) entre instâncias. |
| **Segredos padrão** | `PROFESSIONAL_SESSION_SECRET_KEY` tem o valor padrão `change-me-professional-session`. **Precisa ser trocado** antes de qualquer uso real. |

---

## Como isso é acompanhado

Cada item desta página corresponde a um **card (issue)** no repositório, com rótulo
`pendência`. A wiki descreve o estado; as issues acompanham a evolução.

👉 [Pendências abertas](https://github.com/marluceqa-source/hora-do-remedio/issues?q=is%3Aissue+is%3Aopen+label%3Apend%C3%AAncia)
· [Tudo que já foi entregue](https://github.com/marluceqa-source/hora-do-remedio/issues?q=is%3Aissue+label%3A%22conclu%C3%ADdo%22)

---

## Próximo

- [Visão Geral do Sistema](Visao-Geral)
- [Regras de Negócio — Portal](Regras-de-Negocio-Portal)
