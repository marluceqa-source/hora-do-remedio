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
| **Suíte de backend após a última alteração** | Os 160 testes de backend **não foram reexecutados** após os ajustes finais de validação em português no frontend (que não tocam o backend, mas a verificação não foi feita). |
| **Validação ao vivo de dois formulários** | O cadastro de paciente e o cadastro de medicamento usam o mesmo padrão de validação já validado no navegador nas outras telas, mas **não foram testados ao vivo** porque exigem login com MFA. |

---

## Empacotamento e documentação

| Lacuna | Situação |
|---|---|
| **Docker não cobre o portal** | `Dockerfile` e `docker-compose.yml` não têm nenhuma referência a Node, npm ou `frontend/`. O portal web **não é empacotado nem servido** pela infraestrutura Docker atual. |
| **README não menciona o portal** | Zero ocorrências de "portal" ou "profissional" no `README.md`. A documentação principal descreve apenas o bot e a API — alguém que clone o repositório não descobre que o portal existe. |
| **Wiki não publicada no GitHub** | Estas páginas estão versionadas em `wiki/` no repositório. A wiki do GitHub precisa ser inicializada pela interface web antes de receber o conteúdo por git. |

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

---

## Próximo

- [Visão Geral do Sistema](Visao-Geral)
- [Regras de Negócio — Portal](Regras-de-Negocio-Portal)
