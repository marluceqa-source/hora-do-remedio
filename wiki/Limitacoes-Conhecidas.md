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

### RN21, RN26 e RN27 — redação divergente da especificação
As três estão **implementadas e corretas**, mas a wiki as enuncia com o texto da
implementação, não com o da especificação — descreve a solução em vez da regra, o que impede
verificar o cumprimento sem reler o código. RN27 é a mais sensível: a especificação exige
preservar "registros anteriores **e trilhas de auditoria**", e só a primeira metade está
verificada. Card: [#46](https://github.com/marluceqa-source/hora-do-remedio/issues/46).

---

## Qualidade e testes

| Lacuna | Situação |
|---|---|
| **Testes E2E do portal** | Não implementados. Playwright não foi configurado. |
| **Testes automatizados de acessibilidade** | Não implementados. axe-core não foi configurado. As decisões de [acessibilidade](Acessibilidade) do portal não foram auditadas automaticamente. |
| **Testes do frontend** | Não existem. Não há nenhum teste em `frontend/`. |
| **Validação de formulário sem teste automatizado** | Todos os formulários do portal foram verificados **ao vivo no navegador** ([#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32)), mas essa verificação é **manual e não se repete sozinha**: uma regressão nas mensagens não quebraria nenhum teste. É o que [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24) (Playwright) cobriria. |

A suíte de backend está verde: **185 testes passando**, 86% de cobertura.

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
| **Segredo fraco em ambiente marcado como dev** | Desde o card [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30), a aplicação **recusa iniciar** com segredo de exemplo quando `APP_ENV` não é um ambiente de desenvolvimento. A proteção é por configuração, não por inspeção: quem marcar o ambiente como `dev` continua rodando com segredo fraco. |

---

## Achados da revisão de requisitos (20/11/2026)

Lacunas encontradas ao estruturar a documentação de requisitos segundo o CPRE/IREB. A análise
completa está em [Validação e Verificação](Validacao-e-Verificacao#2-verificação-dos-requisitos-qualidade-da-documentação).

| Achado | Situação |
|---|---|
| **Status `expired` inalcançável** | `ReminderEvent.status` admite `expired`, os relatórios o tratam como "sem confirmação" e o bot tem o rótulo `⌛ expirado` — mas **nenhum código atribui esse status**. Por isso o cenário **CT17** ("botões antigos ou expirados") não tem teste nem implementação. Card: [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35). |
| **`tests/accessibility/` está vazio** | O diretório existe com apenas `__init__.py`. A categoria de teste pedida no prompt master (§11) não foi preenchida; os testes de acessibilidade reais estão em `tests/unit/`. Card: [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41). |
| **RN17 sem marcação no código** | Única regra implementável sem o comentário `RNxx` — porque não há expurgo implementado para marcar. As outras 29 das 32 estão marcadas. Card: [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22). |
| **Critérios de aceite sem conferência registrada** | Os 19 critérios da seção 15 do prompt master não têm registro de verificação item a item em nenhum lugar do repositório. Card: [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39). |
| **Sem baseline da especificação** | Não há tags, releases nem versão declarada na wiki — não é possível dizer "esta é a especificação da versão X". Card: [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38). |
| **LGPD: exportação e exclusão de dados** | `RES06` está declarada, mas não existe rota de exportação nem de exclusão de dados do titular. Card: [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42). |
| **Validação com stakeholders: ausente** | Nenhum paciente, cuidador ou profissional de saúde foi consultado. As decisões de [acessibilidade](Acessibilidade) são hipóteses bem fundamentadas, não achados validados — e esse é o maior risco do projeto. Card: [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40). |

A ordem recomendada para atacar esses itens está em
[Priorização e Backlog](Priorizacao-e-Backlog#5-o-backlog-priorizado).

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
